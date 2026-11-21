# MPComm — Trabalho Final de Sistemas Distribuídos (Parte 1)

Este repositório contém a implementação da **Parte 1** do trabalho final de Sistemas Distribuídos, evoluindo o código-base `MPComm`:

- **Parte 1a:** Substituição de sockets TCP nas interações cliente-servidor por **RPC com gRPC**.
- **Parte 1b:** Tratamento de **perda de mensagens** e garantia de **ordenação FIFO** na comunicação multicast entre peers, **mantendo o uso de sockets UDP**.

---

## 1. Funcionalidades e Arquitetura

O sistema mantém os três componentes do `MPComm` original, separando a comunicação em duas camadas:

- **Cliente-Servidor via gRPC (TCP):**
  - `GroupMngr.py`: gerencia os peers ativos (`Register`, `Unregister`, `ListPeers`, `Stop`), guardando `(ip, rpc_port, udp_port)` de cada processo.
  - `comparisonServer.py`: coordena o início das rodadas (`StartRound`), recebe os logs de entrega dos peers (`SubmitLog`), encerra o sistema (`Shutdown`/`Stop`) e verifica perdas, duplicatas, violações FIFO e divergências na ordem global.
  - `peerCommunicatorUDP.py`: registra-se no `GroupManager`, aguarda o comando `StartRound`, realiza o multicast UDP com os demais peers e envia o log final ao `ComparisonServer`.
- **Multicast Peer-to-Peer via Sockets UDP:**
  - Troca de datagramas UDP entre todos os peers com confirmação (`ACK`), retransmissão por timeout e entrega ordenada FIFO por remetente.

```text
  GroupManager (gRPC) ◀── Register / Unregister / ListPeers ──▶ Peers (gRPC + UDP)
          ▲                                                           ▲   ▲
          │ ListPeers / Stop                     StartRound/SubmitLog │   │ UDP Multicast
          └──────────────── ComparisonServer (gRPC) ──────────────────┘   │ (Confiável + FIFO)
                                                                          ▼
                                                                    Outros Peers
```

---

## 2. Detalhes de Implementação

### Parte 1a — RPC com gRPC (`mpcomm.proto`)

Todas as interações cliente-servidor originalmente feitas com `socket(AF_INET, SOCK_STREAM)` e `pickle` foram migradas para três serviços definidos em `mpcomm.proto`:

| Interação | Serviço gRPC | Método |
| :--- | :--- | :--- |
| Registro e remoção de peer | `GroupManager` | `Register(PeerInfo)` / `Unregister(PeerInfo)` |
| Consulta de peers e encerramento | `GroupManager` | `ListPeers(Empty)` / `Stop(Empty)` |
| Início de rodada e desligamento do peer | `PeerControl` | `StartRound(StartRequest)` / `Shutdown(Empty)` |
| Envio do log de mensagens recebidas | `Comparison` | `SubmitLog(PeerLog)` |

Além da migração para gRPC, foram corrigidos problemas do código original, como o `Unregister` ausente no `GroupManager`, a leitura TCP de tamanho fixo (`recv(32768)`) no envio do log e os limites de iteração da comparação em `comparisonServer.py`.

### Parte 1b — Confiabilidade e Ordenação FIFO sobre UDP (`peerCommunicatorUDP.py`)

Os datagramas UDP são serializados em JSON com os tipos `READY`, `READY_ACK`, `DATA`, `DONE` e `ACK`:

1. **Handshake confiável:** cada peer envia `READY` periodicamente até receber `READY_ACK` de todos os `N` peers (usando `threading.Event` em vez de *busy-waiting*). Uma única thread de recepção trata todos os tipos de pacote, evitando descarte de mensagens `DATA` recebidas durante o handshake.
2. **Tratamento de perda de mensagens:** cada mensagem enviada recebe um número de sequência `seq` por remetente e fica registrada em `pending_acks[seq]`. Ao receber `DATA` ou `DONE`, o receptor sempre devolve `ACK` ao remetente. Uma thread auxiliar verifica periodicamente `pending_acks` e retransmite apenas para os peers que ainda não confirmaram após `RETRANSMIT_TIMEOUT` (`0,25 s`).
3. **Ordenação FIFO e deduplicação:** para cada remetente `s`, o receptor mantém `expected_seq[s]` e um *hold-back buffer* (`holdback[s]`):
   - `seq < expected_seq[s]`: mensagem duplicada (descartada após reenviar `ACK`).
   - `seq > expected_seq[s]`: mensagem fora de ordem (retida no `holdback[s]`).
   - `seq == expected_seq[s]`: mensagem entregue e drenagem sequencial das mensagens já armazenadas em `holdback[s]`.
4. **Encerramento seguro (`DONE`):** o marcador de término do remetente é enviado como `seq = num_msgs` dentro do mesmo fluxo FIFO. Dessa forma, ele também é protegido por `ACK`/retransmissão e só é processado após todas as mensagens `0 .. num_msgs - 1` daquele remetente terem sido entregues.
5. **Simulação opcional de falhas:** os parâmetros `--drop-rate` e `--max-delay-ms` permitem injetar descarte e atraso variável assíncrono nos pacotes UDP para demonstrar a recuperação de perdas e a reordenação FIFO em redes locais de baixa latência.

---

## 3. Comparação: Sockets vs. RPC (Vantagens e Desvantagens)

| Aspecto | Sockets TCP + `pickle` (Original) | RPC com gRPC (Implementado) |
| :--- | :--- | :--- |
| **Vantagens** | Sem dependências externas; controle total dos bytes trafegados; menor overhead em mensagens muito pequenas. | Contrato explícito e tipado (`.proto`); geração automática de stubs; serialização binária segura e independente de linguagem (Protobuf); *framing* TCP e concorrência já resolvidos pelo framework. |
| **Desvantagens** | Protocolo implícito em dicionários/tuplas; necessidade de controlar manualmente delimitação de mensagens (`recv`); `pickle` preso a Python e inseguro; código repetitivo de abertura/fechamento de conexões. | Exige biblioteca externa (`grpcio`) e etapa de geração de código (`protoc`); maior overhead de protocolo (HTTP/2); menos adequado para comunicação em grupo/multicast assíncrono sobre UDP. |

**Conclusão:** o uso de **gRPC** simplificou e tornou mais confiável todo o plano de controle cliente-servidor (registro, descoberta, disparo de rodadas e coleta de logs), enquanto manter **sockets UDP** no multicast entre peers permitiu controle direto sobre confirmações, retransmissões e *hold-back buffer* FIFO. Como esperado, a ordenação FIFO elimina perdas, duplicatas e inversões de um mesmo remetente, mas ainda permite divergências na ordem **global** entre remetentes distintos — questão tratada nas partes seguintes do trabalho.

---

## 4. Como Executar

### Pré-requisitos

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. mpcomm.proto
```

### Execução (local ou em máquinas diferentes)

1. **Inicie o GroupManager:**
```bash
python3 GroupMngr.py --port 5680
```

2. **Inicie os peers** (em máquinas distintas usando as portas padrão, ou na mesma máquina usando portas diferentes):
```bash
# Exemplo em máquinas separadas (substitua IP_SERVIDOR pelo IP do GroupManager/ComparisonServer)
python3 peerCommunicatorUDP.py --gm-addr IP_SERVIDOR:5680 --cs-addr IP_SERVIDOR:5678

# Exemplo com simulação de perda (20%) e atraso variável (até 200 ms)
python3 peerCommunicatorUDP.py --gm-addr IP_SERVIDOR:5680 --cs-addr IP_SERVIDOR:5678 --drop-rate 0.2 --max-delay-ms 200
```

Para testar múltiplos peers na mesma máquina, informe portas distintas em cada terminal:
```bash
python3 peerCommunicatorUDP.py --rpc-port 5700 --udp-port 6789 --drop-rate 0.2 --max-delay-ms 200
python3 peerCommunicatorUDP.py --rpc-port 5701 --udp-port 6790 --drop-rate 0.2 --max-delay-ms 200
python3 peerCommunicatorUDP.py --rpc-port 5702 --udp-port 6791 --drop-rate 0.2 --max-delay-ms 200
```

3. **Inicie o ComparisonServer:**
```bash
python3 comparisonServer.py --port 5678 --gm-addr IP_SERVIDOR:5680
```

Digite o número de mensagens por peer para executar uma rodada e ver o relatório de perdas, duplicatas, ordenação FIFO e ordem global; digite `0` para encerrar os peers e o `GroupManager`.
