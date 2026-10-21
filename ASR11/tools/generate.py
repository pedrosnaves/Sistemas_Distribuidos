"""Gera mensagens e stubs a partir do contrato, sem editar codigo gerado."""
from pathlib import Path
import subprocess
import sys


def main():
    root = Path(__file__).resolve().parents[1]
    subprocess.run([sys.executable, "-m", "grpc_tools.protoc", "-Iprotos", "--python_out=.", "--pyi_out=.", "--grpc_python_out=.", "protos/sdgrpc/contracts.proto"], cwd=root, check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
