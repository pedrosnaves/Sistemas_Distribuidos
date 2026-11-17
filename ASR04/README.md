# ASR04 - Cliente e servidor TCP

Extensão do [exemplo do professor](https://github.com/professorfabio/ClientServerBasics-2.0), apresentado no slide 5 do Capítulo 2. O cliente escolhe uma operação por requisição; o servidor processa os dados e devolve o resultado.

| Requisição | Resposta |
| --- | --- |
| `SOMA\|12\|3` | `15` |
| `MAIUSCULA\|sistemas distribuidos` | `SISTEMAS DISTRIBUIDOS` |
| `TAMANHO\|olá` | `3` |

Python 3, sem bibliotecas adicionais. Execute na pasta `ASR04`:

```bash
# Máquina do servidor
python3 servidor.py 0.0.0.0 5004
# Outra máquina: use o IP privado do servidor
python3 cliente.py IP_SERVIDOR 5004
```

Cada requisição abre uma conexão TCP. As mensagens são texto UTF-8 terminado por uma quebra de linha: `readline()` aguarda a mensagem completa, pois TCP transmite um fluxo de bytes. Os dados de texto devem ocupar uma única linha. O servidor atende uma requisição por vez. Para encerrar, pressione Ctrl+C.

A ASR05 parte destes mesmos programas e acrescenta threads e geração automática de requisições.

## Teste na AWS

Em 17/11/2026, o servidor executou na Server-01 e o cliente na Server-02. As três respostas foram `15`, `SISTEMAS DISTRIBUIDOS` e `3`, conforme a tabela acima.
