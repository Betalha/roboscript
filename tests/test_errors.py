"""Testa que as mensagens de erro correspondem as do PDF (Etapa 4)."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from roboscript.lexer import tokenize
from roboscript.parser import parse
from roboscript.errors import RoboSyntaxError, RoboLexError


class TestErrorsConformePDF(unittest.TestCase):
    def test_invalido1_mover_sem_direcao(self):
        """Conforme PDF: '[Linha 1] Erro sintatico: esperada direcao
        ('frente', 'tras', 'esquerda' ou 'direita') apos 'mover',
        encontrado '10'.'"""
        with self.assertRaises(RoboSyntaxError) as ctx:
            parse(tokenize("mover 10 cm;"))
        msg = str(ctx.exception)
        self.assertIn("[Linha 1]", msg)
        self.assertIn("Erro sintatico", msg)
        self.assertIn("esperada direcao", msg)
        self.assertIn("'frente'", msg)
        self.assertIn("'tras'", msg)
        self.assertIn("'esquerda'", msg)
        self.assertIn("'direita'", msg)
        self.assertIn("'mover'", msg)
        self.assertIn("'10'", msg)

    def test_invalido2_identificador_iniciado_com_digito(self):
        """Conforme PDF: '[Linha 1] Erro lexico: identificador nao pode
        comecar com digito -- encontrado '2robo'.'"""
        with self.assertRaises(RoboLexError) as ctx:
            tokenize("int 2robo = 3;")
        msg = str(ctx.exception)
        self.assertIn("[Linha 1]", msg)
        self.assertIn("Erro lexico", msg)
        self.assertIn("identificador nao pode comecar com digito", msg)
        self.assertIn("'2robo'", msg)


if __name__ == "__main__":
    unittest.main()
