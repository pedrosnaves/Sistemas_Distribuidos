# ASR05 - Cliente e servidor com threads

Parti dos programas da ASR04 e acrescentei uma nova `Thread` para cada requisição no servidor e no cliente. O processamento das três operações e o protocolo TCP são os mesmos.

Python 3, sem bibliotecas adicionais. Execute na pasta `ASR05`:

```bash
# Server-01, terminal 1: servidor sequencial
python3 servidor.py single 0.0.0.0 5005
# Server-01, terminal 2: servidor com threads
python3 servidor.py multi 0.0.0.0 5007

# Server-02: demonstração de cada cenário
python3 cliente.py IP_SERVIDOR single 2000 5005
python3 cliente.py IP_SERVIDOR single 2000 5007
python3 cliente.py IP_SERVIDOR multi 2000 5007

# Ou execute automaticamente três repetições dos três cenários:
python3 experimento.py IP_SERVIDOR 2000
```

O cliente gera a mesma carga com seed 42, alternando soma, maiúsculas e tamanho. No modo multi, cria uma nova thread e um socket para cada requisição, em lotes de até 50 threads. Ele confere as respostas e mede o tempo com `perf_counter()`. O experimento imprime os tempos de cada repetição e as médias. Encerre os servidores com Ctrl+C.

## Relato do experimento

Experimento repetido em 17/11/2026 nas EC2 t2.small, com Python 3.14.4: servidor na Server-01 (`172.31.65.237`) e cliente na Server-02 (`172.31.68.163`). Foram três ensaios de 2.000 requisições por cenário, com a mesma carga gerada por seed 42 e ordem alternada dos cenários. Antes dos ensaios, fiz 20 requisições de aquecimento por cenário. As 18.000 respostas medidas estavam corretas, sem erros.

| Cenário | Repetição 1 (s) | Repetição 2 (s) | Repetição 3 (s) | Média (s) |
| --- | ---: | ---: | ---: | ---: |
| A: ambos single | 1.197708 | 1.206387 | 1.193164 | 1.199086 |
| B: servidor multi | 1.357391 | 1.378276 | 1.375697 | 1.370455 |
| C: ambos multi | 0.803457 | 0.804182 | 0.781958 | 0.796532 |

O tempo inclui conexão, envio, processamento, resposta, conferência das respostas e criação/espera das threads. A geração dos dados e a impressão ficam fora da medição. O cliente multi usa até 50 threads por lote; cada requisição tem uma nova thread e seu próprio socket. As operações são curtas e não há pausas artificiais no processamento.

O tempo médio de C foi 33.6% menor que o de A. A razão entre o tempo médio de B e de A foi 1.14.

Com threads apenas no servidor, o cliente ainda espera cada resposta antes de enviar a próxima requisição. Ele não oferece várias requisições simultâneas para aproveitar a concorrência do servidor. Com threads nos dois lados, parte das esperas pode ser sobreposta. Criar threads também tem custo; o resultado vale para a carga e o ambiente deste experimento.
