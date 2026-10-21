"""Verifica as quatro operacoes na rede sem alterar os registros dos aplicativos."""
import argparse
import json
from pathlib import Path
import sys
import uuid

import grpc

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sdgrpc import contracts_pb2 as pb
from sdgrpc import contracts_pb2_grpc as rpc
from sdgrpc.client import demo


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--naming", required=True)
    args = parser.parse_args()
    name = "teste-" + uuid.uuid4().hex
    checks = []
    with grpc.insecure_channel(args.naming) as channel:
        stub = rpc.NamingServiceStub(channel)
        calculator = stub.Lookup(pb.Name(name="calculadora"), timeout=5)
        text = stub.Lookup(pb.Name(name="texto"), timeout=5)
        try:
            stub.Bind(pb.Binding(name=name, address=calculator), timeout=5)
            assert stub.Lookup(pb.Name(name=name), timeout=5) == calculator
            checks += ["bind", "lookup"]
            try:
                stub.Bind(pb.Binding(name=name, address=text), timeout=5)
                raise AssertionError("Bind duplicado foi aceito")
            except grpc.RpcError as exc:
                assert exc.code() == grpc.StatusCode.ALREADY_EXISTS
            checks.append("duplicate_bind_rejected")
            stub.Rebind(pb.Binding(name=name, address=text), timeout=5)
            assert stub.Lookup(pb.Name(name=name), timeout=5) == text
            checks.append("rebind")
        finally:
            stub.Unbind(pb.Name(name=name), timeout=5)
        try:
            stub.Lookup(pb.Name(name=name), timeout=5)
            raise AssertionError("Lookup encontrou um nome removido")
        except grpc.RpcError as exc:
            assert exc.code() == grpc.StatusCode.NOT_FOUND
        checks += ["unbind", "missing_lookup_rejected"]
    result = demo(args.naming)
    assert result["calculator"]["result"] == 15
    assert result["text"]["words"] == 4
    assert len({result['client']['machine'], result['calculator']['machine'], result['text']['machine']}) == 3
    result["checks"] = checks + ["calculator_rpc", "text_rpc", "three_distinct_application_machines"]
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
