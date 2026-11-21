import argparse
import threading
from concurrent import futures

import grpc

import mpcomm_pb2 as pb
import mpcomm_pb2_grpc as rpc
from constMP import GROUPMNGR_PORT


class GroupManagerServicer(rpc.GroupManagerServicer):
    def __init__(self):
        self.lock = threading.Lock()
        self.peers = []  # Lista de tuplas (ip, rpc_port, udp_port)
        self.stop_event = threading.Event()

    def Register(self, request, context):
        endpoint = (request.ip, request.rpc_port, request.udp_port)
        with self.lock:
            if endpoint not in self.peers:
                self.peers.append(endpoint)
            total = len(self.peers)
        print(f"Peer registrado: {endpoint} (total={total})")
        return pb.Ack(ok=True, message=f"Registrado (total={total})")

    def Unregister(self, request, context):
        endpoint = (request.ip, request.rpc_port, request.udp_port)
        with self.lock:
            if endpoint in self.peers:
                self.peers.remove(endpoint)
        print(f"Peer removido: {endpoint} (total={len(self.peers)})")
        return pb.Ack(ok=True, message="Removido")

    def ListPeers(self, request, context):
        with self.lock:
            lista = [pb.PeerInfo(ip=ip, rpc_port=rp, udp_port=up) for ip, rp, up in self.peers]
        print(f"Lista enviada ({len(lista)} peers)")
        return pb.PeerList(peers=lista)

    def Stop(self, request, context):
        print("Encerramento solicitado.")
        self.stop_event.set()
        return pb.Ack(ok=True, message="Encerrando GroupManager")


def main():
    parser = argparse.ArgumentParser(description="GroupManager (gRPC)")
    parser.add_argument("--port", type=int, default=GROUPMNGR_PORT)
    args = parser.parse_args()

    servicer = GroupManagerServicer()
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
    rpc.add_GroupManagerServicer_to_server(servicer, server)
    server.add_insecure_port(f"0.0.0.0:{args.port}")
    server.start()
    print(f"GroupManager ativo na porta {args.port}")

    try:
        while not servicer.stop_event.wait(timeout=0.5):
            pass
    except KeyboardInterrupt:
        pass
    finally:
        server.stop(grace=1).wait()


if __name__ == "__main__":
    main()
