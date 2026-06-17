"""Testes funcionais do REPL."""
import io
import os
import re
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from roboscript.repl import RoboREPL
from roboscript.world import World, DIR_LESTE


ANSI_RE = re.compile(r"\x1b\[[0-9;?]*[a-zA-Z]")


def strip_ansi(s: str) -> str:
    return ANSI_RE.sub("", s)


def _run_repl(linhas, world=None):
    """Executa o REPL com entrada simulada e retorna (repl, stdout)."""
    entrada = "\n".join(linhas) + "\n"
    stdin = io.StringIO(entrada)
    stdout = io.StringIO()
    w = world or World(largura=20, altura=10, x=5, y=5)
    repl = RoboREPL(world=w, speed=0, stdin=stdin, stdout=stdout, banner=False)
    repl.run()
    return repl, strip_ansi(stdout.getvalue())


class TestREPL(unittest.TestCase):
    def test_help_e_quit(self):
        repl, out = _run_repl([":help", ":q"])
        self.assertIn("Comandos do RoboScript REPL", out)
        self.assertIn("Ate logo!", out)

    def test_declaracao_sem_ponto_virgula(self):
        repl, out = _run_repl(["int x = 5", ":q"])
        self.assertIn("x", repl.interp.global_env.vars)
        self.assertEqual(repl.interp.global_env.vars["x"], 5)

    def test_expressao_pura_imprime_resultado(self):
        repl, out = _run_repl(["2 + 3", ":q"])
        self.assertIn("=> 5", out)

    def test_comando_mover(self):
        w = World(largura=20, altura=10, x=0, y=5, direcao=DIR_LESTE)
        repl, out = _run_repl(["mover frente 3 cm", ":q"], world=w)
        self.assertEqual(repl.world.x, 3)
        self.assertEqual(repl.world.y, 5)

    def test_vars_meta_comando(self):
        repl, out = _run_repl(["int x = 7", "texto s = \"oi\"", ":vars", ":q"])
        self.assertIn("int x = 7", out)
        self.assertIn("texto s = oi", out)

    def test_funcao_multilinha(self):
        repl, out = _run_repl([
            "func dobro(int n) {",
            "  retorno n * 2;",
            "}",
            "dobro(7)",
            ":q",
        ])
        self.assertIn("=> 14", out)
        self.assertIn("dobro", repl.interp.funcoes)

    def test_erro_nao_derruba_repl(self):
        repl, out = _run_repl([
            "int x = 5",
            "errado_aqui +",
            "x + 1",
            ":q",
        ])
        self.assertIn("Erro sintatico", out)
        self.assertIn("=> 6", out)  # x+1 ainda funciona

    def test_reset_limpa_estado(self):
        repl, out = _run_repl([
            "int x = 99",
            ":reset",
            ":vars",
            ":q",
        ])
        # depois do reset, x nao existe mais
        self.assertNotIn("x", repl.interp.global_env.vars)
        self.assertIn("(nenhuma variavel)", out)

    def test_obstaculo_meta(self):
        repl, out = _run_repl([":obstaculo 7,5", ":q"])
        self.assertIn((7, 5), repl.world.obstaculos)

    def test_teleport(self):
        repl, out = _run_repl([":teleport 10,3", ":q"])
        self.assertEqual((repl.world.x, repl.world.y), (10, 3))

    def test_load_arquivo(self):
        caminho = os.path.join(os.path.dirname(__file__), "..", "examples", "exemplo1.robo")
        repl, out = _run_repl([f":load {caminho}", ":q"])
        # exemplo1 declara velocidade e nome
        self.assertIn("velocidade", repl.interp.global_env.vars)
        self.assertIn("nome", repl.interp.global_env.vars)

    def test_meta_desconhecido(self):
        repl, out = _run_repl([":naoexiste", ":q"])
        self.assertIn("meta-comando desconhecido", out)

    def test_tokens_meta(self):
        repl, out = _run_repl([":tokens mover frente 5 cm", ":q"])
        self.assertIn("PALAVRA_CHAVE", out)
        self.assertIn("NUMERO_INTEIRO", out)

    def test_normalizacao_auto_semicolon(self):
        """'int x = 5' (sem ;) deve funcionar."""
        repl, _ = _run_repl(["int x = 5", "x = x + 10", ":q"])
        self.assertEqual(repl.interp.global_env.vars["x"], 15)


if __name__ == "__main__":
    unittest.main()
