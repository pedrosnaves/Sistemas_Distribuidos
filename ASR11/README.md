# ASR11 — Serviços remotos e Serviço de Nomes

Atividade de Sistemas Distribuídos em Python e gRPC, com dois serviços:

- **Soma:** recebe dois números e devolve a soma.
- **Texto:** recebe um texto e devolve suas letras em maiúsculas.

Cada servidor registra seu nome e endereço no Serviço de Nomes. O cliente conhece apenas o IP desse serviço, faz `Lookup` e usa os endereços recebidos para acessar os dois servidores.

## Serviço de Nomes

Os registros ficam em um dicionário na memória:

- `Bind`: registra um nome novo; rejeita nomes duplicados.
- `Lookup`: procura o endereço de um nome.
- `Unbind`: remove um registro.
- `Rebind`: atualiza o endereço de um nome, ou cria o registro se ele não existe.

Ao encerrar o Serviço de Nomes, o dicionário é perdido. Esta é uma implementação didática, sem banco de dados, autenticação ou TLS.

## Preparação

Use Python 3.10 ou superior. Em cada máquina, na pasta `ASR11`:

```bash
python -m pip install -r requirements.txt
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. servicos.proto
```

O segundo comando gera `servicos_pb2.py` e `servicos_pb2_grpc.py`, usados pelos programas. Esses arquivos são gerados automaticamente e não precisam ser escritos pelo aluno.

## Executar em máquinas diferentes

Substitua `IP_NOMES`, `IP_SOMA` e `IP_TEXTO` pelos IPs privados das máquinas. Permita a comunicação TCP nas portas 50061, 50062 e 50063 entre elas. Encerre outros programas que já estejam usando essas portas antes de iniciar.

| Máquina | Programa | Comando |
| --- | --- | --- |
| 1 | Serviço de Nomes | `python servidor_nomes.py` |
| 2 | Soma | `python servidor_soma.py IP_NOMES IP_SOMA` |
| 3 | Texto | `python servidor_texto.py IP_NOMES IP_TEXTO` |
| 4 | Cliente | `python cliente.py IP_NOMES` |

Inicie nessa ordem. Para encerrar um servidor, pressione Ctrl+C. Para repetir tudo do início, encerre os três servidores e inicie novamente nessa ordem, pois `Bind` rejeita nomes já registrados.

Para testar no mesmo computador, abra quatro terminais e use `127.0.0.1` no lugar dos IPs. Isso testa processos diferentes; a execução distribuída da atividade usa as máquinas diferentes indicadas na tabela.

## Saída esperada do cliente

```text
12 + 3 = 15.0
Texto em maiusculas: SISTEMAS DISTRIBUIDOS
Bind / Lookup: 127.0.0.1:6000
Rebind / Lookup: 127.0.0.1:7000
Unbind: registro exemplo removido
```

Os dois últimos endereços são apenas registros de exemplo para demonstrar atualização e remoção; nenhum servidor precisa executar nessas portas.

## Referências

- [gRPC com Python](https://grpc.io/docs/languages/python/quickstart/)
- [Serviço de Nomes simples indicado no enunciado](https://github.com/professorfabio/gRPC-SimpleNamingService)
