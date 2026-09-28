"""Enquadramento UTF-8: uma linha por mensagem, uma conexão por requisição."""

LIMITE_BYTES = 65536


def receber_linha(fluxo):
    """readline mantém o buffer mesmo se TCP fragmentar ou agrupar os dados."""
    dados = fluxo.readline(LIMITE_BYTES + 1)
    if not dados:
        raise ValueError("conexao encerrada sem mensagem")
    if len(dados) > LIMITE_BYTES:
        raise ValueError("mensagem excede o limite de 65536 bytes")
    if not dados.endswith(b"\n"):
        raise ValueError("mensagem sem terminador de linha")
    return dados[:-1].decode("utf-8")


def enviar_linha(sock, mensagem):
    if "\n" in mensagem:
        raise ValueError("mensagem nao pode conter quebra de linha")
    dados = (mensagem + "\n").encode("utf-8")
    if len(dados) > LIMITE_BYTES:
        raise ValueError("mensagem excede o limite de 65536 bytes")
    sock.sendall(dados)
