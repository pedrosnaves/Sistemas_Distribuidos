from concurrent import futures
import math
from pathlib import Path
import tempfile
import unittest

import grpc
from sdgrpc import contracts_pb2 as pb
from sdgrpc import contracts_pb2_grpc as rpc
from sdgrpc.applications import CalculatorService, TextService
from sdgrpc.client import analyze, calculate
from sdgrpc.naming import NamingService


def start(service, add):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=12))
    add(service, server)
    port = server.add_insecure_port("127.0.0.1:0")
    server.start()
    return server, port


class GrpcIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.registry = NamingService()
        self.names, self.names_port = start(self.registry, rpc.add_NamingServiceServicer_to_server)
        self.calc, self.calc_port = start(CalculatorService(), rpc.add_CalculatorServiceServicer_to_server)
        self.text, self.text_port = start(TextService(), rpc.add_TextServiceServicer_to_server)
        self.channel = grpc.insecure_channel(f"127.0.0.1:{self.names_port}")
        self.stub = rpc.NamingServiceStub(self.channel)
        self.stub.Bind(self.binding("calculadora", self.calc_port), timeout=3)
        self.stub.Bind(self.binding("texto", self.text_port), timeout=3)

    def tearDown(self):
        self.channel.close()
        for server in (self.text, self.calc, self.names):
            server.stop(0).wait()
        self.registry.close()

    @staticmethod
    def binding(name, port):
        return pb.Binding(name=name, address=pb.Address(host="127.0.0.1", port=port))

    def assert_code(self, expected, operation):
        with self.assertRaises(grpc.RpcError) as caught:
            operation()
        self.assertEqual(caught.exception.code(), expected)

    def test_bind_lookup_unbind(self):
        self.stub.Bind(self.binding("teste", 50100), timeout=3)
        self.assertEqual(self.stub.Lookup(pb.Name(name="teste"), timeout=3).port, 50100)
        self.stub.Unbind(pb.Name(name="teste"), timeout=3)
        self.assert_code(grpc.StatusCode.NOT_FOUND, lambda: self.stub.Lookup(pb.Name(name="teste"), timeout=3))

    def test_duplicate_bind_does_not_replace(self):
        self.assert_code(grpc.StatusCode.ALREADY_EXISTS, lambda: self.stub.Bind(self.binding("calculadora", 50100), timeout=3))
        self.assertEqual(self.stub.Lookup(pb.Name(name="calculadora"), timeout=3).port, self.calc_port)

    def test_rebind_updates_and_creates(self):
        self.stub.Rebind(self.binding("calculadora", 50100), timeout=3)
        self.assertEqual(self.stub.Lookup(pb.Name(name="calculadora"), timeout=3).port, 50100)
        self.stub.Rebind(self.binding("novo", 50101), timeout=3)
        self.assertEqual(self.stub.Lookup(pb.Name(name="novo"), timeout=3).port, 50101)

    def test_missing_name_returns_not_found(self):
        for action in (self.stub.Lookup, self.stub.Unbind):
            self.assert_code(grpc.StatusCode.NOT_FOUND, lambda: action(pb.Name(name="ausente"), timeout=3))

    def test_validation(self):
        for binding in (self.binding("", 50061), self.binding("Nome com espacos", 50061), self.binding("teste", 0), self.binding("teste", 65536), pb.Binding(name="teste", address=pb.Address(host="0.0.0.0", port=50061))):
            self.assert_code(grpc.StatusCode.INVALID_ARGUMENT, lambda: self.stub.Bind(binding, timeout=3))

    def test_concurrent_duplicate_bind_is_atomic(self):
        def bind_once(_):
            try:
                self.stub.Bind(self.binding("concorrente", 50100), timeout=5)
                return grpc.StatusCode.OK
            except grpc.RpcError as exc:
                return exc.code()
        with futures.ThreadPoolExecutor(max_workers=10) as pool:
            results = list(pool.map(bind_once, range(20)))
        self.assertEqual(results.count(grpc.StatusCode.OK), 1)
        self.assertEqual(results.count(grpc.StatusCode.ALREADY_EXISTS), 19)

    def test_calculator_all_operations_via_discovery(self):
        for operation, expected in ((pb.ADD, 15), (pb.SUBTRACT, 9), (pb.MULTIPLY, 36), (pb.DIVIDE, 4)):
            result = calculate(f"127.0.0.1:{self.names_port}", 12, 3, operation)
            self.assertEqual(result["result"], expected)
            self.assertTrue(result["process_id"] > 0)

    def test_calculator_rejects_invalid_and_overflow(self):
        with grpc.insecure_channel(f"127.0.0.1:{self.calc_port}") as channel:
            stub = rpc.CalculatorServiceStub(channel)
            for request in (pb.Calculation(a=1, b=0, operation=pb.DIVIDE), pb.Calculation(a=math.nan, b=1), pb.Calculation(a=1, b=2, operation=999)):
                self.assert_code(grpc.StatusCode.INVALID_ARGUMENT, lambda: stub.Calculate(request, timeout=3))
            self.assert_code(grpc.StatusCode.OUT_OF_RANGE, lambda: stub.Calculate(pb.Calculation(a=1e308, b=1e308), timeout=3))

    def test_unicode_and_empty_text(self):
        for text in ("Ola, mundo!", "Sistemas distribuídos e ação", ""):
            result = analyze(f"127.0.0.1:{self.names_port}", text)
            self.assertEqual(result["uppercase"], text.upper())
            self.assertEqual(result["characters"], len(text))
            self.assertEqual(result["words"], len(text.split()))

    def test_client_looks_up_again_after_rebind(self):
        replacement, port = start(CalculatorService(), rpc.add_CalculatorServiceServicer_to_server)
        try:
            self.stub.Rebind(self.binding("calculadora", port), timeout=3)
            result = calculate(f"127.0.0.1:{self.names_port}", 1, 2, pb.ADD)
            self.assertEqual(result["discovered_address"], f"127.0.0.1:{port}")
            self.assertEqual(result["result"], 3)
        finally:
            replacement.stop(0).wait()

    def test_sqlite_survives_registry_restart(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "registry.sqlite3"
            for iteration in range(2):
                registry = NamingService(database)
                server, port = start(registry, rpc.add_NamingServiceServicer_to_server)
                try:
                    with grpc.insecure_channel(f"127.0.0.1:{port}") as channel:
                        stub = rpc.NamingServiceStub(channel)
                        if iteration == 0:
                            stub.Bind(self.binding("persistente", 50200), timeout=3)
                        self.assertEqual(stub.Lookup(pb.Name(name="persistente"), timeout=3).port, 50200)
                finally:
                    server.stop(0).wait()
                    registry.close()


if __name__ == "__main__":
    unittest.main()
