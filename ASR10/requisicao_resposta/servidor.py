import sys
import zmq

host = sys.argv[1] if len(sys.argv) > 1 else "0.0.0.0"
contexto = zmq.Context()
socket = contexto.socket(zmq.REP)
socket.bind(f"tcp://{host}:5010")
print(f"REP em {host}:5010", flush=True)
while True:
    mensagem = socket.recv_string()
    operacao, _, dados = mensagem.partition("|")
    if operacao == "STOP":
        socket.send_string("Servidor encerrado")
        break
    if operacao == "MAIUSCULA":
        resposta = dados.upper()
    elif operacao == "TAMANHO":
        resposta = str(len(dados))
    else:
        resposta = mensagem + "*"
    socket.send_string(resposta)
socket.close()
contexto.term()
