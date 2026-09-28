Before running, install the middleware and associated tools (on both machines):


## On Amazon Linux
```
sudo dnf install https://download.zeroc.com/ice/3.7/amzn2023/ice-repo-3.7.amzn2023.noarch.rpm
```

```
sudo dnf install python3-ice ice-compilers
```

## On Ubuntu
```
wget "https://download.zeroc.com/ice/3.8/ubuntu26.04/ice-repo-3.8_1.0.0_all.deb" -O ice-repo.deb
sudo dpkg -i ice-repo.deb
rm ice-repo.deb
sudo apt-get update
```
```
sudo apt-get install python3-zeroc-ice
```
```
sudo apt-get install zeroc-ice-compilers
```
Note: This code is exactly as in Example 3.21 of Maarten van Steen's book.

## Novas operações remotas

Este exemplo foi estendido com `soma(int a, int b)`, que retorna a soma
de dois inteiros (dentro do intervalo de `int` do Slice, de 32 bits), e
`maiuscula(string texto)`, que retorna o texto em maiúsculas usando `str.upper()`.
O método original `printString` continua imprimindo no servidor e retornando
o texto com `*` ao cliente. As três operações estão disponíveis nos dois exemplos.

O projeto usa Python e o mapeamento Ice 3.7; a extensão foi testada com
Python e Ice/slice2py 3.7.10. Use runtime e compilador Slice da mesma versão
3.7 (as instruções Ubuntu acima apontam para Ice 3.8).

Na raiz do repositório, gere os proxies e servants com o compilador instalado:

```bash
slice2py Printer.ice
```

Isso atualiza `Printer_ice.py` e `Demo/__init__.py` automaticamente; não edite
esses arquivos manualmente. Não há etapa de compilação C++ neste projeto Python.

Execute em dois terminais, na raiz do repositório:

```bash
# Terminal 1
python3 -B server.py
```

```bash
# Terminal 2
python3 -B client.py
```

Saída esperada do cliente:

```text
Resposta original: Hello World!*
Resultado da soma: 30
Texto em maiusculas: SISTEMAS DISTRIBUIDOS
```

O cliente usa `localhost` por padrão. Para um servidor em outra máquina,
execute `python3 -B client.py ENDERECO_DO_SERVIDOR` (porta TCP 5678).
Encerre o servidor com Ctrl+C após a demonstração.
Para demonstrar dois objetos, execute `server2.py` e `client2.py` no lugar
do par principal, com apenas um servidor ativo por vez. `client2.py` também
aceita o endereço do servidor como argumento e chama as três operações em
cada objeto.
