import sys
import random
import time
import zmq

host = sys.argv[1] if len(sys.argv) > 1 else "0.0.0.0"
contexto = zmq.Context()
socket = contexto.socket(zmq.PUSH)
socket.bind(f"tcp://{host}:5012")
gerador = random.Random(42)
print(f"PUSH em {host}:5012; aguardando trabalhadores", flush=True)
time.sleep(2)
for numero in range(1, 11):
    valor = gerador.randint(1, 100)
    tarefa = {"id": numero, "valor": valor}
    socket.send_json(tarefa)
    print("Enviou:", tarefa, flush=True)
socket.close()
contexto.term()
