# ASR10 - Três padrões com ZeroMQ

Base: exemplos do ZIP `code-Chap04-Python3(2).zip` e os três padrões apresentados nos slides do Capítulo 4. O ZIP rotula os diretórios como `04-22`, `04-23` e `04-24`; o enunciado/slides usa as figuras 4.21 a 4.23. Foram implementados os três padrões para contemplar esse deslocamento de numeração.

Prepare cada máquina:

```bash
# Nas EC2 Ubuntu, se venv ainda não estiver instalado:
sudo apt-get install -y python3-venv
python3 -m venv .venv
. .venv/bin/activate
pip install pyzmq==27.1.0
```

Os comandos abaixo partem da pasta `ASR10`, com esse ambiente ativado. Substitua `IP_SERVIDOR` pelo endereço privado da máquina que executa o servidor, publicador ou produtor.

## Requisição e resposta (REQ/REP)

Acrescentei conversão para maiúsculas e contagem de caracteres ao eco original. O servidor também responde ao `STOP` antes de encerrar, mantendo a alternância entre receber e responder do padrão REP.

```bash
# Servidor em uma máquina
python3 requisicao_resposta/servidor.py 0.0.0.0
# Cliente em outra; demonstra as operações e encerra o servidor
python3 requisicao_resposta/cliente.py IP_SERVIDOR
```

Porta TCP 5010.

## Publicação e assinatura (PUB/SUB)

Acrescentei o tópico `TEMP` (temperatura fixa de exemplo) e a escolha do tópico pelo assinante. Cada assinante recebe cinco mensagens do tópico escolhido.

```bash
python3 publicacao_assinatura/publicador.py 0.0.0.0
# Em outra máquina, execute um ou ambos os assinantes:
python3 publicacao_assinatura/assinante.py IP_SERVIDOR TIME
python3 publicacao_assinatura/assinante.py IP_SERVIDOR TEMP
```

Porta TCP 5011. O publicador continua até Ctrl+C. Mensagens anteriores à assinatura podem se perder: PUB/SUB não guarda histórico para novos assinantes.

## Pipeline (PUSH/PULL)

No exemplo original, o trabalhador apenas dormia. Acrescentei processamento real: calcular o quadrado do número recebido e identificar a tarefa. O produtor gera dez tarefas com seed 42. Pode haver dois trabalhadores em máquinas diferentes, compartilhando a carga.

```bash
# Inicie os dois trabalhadores antes do produtor, em máquinas diferentes:
python3 pipeline/trabalhador.py IP_SERVIDOR worker-1
python3 pipeline/trabalhador.py IP_SERVIDOR worker-2
# Máquina do produtor:
python3 pipeline/produtor.py 0.0.0.0
```

Porta TCP 5012. Cada tarefa vai para um trabalhador conectado. Os trabalhadores encerram após dez segundos sem novas tarefas e imprimem seus resultados.

## Teste na AWS

Em 17/11/2026, o REQ/REP e o publicador executaram na Server-01. O cliente REQ e o assinante TIME executaram na Server-02; o assinante TEMP, na Server-03. Foram obtidas as quatro respostas esperadas no REQ/REP e cinco mensagens do tópico escolhido por assinante.

No pipeline, a Server-01 produziu dez tarefas. Os trabalhadores nas Server-03 e Server-04 processaram cinco tarefas cada, com os quadrados corretos e sem repetir ou perder tarefas.
