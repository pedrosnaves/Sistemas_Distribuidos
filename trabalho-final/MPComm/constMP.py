import socket

PEER_UDP_PORT = 6789
PEER_RPC_PORT = 5679
SERVER_ADDR = "127.0.0.1"
SERVER_PORT = 5678
GROUPMNGR_ADDR = "127.0.0.1"
GROUPMNGR_PORT = 5680

RETRANSMIT_TIMEOUT = 0.25  # segundos antes de reenviar um pacote UDP sem ACK


def get_local_ip(target_host):
    """Retorna o IP local usado para alcancar target_host."""
    if target_host in ("127.0.0.1", "localhost"):
        return "127.0.0.1"
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect((target_host, 80))
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()
