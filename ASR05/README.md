# ASR05 — sockets TCP e threads

Esta pasta reconstrói a base necessária da **ASR04**, que não havia sido
implementada: cliente e servidor sequenciais com processamento remoto de
operações distintas. A **ASR05** acrescenta os modos multithread e compara
três cenários, sem dependências externas (Python 3.8 ou posterior).

## Arquivos

- `servidor.py`: processamento, modo single e modo multi.
- `cliente.py`: geração determinística, modos single/multi, validação e medição.
- `protocolo.py`: envio e leitura de mensagens delimitadas por `\n`.
- `testes.py`: testes funcionais, de protocolo e de contabilização de erros.
- `benchmark.py`: executa os três cenários e salva as medições.
- `resultados.md` e `resultados.json`: relatório e dados reais do experimento.

## Operações e protocolo

TCP IPv4, texto UTF-8, uma conexão por requisição. Cada mensagem termina com
`\n`, tanto na requisição quanto na resposta. `receber_linha` usa um leitor
com buffer (`socket.makefile` / `readline`) que acumula bytes até o delimitador,
sem supor que um `send` corresponde a um `recv`. O limite é 65.536 bytes por
mensagem, incluindo o terminador; quebras de linha dentro dos parâmetros
não são permitidas. Mensagens incompletas ou inválidas retornam `ERRO|motivo`.

| Requisição (seguida de `\n`) | Resposta (seguida de `\n`) |
|---|---|
| `SOMA\|10,20` | `30` |
| `MAIUSCULA\|sistemas distribuidos` | `SISTEMAS DISTRIBUIDOS` |
| `TAMANHO\|hello` | `5` |

`SOMA` aceita dois números finitos (incluindo negativos e decimais com ponto),
com aritmética `Decimal` na precisão padrão de 28 algarismos significativos.
`MAIUSCULA` usa `str.upper()` e `TAMANHO` conta caracteres Unicode com `len()`,
não bytes. Strings vazias são aceitas. A função `processar_requisicao`
separa operação e parâmetros e trata formatos e operações inválidos.

## Execução

Partindo do diretório que contém `Sistemas-Distribuidos`:

```bash
cd Sistemas-Distribuidos/ASR05
```

Use dois terminais nessa pasta. Execute somente um servidor por porta.
Encerre o servidor com Ctrl+C antes de trocar seu modo.

```bash
# Cenário A — terminal 1
python3 -B servidor.py single
# Cenário A — terminal 2
python3 -B cliente.py single 2000
```

```bash
# Cenários B e C — terminal 1
python3 -B servidor.py multi
# Cenário B — terminal 2
python3 -B cliente.py single 2000
# Cenário C — terminal 2
python3 -B cliente.py multi 2000 --concorrencia 100
```

O argumento posicional do cliente define a quantidade (padrão: 1000).
Para uma demonstração pequena: `python3 -B cliente.py multi 10 --verbose`.
A seed padrão é 42, configurável com `--seed`. A geração ocorre antes da
medição e usa um gerador aleatório local; os mesmos N e seed produzem a mesma
lista. As respostas esperadas são calculadas no cliente para validação.

O modo single do servidor não cria threads de processamento. No modo multi,
cada conexão/requisição ganha **uma nova Thread**, limitada por um semáforo
(padrão: 100 ativas, configurável com `--concorrencia`). O laço principal
continua aceitando conexões enquanto há capacidade; o limite impõe espera
quando todas as vagas estão ocupadas. O cliente multi também cria **uma nova
Thread para cada requisição**, em lotes de até `--concorrencia` threads,
com `join()` em todas antes do próximo lote. Não há pool com reutilização
de threads. Cada thread tem seu próprio socket e sua posição na lista de
resultados. Não há socket compartilhado entre threads.

O timeout padrão é 10 segundos (`--timeout` em ambos os programas).
O cliente mostra requisições, respostas recebidas, sucessos, erros, timeouts,
respostas inválidas, tempo e throughput; retorna código 1 se houver falhas.
Erros são o total de requisições sem sucesso, incluindo timeouts e respostas
inválidas. Um ensaio com qualquer erro é inválido, mesmo que imprima throughput.
Os detalhes só aparecem com `--verbose`, após a medição.

## Múltiplos servidores

O cliente distribui por round-robin, usando o índice original da requisição.
É possível editar `SERVIDORES` em `cliente.py` ou repetir `--servidor`:

```bash
# Um servidor em cada terminal (ou em máquinas distintas)
python3 -B servidor.py multi --porta 5000
python3 -B servidor.py multi --porta 5001
# Cliente em outro terminal
python3 -B cliente.py multi 2000 --servidor 127.0.0.1:5000 --servidor 127.0.0.1:5001
```

Para acesso entre máquinas, use `--host 0.0.0.0` no servidor e o IP real em
`--servidor IP:5000` no cliente. O experimento registrado utiliza um único
servidor em localhost para manter a mesma topologia nos três cenários.

## Testes e reprodução do benchmark

```bash
python3 -B testes.py
python3 -B benchmark.py --quantidade 2000 --seed 42 --concorrencia 100 --repeticoes 5
```

O benchmark inicia e encerra seus próprios servidores, em portas locais livres.
Primeiro valida 10, 20, 100, 500 e 1000 requisições em cada cenário. Depois
executa cinco repetições por cenário com a **mesma lista** de 2000 requisições,
rotacionando a ordem dos cenários. `perf_counter` mede conexão, envio,
processamento remoto e resposta, incluindo criação/join de threads e validação,
mas excluindo geração da carga, inicialização do servidor e impressão.

Ao concluir sem perdas nem respostas inválidas, o script grava `resultados.md`
e `resultados.json` (substituindo as medições anteriores). O relatório contém
tempos individuais, média, mínimo, máximo, desvio padrão amostral e média de
requisições por segundo. Não há sleeps artificiais, nem impressão por requisição
nos ensaios. Multithreading pode perder desempenho nesta carga curta em localhost.

Nenhum arquivo das outras atividades é necessário ou modificado. A pasta foi
fornecida sem repositório Git; a URL de entrega deve ser a do repositório do
aluno após a publicação. Nenhum push é realizado pelos programas.
