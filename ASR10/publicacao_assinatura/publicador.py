import sys
import time
import zmq

host = sys.argv[1] if len(sys.argv) > 1 else "0.0.0.0"
contexto = zmq.Context()
socket = contexto.socket(zmq.PUB)
socket.bind(f"tcp://{host}:5011")
print(f"PUB em {host}:5011", flush=True)
try:
    while True:
        socket.send_string("TIME " + time.asctime())
        socket.send_string("TEMP 25 C")
        time.sleep(1)
except KeyboardInterrupt:
    pass
finally:
    socket.close()
    contexto.term()
