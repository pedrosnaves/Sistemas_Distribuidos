import sys
from statistics import mean
from cliente import executar

host = sys.argv[1]
quantidade = int(sys.argv[2]) if len(sys.argv) > 2 else 2000
if quantidade < 1:
    raise SystemExit("Informe uma quantidade positiva")

cenarios = [("A", "single", 5005), ("B", "single", 5007), ("C", "multi", 5007)]
tempos = {"A": [], "B": [], "C": []}
for repeticao in range(3):
    ordem = cenarios[repeticao:] + cenarios[:repeticao]
    for nome, modo, porta in ordem:
        resultado = executar(host, porta, modo, quantidade)
        if resultado["erros"]:
            raise RuntimeError(f"Ensaio com erros: {resultado}")
        tempos[nome].append(resultado["segundos"])
        print(f"{nome}, repeticao {repeticao + 1}: {resultado['segundos']:.6f} s, "
              f"{resultado['corretas']} corretas", flush=True)

for nome, valores in tempos.items():
    print(f"{nome}: media de {mean(valores):.6f} s")
