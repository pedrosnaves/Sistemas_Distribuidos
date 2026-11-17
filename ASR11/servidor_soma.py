from concurrent import futures
import sys
import grpc
import servicos_pb2 as pb
import servicos_pb2_grpc as rpc


class ServicoSoma(rpc.ServicoSomaServicer):
    def Somar(self, pedido, contexto):
        return pb.Resultado(valor=pedido.a + pedido.b)


def iniciar():
    ip_nomes = sys.argv[1]
    meu_ip = sys.argv[2]
    servidor = grpc.server(futures.ThreadPoolExecutor(max_workers=1))
    rpc.add_ServicoSomaServicer_to_server(ServicoSoma(), servidor)
    servidor.add_insecure_port("0.0.0.0:50062")

    # O proprio servidor registra o endereco que o cliente devera descobrir.
    with grpc.insecure_channel(ip_nomes + ":50061") as canal:
        nomes = rpc.ServicoNomesStub(canal)
        nomes.Bind(pb.Registro(nome="soma", endereco=meu_ip + ":50062"), timeout=5)

    servidor.start()
    print("Servico de Soma registrado na porta 50062")
    servidor.wait_for_termination()


if __name__ == "__main__":
    iniciar()
