import argparse
import json
import random
import socket
import threading
import time
from concurrent import futures

import grpc

import mpcomm_pb2 as pb
import mpcomm_pb2_grpc as rpc
from constMP import (
    GROUPMNGR_ADDR,
    GROUPMNGR_PORT,
    PEER_RPC_PORT,
    PEER_UDP_PORT,
    RETRANSMIT_TIMEOUT,
    SERVER_ADDR,
    SERVER_PORT,
    get_local_ip,
)


class ReliableFifoPeer:
    """Controle cliente-servidor via gRPC (Parte 1a) + Multicast UDP confiavel/FIFO (Parte 1b)."""

    def __init__(self, args):
        self.gm_addr = args.gm_addr
        self.cs_addr = args.cs_addr
        gm_host = self.gm_addr.split(":")[0]
        self.host = args.host or get_local_ip(gm_host)
        self.rpc_port = args.rpc_port
        self.udp_port = args.udp_port
        self.drop_rate = args.drop_rate
        self.max_delay_ms = args.max_delay_ms

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(("0.0.0.0", self.udp_port))
        self.sock.settimeout(0.1)

        self.lock = threading.Lock()
        self.stop_event = threading.Event()
        self.round = None
        self.past_rounds = {}  # round_id -> (my_id, peers) para responder ACKs atrasados

        threading.Thread(target=self._recv_loop, daemon=True).start()
        threading.Thread(target=self._retransmit_loop, daemon=True).start()

    def _send_udp(self, packet, addr):
        """Envia pacote UDP com perda e atraso simulados opcionais."""
        if self.drop_rate > 0 and random.random() < self.drop_rate:
            return
        raw = json.dumps(packet).encode("utf-8")
        if self.max_delay_ms > 0:
            delay = random.uniform(0, self.max_delay_ms) / 1000.0
            threading.Timer(delay, self._raw_sendto, args=(raw, addr)).start()
        else:
            self._raw_sendto(raw, addr)

    def _raw_sendto(self, raw, addr):
        try:
            self.sock.sendto(raw, addr)
        except OSError:
            pass

    def _recv_loop(self):
        while not self.stop_event.is_set():
            try:
                raw, _ = self.sock.recvfrom(65535)
            except socket.timeout:
                continue
            except OSError:
                break
            self._handle_packet(json.loads(raw.decode("utf-8")))

    def _retransmit_loop(self):
        while not self.stop_event.wait(timeout=0.05):
            to_resend = []
            now = time.monotonic()
            with self.lock:
                r = self.round
                if not r:
                    continue
                for seq, pending in list(r["pending_acks"].items()):
                    pkt = r["sent_packets"][seq]
                    for pid, last_sent in list(pending.items()):
                        if now - last_sent >= RETRANSMIT_TIMEOUT:
                            pending[pid] = now
                            r["retransmissions"] += 1
                            to_resend.append((pkt, r["peers"][pid]))
            for pkt, addr in to_resend:
                self._send_udp(pkt, addr)

    def _handle_packet(self, pkt):
        to_send = []
        ptype = pkt["type"]
        rid = pkt["round_id"]

        with self.lock:
            r = self.round
            # Responde ACK para pacotes atrasados de rodadas anteriores (evita deadlock no DONE)
            if r is None or rid != r["round_id"]:
                if rid in self.past_rounds and ptype in ("DATA", "DONE"):
                    old_id, old_peers = self.past_rounds[rid]
                    sid = pkt["sender_id"]
                    ack = {
                        "type": "ACK",
                        "round_id": rid,
                        "ack_from": old_id,
                        "sender_id": sid,
                        "seq": pkt["seq"],
                    }
                    to_send.append((ack, old_peers[sid]))
            elif ptype == "READY":
                sid = pkt["sender_id"]
                to_send.append(
                    ({"type": "READY_ACK", "round_id": rid, "ack_from": r["my_id"]}, r["peers"][sid])
                )
            elif ptype == "READY_ACK":
                r["ready_acks"].add(pkt["ack_from"])
                if len(r["ready_acks"]) == len(r["peers"]):
                    r["handshake_done"].set()
            elif ptype == "ACK" and pkt["sender_id"] == r["my_id"]:
                seq = pkt["seq"]
                if seq in r["pending_acks"]:
                    r["pending_acks"][seq].pop(pkt["ack_from"], None)
                    if not r["pending_acks"][seq]:
                        del r["pending_acks"][seq]
                if r["done_sent"] and not r["pending_acks"]:
                    r["all_acked"].set()
            elif ptype in ("DATA", "DONE"):
                sid = pkt["sender_id"]
                seq = pkt["seq"]
                ack = {
                    "type": "ACK",
                    "round_id": rid,
                    "ack_from": r["my_id"],
                    "sender_id": sid,
                    "seq": seq,
                }
                to_send.append((ack, r["peers"][sid]))

                expected = r["expected_seq"][sid]
                if seq < expected:
                    r["duplicates_discarded"] += 1
                elif seq > expected:
                    if seq not in r["holdback"][sid]:
                        r["holdback"][sid][seq] = pkt
                        r["buffered_fifo"] += 1
                else:
                    # Entrega em ordem FIFO estrita, drenando o hold-back buffer
                    r["holdback"][sid][seq] = pkt
                    while r["expected_seq"][sid] in r["holdback"][sid]:
                        cur = r["holdback"][sid].pop(r["expected_seq"][sid])
                        r["expected_seq"][sid] += 1
                        if cur["type"] == "DONE":
                            r["done_senders"].add(sid)
                            if len(r["done_senders"]) == len(r["peers"]):
                                r["all_done"].set()
                        else:
                            r["delivered"].append((sid, cur["seq"]))
                            print(f"Entregue FIFO: msg {cur['seq']} do peer {sid}")

        for pkt_out, addr in to_send:
            self._send_udp(pkt_out, addr)

    def _multicast(self, ptype, seq):
        with self.lock:
            r = self.round
            pkt = {"type": ptype, "round_id": r["round_id"], "sender_id": r["my_id"], "seq": seq}
            now = time.monotonic()
            r["sent_packets"][seq] = pkt
            r["pending_acks"][seq] = {pid: now for pid in range(len(r["peers"]))}
            if ptype == "DONE":
                r["done_sent"] = True
            targets = list(r["peers"])
        for addr in targets:
            self._send_udp(pkt, addr)

    def run_round(self, round_id, peer_id, num_msgs):
        # 1. Busca lista atual de peers no GroupManager via gRPC
        with grpc.insecure_channel(self.gm_addr) as ch:
            resp = rpc.GroupManagerStub(ch).ListPeers(pb.Empty(), timeout=5)
            peers = [(p.ip, p.udp_port) for p in resp.peers]

        n_peers = len(peers)
        with self.lock:
            self.round = {
                "round_id": round_id,
                "my_id": peer_id,
                "peers": peers,
                "ready_acks": set(),
                "handshake_done": threading.Event(),
                "sent_packets": {},
                "pending_acks": {},
                "done_sent": False,
                "all_acked": threading.Event(),
                "expected_seq": {i: 0 for i in range(n_peers)},
                "holdback": {i: {} for i in range(n_peers)},
                "done_senders": set(),
                "all_done": threading.Event(),
                "delivered": [],
                "retransmissions": 0,
                "buffered_fifo": 0,
                "duplicates_discarded": 0,
            }
            self.past_rounds[round_id] = (peer_id, peers)
            r = self.round

        # 2. Handshake confiavel (READY / READY_ACK)
        while not r["handshake_done"].is_set() and not self.stop_event.is_set():
            with self.lock:
                faltantes = [i for i in range(n_peers) if i not in r["ready_acks"]]
            for i in faltantes:
                self._send_udp({"type": "READY", "round_id": round_id, "sender_id": peer_id}, peers[i])
            r["handshake_done"].wait(timeout=0.15)

        print(f"Peer {peer_id}: handshake concluido com {n_peers} peers.")

        # 3. Envio multicast de mensagens DATA + marcador DONE sequenciado no fluxo FIFO
        for seq in range(num_msgs):
            time.sleep(random.uniform(0.01, 0.08))
            self._multicast("DATA", seq)
        self._multicast("DONE", num_msgs)

        # 4. Aguarda entrega do DONE de todos e ACK de tudo que enviou
        r["all_done"].wait()
        r["all_acked"].wait()

        # 5. Salva log local e envia ao ComparisonServer via gRPC
        with open(f"logfile{peer_id}.log", "w", encoding="utf-8") as f:
            f.write(str(r["delivered"]))

        log_msg = pb.PeerLog(
            round_id=round_id,
            peer_id=peer_id,
            messages=[pb.MessageRecord(sender_id=s, seq=seq) for s, seq in r["delivered"]],
            retransmissions=r["retransmissions"],
            buffered_fifo=r["buffered_fifo"],
            duplicates_discarded=r["duplicates_discarded"],
        )
        with grpc.insecure_channel(self.cs_addr) as ch:
            rpc.ComparisonStub(ch).SubmitLog(log_msg, timeout=10)
        print(f"Peer {peer_id}: rodada {round_id} concluida e log enviado.")

    def register(self):
        with grpc.insecure_channel(self.gm_addr) as ch:
            resp = rpc.GroupManagerStub(ch).Register(
                pb.PeerInfo(ip=self.host, rpc_port=self.rpc_port, udp_port=self.udp_port),
                timeout=5,
            )
            print(f"Registrado no GroupManager: {resp.message}")

    def unregister(self):
        try:
            with grpc.insecure_channel(self.gm_addr) as ch:
                rpc.GroupManagerStub(ch).Unregister(
                    pb.PeerInfo(ip=self.host, rpc_port=self.rpc_port, udp_port=self.udp_port),
                    timeout=3,
                )
        except grpc.RpcError:
            pass

    def close(self):
        self.stop_event.set()
        self.unregister()
        self.sock.close()


class PeerControlServicer(rpc.PeerControlServicer):
    def __init__(self, peer):
        self.peer = peer

    def StartRound(self, request, context):
        threading.Thread(
            target=self.peer.run_round,
            args=(request.round_id, request.peer_id, request.num_msgs),
            daemon=True,
        ).start()
        return pb.Ack(ok=True, message=f"Rodada {request.round_id} iniciada")

    def Shutdown(self, request, context):
        print("Shutdown recebido.")
        self.peer.stop_event.set()
        return pb.Ack(ok=True, message="Encerrando peer")


def main():
    parser = argparse.ArgumentParser(description="Peer MPComm (gRPC + UDP Confiavel/FIFO)")
    parser.add_argument("--gm-addr", default=f"{GROUPMNGR_ADDR}:{GROUPMNGR_PORT}")
    parser.add_argument("--cs-addr", default=f"{SERVER_ADDR}:{SERVER_PORT}")
    parser.add_argument("--host", default=None, help="IP anunciado ao GroupManager")
    parser.add_argument("--rpc-port", type=int, default=PEER_RPC_PORT)
    parser.add_argument("--udp-port", type=int, default=PEER_UDP_PORT)
    parser.add_argument("--drop-rate", type=float, default=0.0, help="Taxa simulada de perda [0..1)")
    parser.add_argument("--max-delay-ms", type=int, default=0, help="Atraso maximo simulado em ms")
    args = parser.parse_args()

    peer = ReliableFifoPeer(args)
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
    rpc.add_PeerControlServicer_to_server(PeerControlServicer(peer), server)
    server.add_insecure_port(f"0.0.0.0:{args.rpc_port}")
    server.start()

    peer.register()
    print(f"Peer ativo em {peer.host} (gRPC:{peer.rpc_port}, UDP:{peer.udp_port})")

    try:
        while not peer.stop_event.wait(timeout=0.5):
            pass
    except KeyboardInterrupt:
        pass
    finally:
        peer.close()
        server.stop(grace=1).wait()


if __name__ == "__main__":
    main()
