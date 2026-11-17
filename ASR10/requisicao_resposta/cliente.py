import sys
import zmq

host = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
contexto = zmq.Context()
socket = contexto.socket(zmq.REQ)
socket.setsockopt(zmq.RCVTIMEO, 10000)
socket.setsockopt(zmq.LINGER, 0)
socket.connect(f"tcp://{host}:5010")
for mensagem in ["Hello world", "MAIUSCULA|distribuído", "TAMANHO|olá", "STOP"]:
    socket.send_string(mensagem)
    resposta = socket.recv_string()
    print(mensagem, "->", resposta)
socket.close()
contexto.term()
