# Experimento ASR05

Medições reais geradas por `python3 -B benchmark.py`. Nenhum tempo é simulado.

- Data UTC: 2026-09-28T02:46:02.783297+00:00
- Python: 3.12.3 (main, Aug 31 2026, 10:18:26) [GCC 13.3.0]
- Sistema operacional: Linux-6.18.33.2-microsoft-standard-WSL2-x86_64-with-glibc2.39
- Arquitetura: x86_64; CPUs lógicas disponíveis: 4.
- Rede: TCP IPv4 em localhost (127.0.0.1), cliente e servidor na mesma máquina.
- Requisições por execução: 2000; seed: 42.
- Concorrência máxima: 100 no cliente e no servidor multi.
- Repetições por cenário: 5; timeout de socket: 10 s.
- SHA-256 da lista de requisições: `0cc4138d7f60c66b053b9adb43a7cd7b882c6fb83c1e1eb1d0b4b704778867da`.

## Método

A lista é gerada uma única vez e reutilizada, sem alterações, em todas as execuções. As operações e suas quantidades são: SOMA: 651, MAIUSCULA: 655, TAMANHO: 694.
Cada execução inicia um novo servidor; sua inicialização fica fora da medição. A ordem A/B/C é rotacionada entre repetições para reduzir o efeito da ordem. Não há aquecimento separado nem sleeps artificiais no processamento. Cada requisição abre uma conexão, envia uma linha e recebe uma linha. O intervalo de perf_counter começa antes do envio (ou criação da primeira thread) e termina após todas as respostas, validações e joins. Assim, criação de threads, sockets, validação e espera entre lotes entram no custo. Geração da carga e impressão dos resumos ficam fora desse intervalo.

## Verificações preliminares

Após os testes funcionais, os tamanhos 10, 20, 100, 500 e 1000 foram executados nos três cenários. Todas as respostas foram recebidas e validadas, sem erros ou timeouts.

| Requisições | Cenário | Respostas | Sucessos | Erros | Tempo (s) |
|---|---|---|---|---|---|
| 10 | A | 10 | 10 | 0 | 0.007910 |
| 10 | B | 10 | 10 | 0 | 0.008166 |
| 10 | C | 10 | 10 | 0 | 0.008842 |
| 20 | A | 20 | 20 | 0 | 0.006580 |
| 20 | B | 20 | 20 | 0 | 0.011897 |
| 20 | C | 20 | 20 | 0 | 0.019143 |
| 100 | A | 100 | 100 | 0 | 0.029328 |
| 100 | B | 100 | 100 | 0 | 0.060339 |
| 100 | C | 100 | 100 | 0 | 0.079016 |
| 500 | A | 500 | 500 | 0 | 0.147025 |
| 500 | B | 500 | 500 | 0 | 0.309557 |
| 500 | C | 500 | 500 | 0 | 0.348752 |
| 1000 | A | 1000 | 1000 | 0 | 0.251596 |
| 1000 | B | 1000 | 1000 | 0 | 0.590491 |
| 1000 | C | 1000 | 1000 | 0 | 0.694224 |

## Comparação

| Cenário | Cliente | Servidor | Requisições | Tempo médio (s) | Req/s |
|---------|---------|----------|-------------|-----------------|-------|
| A | Single | Single | 2000 | 0.563683 | 3570.24 |
| B | Single | Multi | 2000 | 1.162540 | 1722.46 |
| C | Multi | Multi | 2000 | 1.510448 | 1327.17 |

Req/s é a média aritmética dos throughputs individuais (N / tempo), que pode diferir de N / tempo médio.

## Execuções individuais

| Repetição | Cenário | Tempo (s) | Req/s | Respostas | Sucessos | Erros | Timeouts | Inválidas |
|---|---|---|---|---|---|---|---|---|
| 1 | A | 0.570719 | 3504.35 | 2000 | 2000 | 0 | 0 | 0 |
| 1 | B | 1.159091 | 1725.49 | 2000 | 2000 | 0 | 0 | 0 |
| 1 | C | 1.444752 | 1384.32 | 2000 | 2000 | 0 | 0 | 0 |
| 2 | B | 1.089106 | 1836.37 | 2000 | 2000 | 0 | 0 | 0 |
| 2 | C | 1.424415 | 1404.09 | 2000 | 2000 | 0 | 0 | 0 |
| 2 | A | 0.609511 | 3281.32 | 2000 | 2000 | 0 | 0 | 0 |
| 3 | C | 1.503875 | 1329.90 | 2000 | 2000 | 0 | 0 | 0 |
| 3 | A | 0.551156 | 3628.74 | 2000 | 2000 | 0 | 0 | 0 |
| 3 | B | 1.203876 | 1661.30 | 2000 | 2000 | 0 | 0 | 0 |
| 4 | A | 0.598919 | 3339.35 | 2000 | 2000 | 0 | 0 | 0 |
| 4 | B | 1.189117 | 1681.92 | 2000 | 2000 | 0 | 0 | 0 |
| 4 | C | 1.555050 | 1286.13 | 2000 | 2000 | 0 | 0 | 0 |
| 5 | B | 1.171511 | 1707.20 | 2000 | 2000 | 0 | 0 | 0 |
| 5 | C | 1.624150 | 1231.41 | 2000 | 2000 | 0 | 0 | 0 |
| 5 | A | 0.488111 | 4097.43 | 2000 | 2000 | 0 | 0 | 0 |

| Cenário | Mínimo (s) | Máximo (s) | Desvio padrão amostral (s) |
|---|---|---|---|
| A | 0.488111 | 0.609511 | 0.048113 |
| B | 1.089106 | 1.203876 | 0.044441 |
| C | 1.424415 | 1.624150 | 0.081668 |

## Análise

A ordem observada do menor para o maior tempo médio foi A → B → C. B/A = 2.06 e C/A = 2.68 em tempo médio.
No cenário B o cliente espera a resposta antes de enviar a próxima requisição; portanto há no máximo uma requisição ativa. As threads do servidor não permitem sobrepor esse trabalho sequencial e ainda exigem criação e escalonamento de threads.
No cenário C há requisições concorrentes, mas as três operações são muito pequenas. Criação de threads nas duas pontas, conexões TCP, trocas de contexto e execução Python podem custar mais do que o trabalho útil. Na implementação CPython usada, o GIL também limita execução simultânea de código Python; isso não impede sobreposição de I/O. Esses são mecanismos plausíveis para interpretar os tempos, não custos isolados medidos.
Os resultados descrevem esta carga curta em localhost; não demonstram vantagem universal de um modelo, nem permitem extrapolar para operações demoradas, outras máquinas ou redes. O limite de concorrência e o uso de lotes também influenciam o resultado. Todos os ensaios incluídos tiveram zero perdas, erros, timeouts e respostas inválidas.

Os dados completos estão em `resultados.json`. Para reproduzir: `python3 -B benchmark.py --quantidade 2000 --seed 42 --concorrencia 100 --repeticoes 5`.
