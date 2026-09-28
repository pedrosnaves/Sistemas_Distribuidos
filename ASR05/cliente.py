"""Cliente automatizado: sequencial ou uma nova thread por requisição."""
import argparse
from dataclasses import dataclass
import random
import socket
import string
import threading
from time import perf_counter

from protocolo import enviar_linha, receber_linha

SERVIDORES = [("127.0.0.1", 5000)]
SEED = 42


@dataclass(frozen=True)
class Requisicao:
    mensagem: str
    esperado: str


@dataclass
class Resultado:
    resposta: str = None
    erro: str = None


def gerar_requisicoes(quantidade, seed=SEED):
    rng = random.Random(seed)
    requisicoes = []
    for _ in range(quantidade):
        operacao = rng.choice(("SOMA", "MAIUSCULA", "TAMANHO"))
        if operacao == "SOMA":
            a, b = rng.randint(-10000, 10000), rng.randint(-10000, 10000)
            requisicoes.append(Requisicao(f"SOMA|{a},{b}", str(a + b)))
        else:
            texto = "".join(rng.choices(string.ascii_letters + " 0123456789", k=rng.randint(0, 80)))
            esperado = texto.upper() if operacao == "MAIUSCULA" else str(len(texto))
            requisicoes.append(Requisicao(f"{operacao}|{texto}", esperado))
    return requisicoes


def enviar_requisicao(requisicao, servidor, timeout=10):
    try:
        with socket.create_connection(servidor, timeout=timeout) as sock:
            sock.settimeout(timeout)
            enviar_linha(sock, requisicao.mensagem)
            with sock.makefile("rb") as fluxo:
                resposta = receber_linha(fluxo)
        return Resultado(resposta, None if resposta == requisicao.esperado else "resposta_invalida")
    except (TimeoutError, socket.timeout):
        return Resultado(erro="timeout")
    except (ValueError, UnicodeError):
        return Resultado(erro="protocolo_invalido")
    except OSError:
        return Resultado(erro="conexao")


def executar(requisicoes, modo, servidores=None, concorrencia=100, timeout=10):
    servidores = SERVIDORES if servidores is None else servidores
    if modo not in ("single", "multi") or not servidores or concorrencia < 1 or timeout <= 0:
        raise ValueError("configuracao invalida")
    resultados = [None] * len(requisicoes)

    def enviar(indice):
        resultados[indice] = enviar_requisicao(
            requisicoes[indice], servidores[indice % len(servidores)], timeout
        )

    inicio = perf_counter()
    if modo == "single":
        for indice in range(len(requisicoes)):
            enviar(indice)
    else:
        for inicio_lote in range(0, len(requisicoes), concorrencia):
            threads = []
            try:
                for indice in range(inicio_lote, min(inicio_lote + concorrencia, len(requisicoes))):
                    thread = threading.Thread(target=enviar, args=(indice,))
                    try:
                        thread.start()
                    except RuntimeError:
                        resultados[indice] = Resultado(erro="criacao_thread")
                    else:
                        threads.append(thread)
            finally:
                for thread in threads:
                    thread.join()
    tempo = perf_counter() - inicio
    sucessos = sum(r is not None and r.erro is None for r in resultados)
    metricas = {
        "requisicoes": len(requisicoes),
        "respostas": sum(r is not None and r.resposta is not None for r in resultados),
        "sucessos": sucessos,
        "erros": len(requisicoes) - sucessos,
        "timeouts": sum(r is not None and r.erro == "timeout" for r in resultados),
        "respostas_invalidas": sum(r is not None and r.erro in ("resposta_invalida", "protocolo_invalido") for r in resultados),
        "tempo": tempo,
        "throughput": len(requisicoes) / tempo,
        "valido": sucessos == len(requisicoes),
    }
    return metricas, resultados


def endereco(valor):
    try:
        host, porta = valor.rsplit(":", 1)
        porta = int(porta)
        if not host or not 1 <= porta <= 65535:
            raise ValueError()
        return host, porta
    except ValueError:
        raise argparse.ArgumentTypeError("use HOST:PORTA") from None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("modo", choices=("single", "multi"))
    parser.add_argument("quantidade", type=int, nargs="?", default=1000)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--concorrencia", type=int, default=100)
    parser.add_argument("--timeout", type=float, default=10)
    parser.add_argument("--servidor", type=endereco, action="append")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()
    if args.quantidade < 1 or args.concorrencia < 1 or args.timeout <= 0:
        parser.error("quantidade, concorrencia e timeout devem ser positivos")
    requisicoes = gerar_requisicoes(args.quantidade, args.seed)
    metricas, resultados = executar(requisicoes, args.modo, args.servidor, args.concorrencia, args.timeout)
    if args.verbose:
        for requisicao, resultado in zip(requisicoes, resultados):
            print(requisicao.mensagem, "->", resultado)
    for nome, valor in metricas.items():
        print(f"{nome}: {valor:.6f}" if isinstance(valor, float) else f"{nome}: {valor}")
    if not metricas["valido"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
