"""Cada invocacao inicia exatamente um servidor e um processo gRPC."""
import argparse
from concurrent import futures
import logging
import json
import os
from pathlib import Path
import signal
import socket
import threading

import grpc
from sdgrpc import contracts_pb2 as pb
from sdgrpc import contracts_pb2_grpc as rpc
from sdgrpc.applications import CalculatorService, TextService
from sdgrpc.naming import NamingService, endpoint


def main():
    parser = argparse.ArgumentParser(description="Servidor gRPC do exercicio de Sistemas Distribuidos")
    parser.add_argument("role", choices=("names", "calculator", "text"))
    parser.add_argument("--listen-host", default="127.0.0.1")
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--naming", help="Endereco host:porta do servico de nomes")
    parser.add_argument("--advertise-host", help="IP privado ou DNS acessivel pelo cliente")
    parser.add_argument("--name", help="Nome logico registrado pelo servidor")
    parser.add_argument("--database", default="var/names.sqlite3")
    parser.add_argument("--ready-file", help="Arquivo opcional de prontidao para demonstracoes locais")
    parser.add_argument("--stop-file", help="Sinal de encerramento opcional para a demonstracao local")
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("porta deve estar entre 1 e 65535")
    if args.role != "names" and not args.naming:
        parser.error("servidores de aplicacao precisam de --naming")
    advertised = args.advertise_host or args.listen_host
    if args.role != "names" and advertised in ("0.0.0.0", "::"):
        parser.error("informe --advertise-host com um endereco acessivel")

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    registry = None
    if args.role == "names":
        Path(args.database).parent.mkdir(parents=True, exist_ok=True)
        registry = NamingService(args.database)
        rpc.add_NamingServiceServicer_to_server(registry, server)
    elif args.role == "calculator":
        rpc.add_CalculatorServiceServicer_to_server(CalculatorService(), server)
    else:
        rpc.add_TextServiceServicer_to_server(TextService(), server)
    listen = endpoint(pb.Address(host=args.listen_host, port=args.port))
    if server.add_insecure_port(listen) == 0:
        raise RuntimeError(f"Nao foi possivel escutar em {listen}")
    stopped = threading.Event()
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, lambda *_: stopped.set())
    server.start()
    try:
        if args.role != "names":
            name = args.name or {"calculator": "calculadora", "text": "texto"}[args.role]
            binding = pb.Binding(name=name, address=pb.Address(host=advertised, port=args.port))
            with grpc.insecure_channel(args.naming) as channel:
                grpc.channel_ready_future(channel).result(timeout=10)
                stub = rpc.NamingServiceStub(channel)
                try:
                    stub.Bind(binding, timeout=5)
                    action = "bind"
                except grpc.RpcError as exc:
                    if exc.code() != grpc.StatusCode.ALREADY_EXISTS:
                        raise
                    stub.Rebind(binding, timeout=5)
                    action = "rebind"
            logging.info("%s nome=%s endereco=%s", action, name, endpoint(binding.address))
        logging.info("pronto role=%s maquina=%s pid=%d endereco=%s", args.role, socket.gethostname(), os.getpid(), listen)
        if args.ready_file:
            Path(args.ready_file).write_text(json.dumps({"role": args.role, "machine": socket.gethostname(), "process_id": os.getpid(), "address": listen}), encoding="utf-8")
        while not stopped.wait(0.2):
            if args.stop_file and Path(args.stop_file).exists():
                break
    finally:
        server.stop(grace=3).wait()
        if registry:
            registry.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
