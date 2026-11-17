import socket
import sys
from threading import Thread


def processar(requisicao):
    partes = requisicao.split("|", 1)
    if len(partes) != 2:
        return "ERRO: use OPERACAO|dados"
    operacao, dados = partes
    try:
        if operacao == "SOMA":
            a, b = dados.split("|")
            return str(int(a) + int(b))
        if operacao == "MAIUSCULA":
            return dados.upper()
        if operacao == "TAMANHO":
            return str(len(dados))
        return "ERRO: operacao desconhecida"
    except ValueError:
        return "ERRO: informe dois inteiros em SOMA|a|b"


def atender(conexao):
    with conexao:
        with conexao.makefile("r", encoding="utf-8") as entrada:
            requisicao = entrada.readline().rstrip("\n")
        resposta = processar(requisicao)
        conexao.sendall((resposta + "\n").encode("utf-8"))


if __name__ == "__main__":
    modo = sys.argv[1] if len(sys.argv) > 1 else "multi"
    host = sys.argv[2] if len(sys.argv) > 2 else "0.0.0.0"
    porta = int(sys.argv[3]) if len(sys.argv) > 3 else 5005
    if modo not in ("single", "multi"):
        raise SystemExit("Use: python3 servidor.py single|multi [host] [porta]")
    with socket.socket() as servidor:
        servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        servidor.bind((host, porta))
        servidor.listen(100)
        print(f"Servidor {modo} em {host}:{porta}", flush=True)
        while True:
            conexao, endereco = servidor.accept()
            if modo == "multi":
                Thread(target=atender, args=(conexao,), daemon=True).start()
            else:
                atender(conexao)
