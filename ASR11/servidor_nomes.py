from concurrent import futures
import grpc
import servicos_pb2 as pb
import servicos_pb2_grpc as rpc


class ServicoNomes(rpc.ServicoNomesServicer):
    def __init__(self):
        self.registros = {}  # Dicionario: nome do servico -> IP:porta

    def Bind(self, pedido, contexto):
        if pedido.nome in self.registros:
            contexto.abort(grpc.StatusCode.ALREADY_EXISTS, "Nome ja registrado")
        self.registros[pedido.nome] = pedido.endereco
        return pb.Vazio()

    def Lookup(self, pedido, contexto):
        if pedido.nome not in self.registros:
            contexto.abort(grpc.StatusCode.NOT_FOUND, "Nome nao encontrado")
        return pb.Endereco(endereco=self.registros[pedido.nome])

    def Unbind(self, pedido, contexto):
        if pedido.nome not in self.registros:
            contexto.abort(grpc.StatusCode.NOT_FOUND, "Nome nao encontrado")
        del self.registros[pedido.nome]
        return pb.Vazio()

    def Rebind(self, pedido, contexto):
        self.registros[pedido.nome] = pedido.endereco
        return pb.Vazio()


def iniciar():
    # Um pedido por vez simplifica o acesso ao dicionario.
    servidor = grpc.server(futures.ThreadPoolExecutor(max_workers=1))
    rpc.add_ServicoNomesServicer_to_server(ServicoNomes(), servidor)
    servidor.add_insecure_port("0.0.0.0:50061")
    servidor.start()
    print("Servico de Nomes na porta 50061")
    servidor.wait_for_termination()


if __name__ == "__main__":
    iniciar()
