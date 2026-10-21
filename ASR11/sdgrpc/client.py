"""Cliente que recebe somente o bootstrap de nomes e descobre os dois destinos."""
import argparse
import json
import os
import socket
import sys

import grpc
from sdgrpc import contracts_pb2 as pb
from sdgrpc import contracts_pb2_grpc as rpc
from sdgrpc.naming import endpoint

TIMEOUT = 5


def lookup(naming_address, name):
    with grpc.insecure_channel(naming_address) as channel:
        address = rpc.NamingServiceStub(channel).Lookup(pb.Name(name=name), timeout=TIMEOUT)
    return endpoint(address)


def calculate(naming_address, a, b, operation):
    target = lookup(naming_address, "calculadora")
    with grpc.insecure_channel(target) as channel:
        result = rpc.CalculatorServiceStub(channel).Calculate(pb.Calculation(a=a, b=b, operation=operation), timeout=TIMEOUT)
    return {"service": "calculadora", "discovered_address": target, "result": result.result, "machine": result.machine, "process_id": result.process_id}


def analyze(naming_address, text):
    target = lookup(naming_address, "texto")
    with grpc.insecure_channel(target) as channel:
        result = rpc.TextServiceStub(channel).Analyze(pb.TextRequest(text=text), timeout=TIMEOUT)
    return {"service": "texto", "discovered_address": target, "uppercase": result.uppercase, "characters": result.characters, "words": result.words, "machine": result.machine, "process_id": result.process_id}


def demo(naming_address):
    return {"client": {"machine": socket.gethostname(), "process_id": os.getpid()}, "naming_address": naming_address,
            "calculator": calculate(naming_address, 12, 3, pb.ADD),
            "text": analyze(naming_address, "Sistemas Distribuidos com gRPC")}


def main():
    parser = argparse.ArgumentParser(description="Cliente gRPC com descoberta por nomes")
    parser.add_argument("--naming", default="127.0.0.1:50061")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("demo")
    calc = commands.add_parser("calc")
    calc.add_argument("a", type=float)
    calc.add_argument("b", type=float)
    calc.add_argument("--operation", choices=("add", "subtract", "multiply", "divide"), default="add")
    text = commands.add_parser("text")
    text.add_argument("text")
    for action in ("lookup", "unbind", "bind", "rebind"):
        command = commands.add_parser(action)
        command.add_argument("name")
        if action in ("bind", "rebind"):
            command.add_argument("host")
            command.add_argument("port", type=int)
    args = parser.parse_args()
    try:
        if args.command == "demo":
            result = demo(args.naming)
        elif args.command == "calc":
            result = calculate(args.naming, args.a, args.b, pb.Operation.Value(args.operation.upper()))
        elif args.command == "text":
            result = analyze(args.naming, args.text)
        elif args.command == "lookup":
            result = {"name": args.name, "address": lookup(args.naming, args.name)}
        else:
            with grpc.insecure_channel(args.naming) as channel:
                stub = rpc.NamingServiceStub(channel)
                if args.command == "unbind":
                    response = stub.Unbind(pb.Name(name=args.name), timeout=TIMEOUT)
                else:
                    binding = pb.Binding(name=args.name, address=pb.Address(host=args.host, port=args.port))
                    response = getattr(stub, args.command.title())(binding, timeout=TIMEOUT)
            result = {"status": response.message}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except grpc.RpcError as exc:
        print(json.dumps({"error": exc.code().name, "details": exc.details()}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
