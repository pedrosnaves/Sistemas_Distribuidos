# Laboratórios - Processos e threads

Reprodução dos exemplos 3.3 e 3.4, conforme o código dos slides 8 e 9 do Capítulo 3 (páginas 10 e 11 do PDF, por causa das sobreposições de slides). Mantive os nomes `eve`, `bob`, as pausas aleatórias de 1 a 20 segundos e os `start()`/`join()`. Completei os imports e usei f-strings e `flush=True` para facilitar a leitura da saída.

Python 3, sem dependências. Execute na EC2:

```bash
python3 processos.py
python3 threads.py
```

Execução na Server-04 em 17/11/2026, com Python 3.14.4 e método de início `forkserver`.

## Exemplo 3.3 - Processos

```text
49:11 eve is going to sleep for 4 seconds
49:11 bob is going to sleep for 11 seconds
49:15 eve has woken up
49:22 bob has woken up
```

## Exemplo 3.4 - Threads dentro de processos

```text
eve sees shared_x being 92
49:24 eve 0 is going to sleep for 17 seconds
49:24 eve 1 is going to sleep for 6 seconds
49:24 eve 2 is going to sleep for 13 seconds
bob sees shared_x being 92
49:24 bob 0 is going to sleep for 12 seconds
49:24 bob 1 is going to sleep for 17 seconds
49:24 bob 2 is going to sleep for 7 seconds
49:30 eve 1 has woken up, seeing shared_x being 93
49:31 bob 2 has woken up, seeing shared_x being 93
49:36 bob 0 has woken up, seeing shared_x being 94
49:37 eve 2 has woken up, seeing shared_x being 94
49:41 eve 0 has woken up, seeing shared_x being 95
eve sees shared_x being 95
49:41 bob 1 has woken up, seeing shared_x being 95
bob sees shared_x being 95
```

| Processo | shared_x inicial | shared_x final |
| --- | ---: | ---: |
| eve | 92 | 95 |
| bob | 92 | 95 |

## Comparação para o campo da tarefa

No primeiro exemplo, `eve` e `bob` são processos independentes. Cada um sorteia um tempo de sono e prossegue sem esperar o outro terminar; o processo principal usa `join()` para esperar ambos. A ordem das mensagens depende dos tempos sorteados e do escalonamento. Como os períodos de sono se sobrepõem, o tempo total não corresponde à soma desses períodos.

No segundo exemplo, continuam existindo dois processos, mas cada um cria três threads. As três threads de `eve` compartilham a variável global daquele processo, enquanto as de `bob` compartilham outra cópia. Por isso, a tabela mostra separadamente o valor inicial e o valor final de cada processo. Uma variável global comum não se torna memória compartilhada entre processos. Os valores iniciais podem ser iguais ou diferentes, dependendo de como os processos são iniciados; coincidirem não significa compartilhar a mesma variável.

As threads compartilham memória dentro de um processo e têm menor isolamento. Os processos têm espaços de endereçamento separados. No exemplo, os incrementos não usam lock: a saída observada não torna seguro generalizar esse acesso para qualquer programa concorrente. A ordem dos despertares e dos prints pode mudar em outra execução. Como a carga é principalmente `sleep`, o experimento ilustra concorrência e compartilhamento de memória, sem demonstrar ganho de paralelismo para cálculos intensivos.
