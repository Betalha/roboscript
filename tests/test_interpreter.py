"""Testes do interpretador."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from roboscript.lexer import tokenize
from roboscript.parser import parse
from roboscript.interpreter import Interpreter
from roboscript.world import build_world, DIR_NORTE, DIR_LESTE


def _run(src):
    prog = parse(tokenize(src))
    world = build_world(src)
    interp = Interpreter(world, on_step=None, speed=0)
    interp.run(prog)
    return interp, world


class TestInterpreter(unittest.TestCase):
    def test_imprimir_simples(self):
        interp, _ = _run('imprimir("ola");')
        self.assertEqual(interp.output, ["ola"])

    def test_mover_atualiza_posicao(self):
        src = (
            "# @mundo 20x10\n"
            "# @inicio 10,5\n"
            "# @direcao leste\n"
            "mover frente 3 cm;\n"
        )
        _, w = _run(src)
        self.assertEqual((w.x, w.y), (13, 5))
        self.assertEqual(w.direcao, DIR_LESTE)

    def test_girar(self):
        src = (
            "# @mundo 20x10\n"
            "# @inicio 5,5\n"
            "# @direcao norte\n"
            "girar direita 90 graus;\n"
        )
        _, w = _run(src)
        self.assertEqual(w.direcao, DIR_LESTE)

    def test_repita(self):
        src = (
            "# @mundo 20x10\n"
            "# @inicio 0,5\n"
            "# @direcao leste\n"
            "repita 4 vezes { mover frente 1 cm; }\n"
        )
        _, w = _run(src)
        self.assertEqual(w.x, 4)

    def test_funcao_retorno(self):
        src = (
            "func dobro(int n) { retorno n * 2; }\n"
            'int r = dobro(7);\n'
            'imprimir(r);\n'
        )
        interp, _ = _run(src)
        self.assertEqual(interp.output, ["14"])

    def test_se_senao(self):
        src = (
            "int x = 10;\n"
            "se (x > 5) { imprimir(\"maior\"); } senao { imprimir(\"menor\"); }\n"
        )
        interp, _ = _run(src)
        self.assertEqual(interp.output, ["maior"])

    def test_obstaculo_bloqueia_movimento(self):
        src = (
            "# @mundo 10x10\n"
            "# @inicio 0,5\n"
            "# @direcao leste\n"
            "# @obstaculo 3,5\n"
            "mover frente 10 cm;\n"
        )
        _, w = _run(src)
        # robo deve parar em x=2 (cel antes do obstaculo em x=3)
        self.assertEqual(w.x, 2)

    def test_sensor_distancia(self):
        src = (
            "# @mundo 10x10\n"
            "# @inicio 0,5\n"
            "# @direcao leste\n"
            "# @obstaculo 4,5\n"
            "int d = 0;\n"
            "ler(d);\n"
            "imprimir(d);\n"
        )
        interp, _ = _run(src)
        # distancia ate obstaculo em x=4, robo em x=0: 3 celulas livres
        self.assertEqual(interp.output, ["3"])

    def test_pegar_objeto(self):
        src = (
            "# @mundo 10x10\n"
            "# @inicio 5,5\n"
            "# @objeto 5,5\n"
            "pegar;\n"
        )
        _, w = _run(src)
        self.assertTrue(w.carregando)

    def test_exemplos_pdf_executam_sem_erro(self):
        base = os.path.join(os.path.dirname(__file__), "..", "examples")
        for nome in ("exemplo1.robo", "exemplo2.robo", "exemplo3.robo"):
            with open(os.path.join(base, nome)) as f:
                src = f.read()
            _run(src)  # nao deve lancar


if __name__ == "__main__":
    unittest.main()
