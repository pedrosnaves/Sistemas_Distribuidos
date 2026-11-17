import sys
import zmq

host = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
topico = sys.argv[2] if len(sys.argv) > 2 else "TIME"
contexto = zmq.Context()
socket = contexto.socket(zmq.SUB)
socket.setsockopt_string(zmq.SUBSCRIBE, topico + " ")
socket.setsockopt(zmq.RCVTIMEO, 10000)
socket.setsockopt(zmq.LINGER, 0)
socket.connect(f"tcp://{host}:5011")
for i in range(5):
    mensagem = socket.recv_string()
    print(mensagem, flush=True)
socket.close()
contexto.term()
