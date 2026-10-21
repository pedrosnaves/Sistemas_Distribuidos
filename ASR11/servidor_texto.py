from concurrent import futures
import sys
import grpc
import servicos_pb2 as pb
import servicos_pb2_grpc as rpc


class ServicoTexto(rpc.ServicoTextoServicer):
    def Maiusculas(self, pedido, contexto):
        return pb.Texto(texto=pedido.texto.upper())


def iniciar():
    ip_nomes = sys.argv[1]
    meu_ip = sys.argv[2]
    servidor = grpc.server(futures.ThreadPoolExecutor(max_workers=1))
    rpc.add_ServicoTextoServicer_to_server(ServicoTexto(), servidor)
    servidor.add_insecure_port("0.0.0.0:50063")

    with grpc.insecure_channel(ip_nomes + ":50061") as canal:
        nomes = rpc.ServicoNomesStub(canal)
        nomes.Bind(pb.Registro(nome="texto", endereco=meu_ip + ":50063"), timeout=5)

    servidor.start()
    print("Servico de Texto registrado na porta 50063")
    servidor.wait_for_termination()


if __name__ == "__main__":
    iniciar()
