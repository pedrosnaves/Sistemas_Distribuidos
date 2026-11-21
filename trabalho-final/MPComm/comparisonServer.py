import argparse
import threading
from concurrent import futures

import grpc

import mpcomm_pb2 as pb
import mpcomm_pb2_grpc as rpc
from constMP import GROUPMNGR_ADDR, GROUPMNGR_PORT, SERVER_PORT


class ComparisonServicer(rpc.ComparisonServicer):
    def __init__(self):
        self.cond = threading.Condition()
        self.logs = {}  # round_id -> {peer_id: PeerLog}

    def prepare_round(self, round_id):
        with self.cond:
            self.logs[round_id] = {}

    def SubmitLog(self, request, context):
        with self.cond:
            self.logs.setdefault(request.round_id, {})[request.peer_id] = request
            self.cond.notify_all()
        print(f"Log recebido do peer {request.peer_id} ({len(request.messages)} msgs)")
        return pb.Ack(ok=True, message="Log recebido")

    def wait_logs(self, round_id, total_peers):
        with self.cond:
            self.cond.wait_for(lambda: len(self.logs.get(round_id, {})) >= total_peers)
            return dict(self.logs[round_id])


def verificar_resultados(logs, n_msgs):
    peer_ids = sorted(logs.keys())
    n_peers = len(peer_ids)
    esperadas = {(s, seq) for s in range(n_peers) for seq in range(n_msgs)}

    perdidas = 0
    duplicatas = 0
    erros_fifo = 0
    retx = 0
    buf_fifo = 0
    dup_desc = 0

    for pid in peer_ids:
        log = logs[pid]
        entregues = [(m.sender_id, m.seq) for m in log.messages]
        perdidas += len(esperadas - set(entregues))
        duplicatas += len(entregues) - len(set(entregues))

        # Checa ordem FIFO por remetente: 0, 1, 2, ..., n_msgs - 1
        ultimo_seq = {}
        for sender_id, seq in entregues:
            if seq != ultimo_seq.get(sender_id, -1) + 1:
                erros_fifo += 1
            ultimo_seq[sender_id] = seq

        retx += log.retransmissions
        buf_fifo += log.buffered_fifo
        dup_desc += log.duplicates_discarded

    # Comparacao de ordem global entre todos os peers (metrica original corrigida)
    fora_ordem_global = 0
    if n_peers >= 2:
        seqs = [[(m.sender_id, m.seq) for m in logs[pid].messages] for pid in peer_ids]
        for j in range(min(len(s) for s in seqs)):
            if any(seqs[i][j] != seqs[0][j] for i in range(1, n_peers)):
                fora_ordem_global += 1

    print("\n--- Resultado da Rodada ---")
    print(f"Peers: {n_peers} | Msgs/peer: {n_msgs} | Esperado/peer: {n_peers * n_msgs}")
    print(f"Mensagens perdidas         : {perdidas}")
    print(f"Duplicatas entregues       : {duplicatas}")
    print(f"Violacoes de ordem FIFO    : {erros_fifo}")
    print(f"Divergencias ordem global  : {fora_ordem_global} / {n_peers * n_msgs}")
    print(
        f"Stats UDP -> retransmissoes={retx}, retidas_fifo={buf_fifo}, "
        f"duplicatas_descartadas={dup_desc}\n"
    )


def listar_peers(gm_addr):
    with grpc.insecure_channel(gm_addr) as ch:
        return list(rpc.GroupManagerStub(ch).ListPeers(pb.Empty(), timeout=5).peers)


def encerrar_sistema(gm_addr, peers):
    for peer in peers:
        try:
            with grpc.insecure_channel(f"{peer.ip}:{peer.rpc_port}") as ch:
                rpc.PeerControlStub(ch).Shutdown(pb.Empty(), timeout=5)
        except grpc.RpcError:
            pass
    try:
        with grpc.insecure_channel(gm_addr) as ch:
            rpc.GroupManagerStub(ch).Stop(pb.Empty(), timeout=5)
    except grpc.RpcError:
        pass


def main():
    parser = argparse.ArgumentParser(description="ComparisonServer (gRPC)")
    parser.add_argument("--port", type=int, default=SERVER_PORT)
    parser.add_argument("--gm-addr", default=f"{GROUPMNGR_ADDR}:{GROUPMNGR_PORT}")
    args = parser.parse_args()

    servicer = ComparisonServicer()
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
    rpc.add_ComparisonServicer_to_server(servicer, server)
    server.add_insecure_port(f"0.0.0.0:{args.port}")
    server.start()
    print(f"ComparisonServer ativo na porta {args.port}")

    round_id = 0
    try:
        while True:
            n_msgs = int(input("Numero de mensagens por peer (0 para encerrar): "))
            peers = listar_peers(args.gm_addr)

            if n_msgs == 0:
                encerrar_sistema(args.gm_addr, peers)
                break

            if not peers:
                print("Nenhum peer registrado no GroupManager.")
                continue

            round_id += 1
            servicer.prepare_round(round_id)

            for peer_id, peer in enumerate(peers):
                with grpc.insecure_channel(f"{peer.ip}:{peer.rpc_port}") as ch:
                    resp = rpc.PeerControlStub(ch).StartRound(
                        pb.StartRequest(round_id=round_id, peer_id=peer_id, num_msgs=n_msgs),
                        timeout=5,
                    )
                    print(f"Peer {peer_id} ({peer.ip}:{peer.rpc_port}): {resp.message}")

            print("Aguardando logs dos peers...")
            logs = servicer.wait_logs(round_id, len(peers))
            verificar_resultados(logs, n_msgs)
    except (KeyboardInterrupt, EOFError):
        pass
    finally:
        server.stop(grace=1).wait()


if __name__ == "__main__":
    main()
