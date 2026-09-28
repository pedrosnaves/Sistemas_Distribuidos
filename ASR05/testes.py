"""Testes funcionais e de protocolo, separados das medições de desempenho."""
import socket
import threading
import unittest
from unittest.mock import patch

import cliente
from benchmark import servidor_em_execucao
from cliente import Requisicao, enviar_requisicao, executar, gerar_requisicoes
from protocolo import receber_linha
from servidor import processar_requisicao


class Testes(unittest.TestCase):
    def test_operacoes(self):
        for mensagem, esperado in [("SOMA|10,20", "30"), ("SOMA|-1.5,2", "0.5"),
                                   ("MAIUSCULA|sistemas distribuidos", "SISTEMAS DISTRIBUIDOS"),
                                   ("TAMANHO|hello", "5"), ("MAIUSCULA|ação", "AÇÃO"),
                                   ("TAMANHO|ação", "4"), ("TAMANHO|", "0"),
                                   ("MAIUSCULA|", ""), ("MAIUSCULA|a|b", "A|B")]:
            with self.subTest(mensagem=mensagem):
                self.assertEqual(processar_requisicao(mensagem), esperado)

    def test_entradas_invalidas(self):
        for mensagem in ("", "SOMA", "SOMA|1", "SOMA|1,2,3", "SOMA|a,b", "SOMA|NaN,1", "SOMA|Infinity,1", "OUTRA|x"):
            self.assertTrue(processar_requisicao(mensagem).startswith("ERRO|"))

    def test_linhas_agrupadas(self):
        a, b = socket.socketpair()
        with a, b, b.makefile("rb") as fluxo:
            a.sendall(b"primeira\nsegunda\n")
            self.assertEqual(receber_linha(fluxo), "primeira")
            self.assertEqual(receber_linha(fluxo), "segunda")

    def test_geracao_reprodutivel(self):
        self.assertEqual(gerar_requisicoes(100), gerar_requisicoes(100))
        self.assertEqual({r.mensagem.split("|")[0] for r in gerar_requisicoes(100)}, {"SOMA", "MAIUSCULA", "TAMANHO"})

    def test_rpc_single_e_multi(self):
        exemplos = [Requisicao("SOMA|10,20", "30"),
                    Requisicao("MAIUSCULA|sistemas distribuidos", "SISTEMAS DISTRIBUIDOS"),
                    Requisicao("TAMANHO|hello", "5")]
        for modo in ("single", "multi"):
            with servidor_em_execucao(modo) as endereco:
                for requisicao in exemplos:
                    self.assertIsNone(enviar_requisicao(requisicao, endereco).erro)
                for cliente_modo in ("single", "multi"):
                    for quantidade in (10, 20):
                        resumo, _ = executar(gerar_requisicoes(quantidade), cliente_modo, [endereco], 5)
                        self.assertEqual(resumo["sucessos"], quantidade)
                        self.assertEqual(resumo["respostas"], quantidade)
                        self.assertEqual(resumo["erros"], 0)

    def test_fragmentacao_e_erros_remotos(self):
        with servidor_em_execucao("multi") as endereco:
            with socket.create_connection(endereco, timeout=2) as sock, sock.makefile("rb") as fluxo:
                # Inclusive um caractere UTF-8 dividido entre chamadas sendall.
                for fragmento in (b"MAI", b"USCULA|a\xc3", b"\xa7ao", b"\n"):
                    sock.sendall(fragmento)
                self.assertEqual(receber_linha(fluxo), "AÇAO")
            for dados in (b"SOMA|1,2", b"\xff\n", b"x" * 65537):
                with socket.create_connection(endereco, timeout=2) as sock, sock.makefile("rb") as fluxo:
                    sock.sendall(dados)
                    sock.shutdown(socket.SHUT_WR)
                    self.assertTrue(receber_linha(fluxo).startswith("ERRO|"))
            with socket.create_connection(endereco, timeout=2) as sock, sock.makefile("rb") as fluxo:
                sock.sendall(b"SOMA|a,2\n")
                self.assertTrue(receber_linha(fluxo).startswith("ERRO|"))

    def test_round_robin_e_nova_thread(self):
        with servidor_em_execucao("multi") as primeiro, servidor_em_execucao("multi") as segundo:
            original = cliente.enviar_requisicao
            with patch("cliente.enviar_requisicao", wraps=original) as enviar:
                with patch("cliente.threading.Thread", wraps=threading.Thread) as criar:
                    resumo, _ = executar(gerar_requisicoes(20), "multi", [primeiro, segundo], 5)
                    self.assertEqual(criar.call_count, 20)
                self.assertEqual(resumo["sucessos"], 20)
                destinos = [chamada.args[1] for chamada in enviar.call_args_list]
                self.assertEqual(destinos.count(primeiro), 10)
                self.assertEqual(destinos.count(segundo), 10)

    def test_resposta_invalida_contabilizada(self):
        with servidor_em_execucao("single") as endereco:
            resumo, _ = executar([Requisicao("SOMA|1,2", "999")], "single", [endereco])
            self.assertEqual(resumo["respostas"], 1)
            self.assertEqual(resumo["respostas_invalidas"], 1)
            self.assertEqual(resumo["erros"], 1)
            self.assertFalse(resumo["valido"])

    def test_timeout_e_erro_conexao(self):
        for erro, nome in [(socket.timeout(), "timeout"), (ConnectionRefusedError(), "conexao")]:
            with patch("cliente.socket.create_connection", side_effect=erro):
                resumo, resultados = executar([Requisicao("TAMANHO|x", "1")], "single")
                self.assertEqual(resumo["erros"], 1)
                self.assertEqual(resumo["respostas"], 0)
                self.assertEqual(resultados[0].erro, nome)
                self.assertEqual(resumo["timeouts"], int(nome == "timeout"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
