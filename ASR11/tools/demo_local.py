"""Demonstra quatro processos reais no computador local e encerra os servidores."""
import json
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time

import grpc

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from sdgrpc import contracts_pb2 as pb
from sdgrpc import contracts_pb2_grpc as rpc


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def main():
    processes = []
    stop_paths = []
    with tempfile.TemporaryDirectory() as temporary:
        logs = []
        ready = {}
        try:
            ports = {role: free_port() for role in ("names", "calculator", "text")}
            naming = f"127.0.0.1:{ports['names']}"
            for role in ports:
                ready_path = Path(temporary) / f"{role}.json"
                stop_path = Path(temporary) / f"{role}.stop"
                command = [sys.executable, "-m", "sdgrpc.server", role, "--port", str(ports[role]), "--ready-file", str(ready_path), "--stop-file", str(stop_path)]
                if role == "names":
                    command += ["--database", str(Path(temporary) / "names.sqlite3")]
                else:
                    command += ["--naming", naming]
                log = open(Path(temporary) / f"{role}.log", "w+", encoding="utf-8")
                logs.append(log)
                process = subprocess.Popen(command, cwd=ROOT, stdout=log, stderr=log)
                processes.append(process)
                stop_paths.append(stop_path)
                with grpc.insecure_channel(f"127.0.0.1:{ports[role]}") as channel:
                    grpc.channel_ready_future(channel).result(timeout=15)
                deadline = time.monotonic() + 15
                while not ready_path.exists():
                    if process.poll() is not None or time.monotonic() > deadline:
                        raise RuntimeError(f"Servidor {role} nao ficou pronto")
                    time.sleep(0.1)
                ready[role] = json.loads(ready_path.read_text(encoding="utf-8"))
            deadline = time.monotonic() + 15
            with grpc.insecure_channel(naming) as channel:
                stub = rpc.NamingServiceStub(channel)
                for name in ("calculadora", "texto"):
                    while True:
                        try:
                            stub.Lookup(pb.Name(name=name), timeout=2)
                            break
                        except grpc.RpcError:
                            if time.monotonic() > deadline:
                                raise
                            time.sleep(0.1)
            output = subprocess.check_output([sys.executable, "-m", "sdgrpc.client", "--naming", naming, "demo"], cwd=ROOT, text=True, encoding="utf-8")
            result = json.loads(output)
            assert result["calculator"]["result"] == 15
            assert result["text"]["words"] == 4
            assert result["calculator"]["process_id"] == ready['calculator']['process_id']
            assert result["text"]["process_id"] == ready['text']['process_id']
            assert len({r['process_id'] for r in ready.values()} | {result['client']['process_id']}) == 4
            result["naming_process_id"] = ready['names']['process_id']
            print(json.dumps(result, ensure_ascii=False, indent=2))
        finally:
            for process, stop_path in reversed(list(zip(processes, stop_paths))):
                stop_path.touch()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
            for log in logs:
                log.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
