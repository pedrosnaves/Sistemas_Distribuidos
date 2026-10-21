import sys
import grpc
import servicos_pb2 as pb
import servicos_pb2_grpc as rpc


def executar():
    ip_nomes = sys.argv[1]
    with grpc.insecure_channel(ip_nomes + ":50061") as canal_nomes:
        nomes = rpc.ServicoNomesStub(canal_nomes)

        # Descobre a soma pelo nome e so depois chama o servidor remoto.
        endereco = nomes.Lookup(pb.Nome(nome="soma"), timeout=5).endereco
        with grpc.insecure_channel(endereco) as canal_soma:
            soma = rpc.ServicoSomaStub(canal_soma)
            resposta = soma.Somar(pb.Numeros(a=12, b=3), timeout=5)
            print("12 + 3 =", resposta.valor)

        # O endereco do segundo servico tambem vem do Servico de Nomes.
        endereco = nomes.Lookup(pb.Nome(nome="texto"), timeout=5).endereco
        with grpc.insecure_channel(endereco) as canal_texto:
            texto = rpc.ServicoTextoStub(canal_texto)
            resposta = texto.Maiusculas(pb.Texto(texto="Sistemas Distribuidos"), timeout=5)
            print("Texto em maiusculas:", resposta.texto)

        # Exemplo separado para demonstrar as quatro operacoes de nomes.
        nomes.Bind(pb.Registro(nome="exemplo", endereco="127.0.0.1:6000"), timeout=5)
        print("Bind / Lookup:", nomes.Lookup(pb.Nome(nome="exemplo"), timeout=5).endereco)
        nomes.Rebind(pb.Registro(nome="exemplo", endereco="127.0.0.1:7000"), timeout=5)
        print("Rebind / Lookup:", nomes.Lookup(pb.Nome(nome="exemplo"), timeout=5).endereco)
        nomes.Unbind(pb.Nome(nome="exemplo"), timeout=5)
        print("Unbind: registro exemplo removido")


if __name__ == "__main__":
    executar()
