import socket
import sys


def chamar(host, porta, requisicao):
    with socket.create_connection((host, porta), timeout=30) as conexao:
        conexao.sendall((requisicao + "\n").encode("utf-8"))
        with conexao.makefile("r", encoding="utf-8") as resposta:
            return resposta.readline().rstrip("\n")


if __name__ == "__main__":
    host = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
    porta = int(sys.argv[2]) if len(sys.argv) > 2 else 5004
    for requisicao in ("SOMA|12|3", "MAIUSCULA|sistemas distribuidos", "TAMANHO|olá"):
        print(requisicao, "->", chamar(host, porta, requisicao))
