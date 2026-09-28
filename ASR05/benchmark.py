"""Executa os três cenários com a mesma carga e grava medições reais."""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import selectors
import signal
import statistics
import subprocess
import sys

from cliente import executar, gerar_requisicoes

PASTA = Path(__file__).resolve().parent
CENARIOS = (("A", "single", "single"), ("B", "single", "multi"), ("C", "multi", "multi"))


@contextmanager
def servidor_em_execucao(modo, concorrencia=100):
    processo = subprocess.Popen(
        [sys.executable, "-B", str(PASTA / "servidor.py"), modo,
         "--porta", "0", "--concorrencia", str(concorrencia)],
        cwd=PASTA, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )
    try:
        with selectors.DefaultSelector() as seletor:
            seletor.register(processo.stdout, selectors.EVENT_READ)
            if not seletor.select(timeout=10):
                raise RuntimeError("Servidor nao iniciou em 10 segundos")
        linha = processo.stdout.readline().strip()
        if not linha.startswith("PRONTO "):
            raise RuntimeError("Falha ao iniciar servidor: " + linha)
        _, host, porta, _ = linha.split()
        yield (host, int(porta))
    finally:
        if processo.poll() is None:
            processo.send_signal(signal.SIGINT)
        try:
            processo.communicate(timeout=15)
        except subprocess.TimeoutExpired:
            processo.kill()
            processo.communicate()


def medir(cenario, requisicoes, concorrencia):
    nome, cliente, servidor = cenario
    with servidor_em_execucao(servidor, concorrencia) as endereco:
        metricas, _ = executar(requisicoes, cliente, [endereco], concorrencia)
    if not metricas["valido"] or metricas["respostas"] != len(requisicoes):
        raise RuntimeError(f"Benchmark invalido no cenario {nome}: {metricas}")
    return {"cenario": nome, "cliente": cliente, "servidor": servidor, **metricas}


def relatorio(dados):
    ambiente = dados["ambiente"]
    linhas = [
        "# Experimento ASR05", "",
        "Medições reais geradas por `python3 -B benchmark.py`. Nenhum tempo é simulado.", "",
        f"- Data UTC: {ambiente['data_utc']}",
        f"- Python: {ambiente['python']}",
        f"- Sistema operacional: {ambiente['sistema']}",
        f"- Arquitetura: {ambiente['arquitetura']}; CPUs lógicas disponíveis: {ambiente['cpus']}.",
        "- Rede: TCP IPv4 em localhost (127.0.0.1), cliente e servidor na mesma máquina.",
        f"- Requisições por execução: {dados['quantidade']}; seed: {dados['seed']}.",
        f"- Concorrência máxima: {dados['concorrencia']} no cliente e no servidor multi.",
        f"- Repetições por cenário: {dados['repeticoes']}; timeout de socket: 10 s.",
        f"- SHA-256 da lista de requisições: `{dados['sha256_carga']}`.", "",
        "## Método", "",
        "A lista é gerada uma única vez e reutilizada, sem alterações, em todas as execuções. "
        "As operações e suas quantidades são: " + ", ".join(f"{k}: {v}" for k, v in dados['operacoes'].items()) + ".",
        "Cada execução inicia um novo servidor; sua inicialização fica fora da medição. "
        "A ordem A/B/C é rotacionada entre repetições para reduzir o efeito da ordem. "
        "Não há aquecimento separado nem sleeps artificiais no processamento. "
        "Cada requisição abre uma conexão, envia uma linha e recebe uma linha. "
        "O intervalo de perf_counter começa antes do envio (ou criação da primeira thread) "
        "e termina após todas as respostas, validações e joins. "
        "Assim, criação de threads, sockets, validação e espera entre lotes entram no custo. "
        "Geração da carga e impressão dos resumos ficam fora desse intervalo.", "",
        "## Verificações preliminares", "",
        "Após os testes funcionais, os tamanhos 10, 20, 100, 500 e 1000 foram "
        "executados nos três cenários. Todas as respostas foram recebidas e validadas, sem erros ou timeouts.", "",
        "| Requisições | Cenário | Respostas | Sucessos | Erros | Tempo (s) |",
        "|---|---|---|---|---|---|",
    ]
    for item in dados["preliminares"]:
        linhas.append(f"| {item['requisicoes']} | {item['cenario']} | {item['respostas']} | {item['sucessos']} | {item['erros']} | {item['tempo']:.6f} |")
    linhas += ["", "## Comparação", "",
        "| Cenário | Cliente | Servidor | Requisições | Tempo médio (s) | Req/s |",
        "|---------|---------|----------|-------------|-----------------|-------|"]
    medias = {}
    for nome, cliente, servidor in CENARIOS:
        itens = [item for item in dados["execucoes"] if item["cenario"] == nome]
        tempos = [item["tempo"] for item in itens]
        medias[nome] = statistics.mean(tempos)
        linhas.append(f"| {nome} | {cliente.title()} | {servidor.title()} | {dados['quantidade']} | {medias[nome]:.6f} | {statistics.mean(item['throughput'] for item in itens):.2f} |")
    linhas += ["", "Req/s é a média aritmética dos throughputs individuais (N / tempo), "
               "que pode diferir de N / tempo médio.", "", "## Execuções individuais", "",
        "| Repetição | Cenário | Tempo (s) | Req/s | Respostas | Sucessos | Erros | Timeouts | Inválidas |",
        "|---|---|---|---|---|---|---|---|---|"]
    for item in dados["execucoes"]:
        linhas.append(f"| {item['repeticao']} | {item['cenario']} | {item['tempo']:.6f} | {item['throughput']:.2f} | {item['respostas']} | {item['sucessos']} | {item['erros']} | {item['timeouts']} | {item['respostas_invalidas']} |")
    linhas += ["", "| Cenário | Mínimo (s) | Máximo (s) | Desvio padrão amostral (s) |", "|---|---|---|---|"]
    for nome, _, _ in CENARIOS:
        tempos = [item["tempo"] for item in dados["execucoes"] if item["cenario"] == nome]
        linhas.append(f"| {nome} | {min(tempos):.6f} | {max(tempos):.6f} | {statistics.stdev(tempos):.6f} |")
    ordem = sorted(medias, key=medias.get)
    linhas += ["", "## Análise", "",
        f"A ordem observada do menor para o maior tempo médio foi {' → '.join(ordem)}. "
        f"B/A = {medias['B'] / medias['A']:.2f} e C/A = {medias['C'] / medias['A']:.2f} em tempo médio.",
        "No cenário B o cliente espera a resposta antes de enviar a próxima requisição; "
        "portanto há no máximo uma requisição ativa. As threads do servidor não permitem "
        "sobrepor esse trabalho sequencial e ainda exigem criação e escalonamento de threads.",
        "No cenário C há requisições concorrentes, mas as três operações são muito pequenas. "
        "Criação de threads nas duas pontas, conexões TCP, trocas de contexto e execução Python "
        "podem custar mais do que o trabalho útil. Na implementação CPython usada, o GIL "
        "também limita execução simultânea de código Python; isso não impede sobreposição de I/O. "
        "Esses são mecanismos plausíveis para interpretar os tempos, não custos isolados medidos.",
        "Os resultados descrevem esta carga curta em localhost; não demonstram vantagem universal "
        "de um modelo, nem permitem extrapolar para operações demoradas, outras máquinas ou redes. "
        "O limite de concorrência e o uso de lotes também influenciam o resultado. "
        "Todos os ensaios incluídos tiveram zero perdas, erros, timeouts e respostas inválidas.", "",
        "Os dados completos estão em `resultados.json`. Para reproduzir: "
        f"`python3 -B benchmark.py --quantidade {dados['quantidade']} --seed {dados['seed']} "
        f"--concorrencia {dados['concorrencia']} --repeticoes {dados['repeticoes']}`.", "",
    ]
    return "\n".join(linhas)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quantidade", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--concorrencia", type=int, default=100)
    parser.add_argument("--repeticoes", type=int, default=5)
    args = parser.parse_args()
    if args.quantidade < 1 or args.concorrencia < 1 or args.repeticoes < 3:
        parser.error("quantidade/concorrencia positivas e pelo menos 3 repeticoes")
    preliminares = []
    for quantidade in (10, 20, 100, 500, 1000):
        carga = gerar_requisicoes(quantidade, args.seed)
        for cenario in CENARIOS:
            resultado = medir(cenario, carga, args.concorrencia)
            preliminares.append(resultado)
            print(f"Preliminar {cenario[0]} N={quantidade}: {resultado['sucessos']} sucessos, {resultado['erros']} erros", flush=True)
    carga = gerar_requisicoes(args.quantidade, args.seed)
    execucoes = []
    for repeticao in range(args.repeticoes):
        deslocamento = repeticao % len(CENARIOS)
        for cenario in CENARIOS[deslocamento:] + CENARIOS[:deslocamento]:
            resultado = medir(cenario, carga, args.concorrencia)
            resultado["repeticao"] = repeticao + 1
            execucoes.append(resultado)
            print(f"Repeticao {repeticao + 1}, {cenario[0]}: {resultado['tempo']:.6f}s, {resultado['throughput']:.2f} req/s, {resultado['sucessos']} sucessos, {resultado['erros']} erros", flush=True)
    dados = {
        "ambiente": {"data_utc": datetime.now(timezone.utc).isoformat(), "python": sys.version,
                     "sistema": platform.platform(), "arquitetura": platform.machine(), "cpus": os.cpu_count()},
        "quantidade": args.quantidade, "seed": args.seed, "concorrencia": args.concorrencia,
        "repeticoes": args.repeticoes,
        "sha256_carga": hashlib.sha256("\n".join(r.mensagem for r in carga).encode()).hexdigest(),
        "operacoes": {op: sum(r.mensagem.startswith(op + "|") for r in carga) for op in ("SOMA", "MAIUSCULA", "TAMANHO")},
        "preliminares": preliminares, "execucoes": execucoes,
    }
    (PASTA / "resultados.json").write_text(json.dumps(dados, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (PASTA / "resultados.md").write_text(relatorio(dados), encoding="utf-8")
    print("Resultados reais gravados em resultados.md e resultados.json.")


if __name__ == "__main__":
    main()
