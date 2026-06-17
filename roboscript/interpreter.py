"""Interpretador tree-walking do RoboScript."""
import time
from typing import Any, Callable, Dict, List, Optional

from . import ast_nodes as ast
from .errors import RoboRuntimeError, RoboTypeError
from .world import World


class Environment:
    def __init__(self, parent: Optional["Environment"] = None):
        self.vars: Dict[str, Any] = {}
        self.types: Dict[str, str] = {}
        self.parent = parent

    def declare(self, nome: str, tipo: str, valor: Any, linha: int):
        if nome in self.vars:
            raise RoboRuntimeError(linha, f"variavel '{nome}' ja declarada neste escopo")
        self.vars[nome] = valor
        self.types[nome] = tipo

    def assign(self, nome: str, valor: Any, linha: int):
        env = self._find(nome)
        if env is None:
            raise RoboRuntimeError(linha, f"variavel '{nome}' nao declarada")
        env.vars[nome] = valor

    def get(self, nome: str, linha: int) -> Any:
        env = self._find(nome)
        if env is None:
            raise RoboRuntimeError(linha, f"variavel '{nome}' nao declarada")
        return env.vars[nome]

    def _find(self, nome: str) -> Optional["Environment"]:
        if nome in self.vars:
            return self
        if self.parent:
            return self.parent._find(nome)
        return None


class _ReturnSignal(Exception):
    def __init__(self, valor):
        self.valor = valor


class Interpreter:
    def __init__(self, world: World, on_step: Optional[Callable[[World], None]] = None,
                 speed: float = 0.2):
        self.world = world
        self.global_env = Environment()
        self.funcoes: Dict[str, ast.FuncaoDef] = {}
        self.on_step = on_step
        self.speed = speed
        self.output: List[str] = []

    # ---- API publica ----
    def run(self, programa: ast.Programa):
        # primeira passada: registra funcoes
        for ins in programa.instrucoes:
            if isinstance(ins, ast.FuncaoDef):
                self.funcoes[ins.nome] = ins
        # render inicial
        self._step("(inicio)")
        # executa instrucoes (pulando defs)
        for ins in programa.instrucoes:
            if isinstance(ins, ast.FuncaoDef):
                continue
            self._exec(ins, self.global_env)

    # ---- helpers ----
    def _step(self, acao: str, leitura: Optional[int] = None):
        self.world.ultima_acao = acao
        if leitura is not None:
            self.world.ultima_leitura = leitura
        self.world.log.append(acao)
        if self.on_step:
            self.on_step(self.world)
            if self.speed > 0:
                time.sleep(self.speed)

    def _truthy(self, v) -> bool:
        if isinstance(v, bool):
            return v
        if isinstance(v, (int, float)):
            return v != 0
        if isinstance(v, str):
            return len(v) > 0
        return bool(v)

    def _check_tipo(self, tipo_decl: str, valor: Any, linha: int):
        if valor is None:
            return
        if tipo_decl == "int" and not isinstance(valor, int) or (isinstance(valor, bool) and tipo_decl == "int"):
            # nota: bool e int em Python; tratamos bool separado
            if isinstance(valor, bool):
                raise RoboTypeError(linha, f"esperado int, recebido bool")
            if not isinstance(valor, int):
                raise RoboTypeError(linha, f"esperado int, recebido {type(valor).__name__}")
        if tipo_decl == "float":
            if not isinstance(valor, (int, float)) or isinstance(valor, bool):
                raise RoboTypeError(linha, f"esperado float, recebido {type(valor).__name__}")
        if tipo_decl == "texto" and not isinstance(valor, str):
            raise RoboTypeError(linha, f"esperado texto, recebido {type(valor).__name__}")
        if tipo_decl == "bool" and not isinstance(valor, bool):
            raise RoboTypeError(linha, f"esperado bool, recebido {type(valor).__name__}")

    # ---- exec instrucao ----
    def _exec(self, node, env: Environment):
        m = getattr(self, f"_exec_{type(node).__name__}", None)
        if m is None:
            raise RoboRuntimeError(getattr(node, "linha", 0),
                                   f"nao sei executar {type(node).__name__}")
        return m(node, env)

    def _exec_Declaracao(self, node: ast.Declaracao, env: Environment):
        valor = None
        if node.valor is not None:
            valor = self._eval(node.valor, env)
            self._check_tipo(node.tipo, valor, node.linha)
        else:
            valor = {"int": 0, "float": 0.0, "texto": "", "bool": False}[node.tipo]
        env.declare(node.nome, node.tipo, valor, node.linha)

    def _exec_Atribuicao(self, node: ast.Atribuicao, env: Environment):
        valor = self._eval(node.valor, env)
        env.assign(node.nome, valor, node.linha)

    def _exec_ComandoRobo(self, node: ast.ComandoRobo, env: Environment):
        if node.acao == "mover":
            qtd = self._eval(node.expressao, env)
            if not isinstance(qtd, (int, float)) or isinstance(qtd, bool):
                raise RoboRuntimeError(node.linha, "quantidade em 'mover' deve ser numerica")
            qtd = int(qtd)
            andados = self.world.mover(node.direcao, qtd)
            obs = "" if andados == qtd else f" (parou em obstaculo/borda, andou {andados})"
            self._step(f"mover {node.direcao} {qtd} cm{obs}")
            return
        if node.acao == "girar":
            qtd = self._eval(node.expressao, env)
            if not isinstance(qtd, (int, float)) or isinstance(qtd, bool):
                raise RoboRuntimeError(node.linha, "graus em 'girar' deve ser numerico")
            qtd = int(qtd)
            self.world.girar(node.direcao, qtd)
            self._step(f"girar {node.direcao} {qtd} graus")
            return
        if node.acao == "parar":
            self._step("parar")
            return
        if node.acao == "pegar":
            ok = self.world.pegar()
            self._step("pegar" + ("" if ok else " (nada aqui)"))
            return
        if node.acao == "soltar":
            ok = self.world.soltar()
            self._step("soltar" + ("" if ok else " (nada para soltar)"))
            return
        if node.acao == "esperar":
            qtd = self._eval(node.expressao, env)
            self._step(f"esperar {qtd}")
            if self.speed > 0:
                time.sleep(min(float(qtd) * 0.1, 2.0))
            return

    def _exec_Se(self, node: ast.Se, env: Environment):
        cond = self._eval(node.condicao, env)
        if self._truthy(cond):
            for ins in node.bloco_entao:
                self._exec(ins, env)
        elif node.bloco_senao:
            for ins in node.bloco_senao:
                self._exec(ins, env)

    def _exec_Enquanto(self, node: ast.Enquanto, env: Environment):
        max_iter = 100000
        i = 0
        while self._truthy(self._eval(node.condicao, env)):
            for ins in node.bloco:
                self._exec(ins, env)
            i += 1
            if i > max_iter:
                raise RoboRuntimeError(node.linha, "loop 'enquanto' excedeu limite de iteracoes")

    def _exec_Repita(self, node: ast.Repita, env: Environment):
        n = self._eval(node.vezes, env)
        if not isinstance(n, (int, float)) or isinstance(n, bool):
            raise RoboRuntimeError(node.linha, "'repita' espera valor numerico")
        for _ in range(int(n)):
            for ins in node.bloco:
                self._exec(ins, env)

    def _exec_FuncaoDef(self, node, env):
        # ja registrada na primeira passada
        self.funcoes[node.nome] = node

    def _exec_Imprimir(self, node: ast.Imprimir, env: Environment):
        partes = [self._fmt(self._eval(e, env)) for e in node.expressoes]
        linha = " ".join(partes)
        self.output.append(linha)
        self._step(f"imprimir: {linha}")

    def _exec_Ler(self, node: ast.Ler, env: Environment):
        # sensor automatico: distancia ate proximo obstaculo na direcao atual
        d = self.world.sensor_distancia()
        env.assign(node.nome, d, node.linha)
        self._step(f"ler({node.nome}) = sensor distancia", leitura=d)

    def _exec_Retorno(self, node: ast.Retorno, env: Environment):
        v = self._eval(node.valor, env)
        raise _ReturnSignal(v)

    def _exec_FuncaoChamada(self, node: ast.FuncaoChamada, env: Environment):
        # chamada como statement: ignora retorno
        self._eval(node, env)

    # ---- eval expressao ----
    def _eval(self, node, env: Environment):
        m = getattr(self, f"_eval_{type(node).__name__}", None)
        if m is None:
            raise RoboRuntimeError(getattr(node, "linha", 0),
                                   f"nao sei avaliar {type(node).__name__}")
        return m(node, env)

    def _eval_Literal(self, node: ast.Literal, env): return node.valor

    def _eval_Identificador(self, node: ast.Identificador, env):
        return env.get(node.nome, node.linha)

    def _eval_BinOp(self, node: ast.BinOp, env):
        op = node.op
        # short-circuit
        if op == "and":
            a = self._eval(node.esq, env)
            if not self._truthy(a):
                return False
            return self._truthy(self._eval(node.dir, env))
        if op == "or":
            a = self._eval(node.esq, env)
            if self._truthy(a):
                return True
            return self._truthy(self._eval(node.dir, env))
        a = self._eval(node.esq, env)
        b = self._eval(node.dir, env)
        if op == "+":
            if isinstance(a, str) or isinstance(b, str):
                return self._fmt(a) + self._fmt(b)
            return a + b
        if op == "-": return a - b
        if op == "*": return a * b
        if op == "/":
            if b == 0:
                raise RoboRuntimeError(node.linha, "divisao por zero")
            if isinstance(a, int) and isinstance(b, int):
                return a // b if (a % b == 0) else a / b
            return a / b
        if op == "==": return a == b
        if op == "!=": return a != b
        if op == ">":  return a > b
        if op == "<":  return a < b
        if op == ">=": return a >= b
        if op == "<=": return a <= b
        raise RoboRuntimeError(node.linha, f"operador desconhecido {op}")

    def _eval_UnOp(self, node: ast.UnOp, env):
        v = self._eval(node.operando, env)
        if node.op == "-":
            return -v
        if node.op == "not":
            return not self._truthy(v)
        raise RoboRuntimeError(node.linha, f"operador unario desconhecido {node.op}")

    def _eval_FuncaoChamada(self, node: ast.FuncaoChamada, env):
        if node.nome not in self.funcoes:
            raise RoboRuntimeError(node.linha, f"funcao '{node.nome}' nao definida")
        fdef = self.funcoes[node.nome]
        if len(node.args) != len(fdef.parametros):
            raise RoboRuntimeError(
                node.linha,
                f"funcao '{node.nome}' espera {len(fdef.parametros)} argumentos, "
                f"recebidos {len(node.args)}"
            )
        novo = Environment(parent=self.global_env)
        for (tipo, nome), arg_node in zip(fdef.parametros, node.args):
            val = self._eval(arg_node, env)
            self._check_tipo(tipo, val, node.linha)
            novo.declare(nome, tipo, val, node.linha)
        try:
            for ins in fdef.bloco:
                self._exec(ins, novo)
        except _ReturnSignal as r:
            return r.valor
        return None

    # ---- API publica para o REPL ----
    def exec_uma(self, node):
        """Executa uma instrucao ja parseada no escopo global do interpretador."""
        if isinstance(node, ast.FuncaoDef):
            self.funcoes[node.nome] = node
            return
        self._exec(node, self.global_env)

    def eval_uma(self, node):
        """Avalia uma expressao ja parseada no escopo global e retorna o valor."""
        return self._eval(node, self.global_env)

    def registrar_funcao(self, fdef: "ast.FuncaoDef"):
        self.funcoes[fdef.nome] = fdef

    def fmt(self, v) -> str:
        return self._fmt(v)

    def _fmt(self, v) -> str:
        if isinstance(v, bool):
            return "verdade" if v else "falso"
        if v is None:
            return "(nulo)"
        return str(v)
