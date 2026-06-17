"""Testes do parser."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from roboscript.lexer import tokenize
from roboscript.parser import parse
from roboscript import ast_nodes as ast
from roboscript.errors import RoboSyntaxError


def _parse(src):
    return parse(tokenize(src))


class TestParser(unittest.TestCase):
    def test_declaracao_simples(self):
        p = _parse("int x = 5;")
        self.assertIsInstance(p.instrucoes[0], ast.Declaracao)
        self.assertEqual(p.instrucoes[0].tipo, "int")
        self.assertEqual(p.instrucoes[0].nome, "x")

    def test_comando_mover(self):
        p = _parse("mover frente 10 cm;")
        c = p.instrucoes[0]
        self.assertIsInstance(c, ast.ComandoRobo)
        self.assertEqual(c.acao, "mover")
        self.assertEqual(c.direcao, "frente")
        self.assertEqual(c.unidade, "cm")

    def test_condicional_com_senao(self):
        p = _parse("se (x < 10) { parar; } senao { mover frente 1 cm; }")
        self.assertIsInstance(p.instrucoes[0], ast.Se)

    def test_funcao_definicao_e_chamada(self):
        p = _parse(
            "func soma(int a, int b) { retorno a + b; }"
            "int r = soma(1, 2);"
        )
        self.assertIsInstance(p.instrucoes[0], ast.FuncaoDef)
        self.assertEqual(len(p.instrucoes[0].parametros), 2)
        self.assertIsInstance(p.instrucoes[1], ast.Declaracao)

    def test_erro_falta_direcao_em_mover(self):
        with self.assertRaises(RoboSyntaxError) as ctx:
            _parse("mover 10 cm;")
        msg = str(ctx.exception)
        self.assertIn("esperada direcao", msg)
        self.assertIn("frente", msg)
        self.assertIn("'10'", msg)
        self.assertIn("Linha 1", msg)

    def test_precedencia_operadores(self):
        # 1 + 2 * 3 deve gerar BinOp(+, 1, BinOp(*, 2, 3))
        p = _parse("int x = 1 + 2 * 3;")
        valor = p.instrucoes[0].valor
        self.assertIsInstance(valor, ast.BinOp)
        self.assertEqual(valor.op, "+")
        self.assertIsInstance(valor.dir, ast.BinOp)
        self.assertEqual(valor.dir.op, "*")

    def test_repita_vezes(self):
        p = _parse("repita 3 vezes { parar; }")
        self.assertIsInstance(p.instrucoes[0], ast.Repita)


if __name__ == "__main__":
    unittest.main()
