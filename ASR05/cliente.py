import sys
import random
import socket
from threading import Thread
from time import perf_counter


def chamar(host, porta, requisicao):
    with socket.create_connection((host, porta), timeout=30) as conexao:
        conexao.sendall((requisicao + "\n").encode("utf-8"))
        with conexao.makefile("r", encoding="utf-8") as resposta:
            return resposta.readline().rstrip("\n")


def executar(host, porta, modo, quantidade):
    gerador = random.Random(42)
    concorrencia = 50
    carga = []
    for i in range(quantidade):
        a, b = gerador.randint(0, 1000), gerador.randint(0, 1000)
        texto = f"requisição {a}"
        opcoes = [(f"SOMA|{a}|{b}", str(a + b)),
                  (f"MAIUSCULA|{texto}", texto.upper()),
                  (f"TAMANHO|{texto}", str(len(texto)))]
        carga.append(opcoes[i % 3])
    resultados = [False] * quantidade

    def enviar(indice):
        requisicao, esperado = carga[indice]
        try:
            resultados[indice] = chamar(host, porta, requisicao) == esperado
        except OSError:
            resultados[indice] = False

    inicio = perf_counter()
    if modo == "single":
        for i in range(quantidade):
            enviar(i)
    else:
        # Uma nova thread por requisição; no máximo 50 por lote.
        for inicio_lote in range(0, quantidade, concorrencia):
            threads = [Thread(target=enviar, args=(i,))
                       for i in range(inicio_lote, min(inicio_lote + concorrencia, quantidade))]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()
    segundos = perf_counter() - inicio
    corretas = sum(resultados)
    return {"corretas": corretas, "erros": quantidade - corretas, "segundos": segundos}


if __name__ == "__main__":
    host, modo = sys.argv[1:3]
    quantidade = int(sys.argv[3]) if len(sys.argv) > 3 else 2000
    porta = int(sys.argv[4]) if len(sys.argv) > 4 else 5005
    if modo not in ("single", "multi") or quantidade < 1:
        raise SystemExit("Use: cliente.py IP single|multi [quantidade] [porta]")
    resultado = executar(host, porta, modo, quantidade)
    print(resultado)
    raise SystemExit(1 if resultado["erros"] else 0)
