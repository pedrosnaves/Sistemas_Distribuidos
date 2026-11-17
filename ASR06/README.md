# ASR06 - Dois novos métodos com Ice

Base: [ice-demo do professor](https://github.com/professorfabio/ice-demo). Mantive `printString` e acrescentei `soma(a, b)` e `maiuscula(texto)` no contrato e no servidor. O cliente demonstra os três métodos.

Nas duas EC2 Ubuntu 26.04, instale o Ice:

```bash
wget https://download.zeroc.com/ice/3.8/ubuntu26.04/ice-repo-3.8_1.0.0_all.deb -O ice-repo.deb
sudo dpkg -i ice-repo.deb
sudo apt-get update
sudo apt-get install -y python3-zeroc-ice
```

Dentro da pasta `ASR06`:

```bash
# Máquina do servidor
python3 servidor.py 0.0.0.0
# Outra máquina
python3 cliente.py IP_SERVIDOR
```

`Ice.loadSlice` carrega `Printer.ice` e gera os tipos em memória. Use a porta TCP 5006 e encerre o servidor com Ctrl+C. A soma usa inteiros de 32 bits, conforme o tipo `int` do Slice.

Teste na AWS em 17/11/2026: servidor na Server-01, cliente na Server-02 e Ice 3.8.3. As respostas foram:

```text
printString: Hello World!*
soma: 30
maiuscula: SISTEMAS DISTRIBUÍDOS
```
