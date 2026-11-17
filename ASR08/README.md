# ASR08 - Python e Java com Ice

O enunciado menciona ASR07. Como essa atividade é uma lista teórica, foi adotada como base a ASR06, que já oferece métodos remotos com Ice. O contrato `Printer.ice` é o mesmo da ASR06; apenas a porta foi alterada para TCP 5008.

Foram implementados os dois cenários:

1. Cliente Python chamando servidor Java.
2. Cliente Java chamando servidor Python.

Cada cliente chama `printString`, `soma` e `maiuscula`, incluindo texto com acento. Ambos os lados usam Ice 3.8.3.

## Preparação

Nas EC2 Ubuntu 26.04, configure o repositório oficial e instale Python/Ice e o JDK:

```bash
wget https://download.zeroc.com/ice/3.8/ubuntu26.04/ice-repo-3.8_1.0.0_all.deb -O ice-repo.deb
sudo dpkg -i ice-repo.deb
sudo apt-get update
sudo apt-get install -y python3-zeroc-ice default-jdk-headless
```

Use [Gradle 9.1.0](https://gradle.org/releases/) ou uma versão compatível com seu JDK. Nas EC2 deste experimento, ele está instalado em `~/asr/gradle-9.1.0`. O `build.gradle` usa o plugin oficial Slice Tools, que obtém o compilador e gera os tipos Java a partir de `Printer.ice`.

Na pasta `ASR08`, compile:

```bash
~/asr/gradle-9.1.0/bin/gradle --no-daemon classes copiarBibliotecas
# Se o Gradle estiver no PATH, use: gradle classes copiarBibliotecas
```

A compilação gera as classes e obtém a biblioteca Ice na pasta `build`, que fica fora da entrega. O Ice para Python é instalado pelo APT.

## Executar em máquinas diferentes

Execute os comandos dentro de `ASR08`. Use o IP privado da máquina que executa o servidor:

```bash
# Cenário 1: uma máquina executa Java
java -cp "build/classes/java/main:build/libs/*" Servidor 0.0.0.0
# Outra máquina executa Python
python3 cliente.py IP_SERVIDOR_JAVA
```

Encerre o servidor Java com Ctrl+C antes de testar o outro cenário na mesma porta.

```bash
# Cenário 2: uma máquina executa Python
python3 servidor.py 0.0.0.0
# Outra máquina executa Java
java -cp "build/classes/java/main:build/libs/*" Cliente IP_SERVIDOR_PYTHON
```

Teste na AWS em 17/11/2026: nos dois cenários, o servidor executou na Server-01 e o cliente na Server-02, com Ice 3.8.3 e Java 25. As respostas foram `Hello World!*`, `30` e `SISTEMAS DISTRIBUÍDOS`.

## Discussão para o campo de texto da tarefa

O middleware permite que um programa Python invoque métodos de um objeto implementado em Java e vice-versa. A interface é descrita em Slice, independente da linguagem. O Ice converte os parâmetros e resultados para uma representação comum, transmite as chamadas e encaminha cada operação ao método correspondente. Assim, o cliente usa um proxy e chama métodos, sem programar diretamente o envio de bytes.

Se fizéssemos isso diretamente sobre TCP, precisaríamos definir e implementar nas duas linguagens o formato das mensagens, a codificação dos textos e números, a delimitação de cada mensagem, a identificação da operação e o tratamento das respostas. O middleware reduz esse trabalho e facilita a interoperabilidade e a manutenção do contrato.

Essa facilidade exige o runtime Ice e versões compatíveis do contrato nos dois lados. A comunicação continua sujeita a latência e falhas de rede: uma chamada remota pode falhar mesmo quando uma chamada local equivalente funcionaria. O middleware simplifica a comunicação, mas não elimina essas diferenças.
