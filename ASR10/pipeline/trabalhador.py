import sys
import zmq

host = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
nome = sys.argv[2] if len(sys.argv) > 2 else "trabalhador"
contexto = zmq.Context()
socket = contexto.socket(zmq.PULL)
socket.setsockopt(zmq.RCVTIMEO, 10000)
socket.setsockopt(zmq.LINGER, 0)
socket.connect(f"tcp://{host}:5012")
while True:
    try:
        tarefa = socket.recv_json()
    except zmq.Again:
        break
    valor = tarefa["valor"]
    print(f"{nome}: tarefa {tarefa['id']}, {valor} ao quadrado = {valor ** 2}", flush=True)
socket.close()
contexto.term()
