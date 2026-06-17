"""Testes do lexer."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from roboscript.lexer import tokenize
from roboscript.errors import RoboLexError


class TestLexer(unittest.TestCase):
    def test_palavras_reservadas(self):
        toks = tokenize("mover frente 10 cm")
        tipos = [t.tipo for t in toks if t.tipo != "EOF"]
        self.assertEqual(tipos, ["PALAVRA_CHAVE", "PALAVRA_CHAVE",
                                 "NUMERO_INTEIRO", "PALAVRA_CHAVE"])

    def test_identificador_simples(self):
        toks = tokenize("movimento = 5")
        self.assertEqual(toks[0].tipo, "IDENTIFICADOR")
        self.assertEqual(toks[0].lexema, "movimento")

    def test_operadores_relacionais(self):
        toks = tokenize("a == b != c >= d <= e > f < g")
        ops = [t.lexema for t in toks if t.tipo == "OP_RELACIONAL"]
        self.assertEqual(ops, ["==", "!=", ">=", "<=", ">", "<"])

    def test_string_com_escape(self):
        toks = tokenize(r'"linha1\nlinha2"')
        self.assertEqual(toks[0].tipo, "STRING")
        self.assertEqual(toks[0].valor, "linha1\nlinha2")

    def test_comentarios_descartados(self):
        toks = tokenize("# isso eh comentario\nmover")
        self.assertEqual(toks[0].lexema, "mover")

    def test_comentario_bloco(self):
        toks = tokenize("/* bloco\nmulti */ parar")
        self.assertEqual(toks[0].lexema, "parar")

    def test_erro_identificador_iniciando_com_digito(self):
        with self.assertRaises(RoboLexError) as ctx:
            tokenize("int 2robo = 3;")
        self.assertIn("2robo", str(ctx.exception))
        self.assertIn("identificador nao pode comecar com digito", str(ctx.exception))
        self.assertIn("Linha 1", str(ctx.exception))

    def test_numero_decimal(self):
        toks = tokenize("3.14")
        self.assertEqual(toks[0].tipo, "NUMERO_DECIMAL")
        self.assertEqual(toks[0].valor, 3.14)

    def test_delimitadores(self):
        toks = tokenize("( ) { } , ; :")
        for t in toks[:-1]:
            self.assertEqual(t.tipo, "DELIMITADOR")


if __name__ == "__main__":
    unittest.main()
