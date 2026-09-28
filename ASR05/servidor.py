"""Base ASR04 sequencial e extensão ASR05 com uma thread por requisição."""
import argparse
from decimal import Decimal, DecimalException
import socket
import threading

from protocolo import enviar_linha, receber_linha


def processar_requisicao(requisicao):
    operacao, separador, parametros = requisicao.partition("|")
    if not separador:
        return "ERRO|formato esperado: OPERACAO|PARAMETROS"
    if operacao == "SOMA":
        partes = parametros.split(",")
        if len(partes) != 2:
            return "ERRO|SOMA exige dois numeros separados por virgula"
        try:
            a, b = (Decimal(parte.strip()) for parte in partes)
            if not a.is_finite() or not b.is_finite():
                return "ERRO|numeros devem ser finitos"
            resultado = a + b
            # Evita respostas gigantes produzidas por expoentes extremos.
            if not resultado.is_finite() or abs(resultado.adjusted()) > 1000:
                return "ERRO|resultado fora do intervalo suportado"
            texto = format(resultado, "f")
            return texto.rstrip("0").rstrip(".") if "." in texto else texto
        except (DecimalException, ValueError):
            return "ERRO|numeros invalidos"
    if operacao == "MAIUSCULA":
        return parametros.upper()
    if operacao == "TAMANHO":
        return str(len(parametros))
    return "ERRO|operacao desconhecida"


def atender_requisicao(conn, timeout):
    with conn:
        conn.settimeout(timeout)
        try:
            with conn.makefile("rb") as fluxo:
                try:
                    resposta = processar_requisicao(receber_linha(fluxo))
                except (ValueError, UnicodeError) as erro:
                    resposta = "ERRO|" + str(erro)
                try:
                    enviar_linha(conn, resposta)
                except ValueError:
                    enviar_linha(conn, "ERRO|resposta excede o limite do protocolo")
        except (OSError, TimeoutError):
            # Um cliente desconectado/com timeout não derruba o servidor.
            pass


def servir(modo, host="127.0.0.1", porta=5000, concorrencia=100, timeout=10):
    vagas = threading.Semaphore(concorrencia)
    threads = []

    def executar(conn):
        try:
            atender_requisicao(conn, timeout)
        finally:
            vagas.release()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as servidor:
        servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        servidor.bind((host, porta))
        servidor.listen(256)
        print(f"PRONTO {host} {servidor.getsockname()[1]} {modo}", flush=True)
        try:
            while True:
                if modo == "single":
                    conn, _ = servidor.accept()
                    atender_requisicao(conn, timeout)
                else:
                    # Limita threads ativas, mas cada conexão ganha uma nova Thread.
                    vagas.acquire()
                    try:
                        conn, _ = servidor.accept()
                    except BaseException:
                        vagas.release()
                        raise
                    thread = threading.Thread(target=executar, args=(conn,))
                    try:
                        thread.start()
                    except BaseException:
                        conn.close()
                        vagas.release()
                        raise
                    threads = [ativa for ativa in threads if ativa.is_alive()]
                    threads.append(thread)
        except KeyboardInterrupt:
            pass
        finally:
            for thread in threads:
                thread.join()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("modo", choices=("single", "multi"))
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--porta", type=int, default=5000)
    parser.add_argument("--concorrencia", type=int, default=100)
    parser.add_argument("--timeout", type=float, default=10)
    args = parser.parse_args()
    if args.concorrencia < 1 or args.timeout <= 0:
        parser.error("concorrencia e timeout devem ser positivos")
    servir(args.modo, args.host, args.porta, args.concorrencia, args.timeout)


if __name__ == "__main__":
    main()
