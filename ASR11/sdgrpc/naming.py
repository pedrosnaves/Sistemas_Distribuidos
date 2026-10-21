"""Registro persistente e seguro para acessos concorrentes dentro do processo."""
import ipaddress
import re
import sqlite3
import threading

import grpc
from sdgrpc import contracts_pb2 as pb
from sdgrpc import contracts_pb2_grpc as rpc


def endpoint(address):
    host = f"[{address.host}]" if ":" in address.host else address.host
    return f"{host}:{address.port}"


class NamingService(rpc.NamingServiceServicer):
    def __init__(self, database=":memory:"):
        self.lock = threading.RLock()
        self.database = sqlite3.connect(str(database), check_same_thread=False)
        self.database.execute("PRAGMA journal_mode=WAL")
        self.database.execute(
            "CREATE TABLE IF NOT EXISTS names (name TEXT PRIMARY KEY, host TEXT NOT NULL, port INTEGER NOT NULL)"
        )
        self.database.commit()

    @staticmethod
    def validate_name(name, context):
        if not re.fullmatch(r"[a-z][a-z0-9._-]{0,63}", name):
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "Nome invalido: use letras minusculas, numeros, ponto, hifen ou sublinhado.")

    def validate_binding(self, request, context):
        self.validate_name(request.name, context)
        address = request.address
        if not 1 <= address.port <= 65535:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "A porta deve estar entre 1 e 65535.")
        try:
            parsed = ipaddress.ip_address(address.host)
        except ValueError:
            if not re.fullmatch(r"(?=.{1,253}$)[a-zA-Z0-9](?:[a-zA-Z0-9.-]*[a-zA-Z0-9])?", address.host):
                context.abort(grpc.StatusCode.INVALID_ARGUMENT, "Host invalido; informe um IP ou nome DNS sem protocolo.")
        else:
            if parsed.is_unspecified or parsed.is_multicast:
                context.abort(grpc.StatusCode.INVALID_ARGUMENT, "Registre um endereco de destino, nao um endereco curinga ou multicast.")

    def Bind(self, request, context):
        self.validate_binding(request, context)
        with self.lock:
            try:
                with self.database:
                    self.database.execute("INSERT INTO names VALUES (?, ?, ?)", (request.name, request.address.host, request.address.port))
            except sqlite3.IntegrityError:
                context.abort(grpc.StatusCode.ALREADY_EXISTS, "Nome ja registrado; use rebind para atualizar.")
        return pb.Status(message="Nome registrado.")

    def Lookup(self, request, context):
        self.validate_name(request.name, context)
        with self.lock:
            row = self.database.execute("SELECT host, port FROM names WHERE name = ?", (request.name,)).fetchone()
        if row is None:
            context.abort(grpc.StatusCode.NOT_FOUND, "Nome nao encontrado.")
        return pb.Address(host=row[0], port=row[1])

    def Unbind(self, request, context):
        self.validate_name(request.name, context)
        with self.lock, self.database:
            cursor = self.database.execute("DELETE FROM names WHERE name = ?", (request.name,))
            if cursor.rowcount == 0:
                context.abort(grpc.StatusCode.NOT_FOUND, "Nome nao encontrado.")
        return pb.Status(message="Registro removido.")

    def Rebind(self, request, context):
        self.validate_binding(request, context)
        with self.lock, self.database:
            self.database.execute(
                "INSERT INTO names VALUES (?, ?, ?) ON CONFLICT(name) DO UPDATE SET host=excluded.host, port=excluded.port",
                (request.name, request.address.host, request.address.port),
            )
        return pb.Status(message="Registro atualizado (ou criado se ainda nao existia).")

    def close(self):
        with self.lock:
            self.database.close()
