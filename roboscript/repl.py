"""REPL interativo do RoboScript."""
import os
import sys
import time
from typing import Optional, List

from .lexer import tokenize, PALAVRAS_RESERVADAS
from .parser import Parser, parse_uma, parse_expressao
from .interpreter import Interpreter
from .world import World, build_world, parse_diretivas, NOMES_DIR
from .visualizer import render, init_animation, end_animation, CLEAR
from .errors import RoboError
from . import ast_nodes as ast


RED = "\033[31m"
YEL = "\033[33m"
CYA = "\033[36m"
GRN = "\033[32m"
DIM = "\033[2m"
RST = "\033[0m"
BOLD = "\033[1m"


META_COMMANDS = [
    ":help", ":h",
    ":vars", ":v",
    ":funcs", ":f",
    ":reset",
    ":world",
    ":obstaculo", ":objeto", ":rm",
    ":teleport",
    ":speed",
    ":load",
    ":tokens", ":ast",
    ":redraw", ":r",
    ":clear",
    ":mode",
    ":quit", ":q", ":exit",
]


HELP_TEXT = """\
Comandos do RoboScript REPL:

  Instrucoes da linguagem:
    int x = 5            declara variavel (o ';' eh opcional no REPL)
    x = x + 1            atribuicao
    mover frente 3 cm    movimenta o robo
    girar direita 90 graus
    parar; pegar; soltar
    se (x > 0) { ... }   blocos multi-linha sao detectados automaticamente
    func nome(int a) { retorno a * 2; }
    imprimir(x, "ola")
    ler(distancia)

  Expressoes nuas (avaliadas e impressas):
    2 + 3
    velocidade * 2
    minhafunc(10)

  Meta-comandos (prefixo ':'):
    :help, :h               mostra esta ajuda
    :vars, :v               lista variaveis e tipos
    :funcs, :f              lista funcoes definidas
    :world                  mostra estado do mundo
    :reset                  reinicia mundo, variaveis e funcoes
    :obstaculo X,Y          adiciona obstaculo
    :objeto X,Y             adiciona objeto pegavel
    :rm X,Y                 remove obstaculo/objeto da celula
    :teleport X,Y           move robo para (X,Y)
    :speed N                ajusta delay da animacao (segundos)
    :load arquivo.robo      carrega e executa arquivo
    :tokens <codigo>        mostra tokens sem executar
    :ast <codigo>           mostra AST sem executar
    :redraw, :r             redesenha a grade
    :clear                  limpa terminal
    :mode tela|log          alterna entre tela cheia e log
    :quit, :q               sai do REPL (Ctrl+D tambem funciona)
"""


def _supports_readline() -> bool:
    try:
        import readline  # noqa
        return True
    except ImportError:
        return False


class RoboREPL:
    def __init__(self, world: Optional[World] = None, speed: float = 0.1,
                 stdin=None, stdout=None, banner: bool = True,
                 modo_tela: bool = True):
        self.world = world or World()
        self.speed = speed
        self.interp = Interpreter(self.world, on_step=None, speed=0)
        self.stdin = stdin or sys.stdin
        self.stdout = stdout or sys.stdout
        self.banner = banner
        self.modo_tela = modo_tela
        self.rodando = True
        self.ultimo_resultado: Optional[str] = None
        self.ultimo_erro: Optional[str] = None
        self._interactive = (
            self.stdin is sys.stdin
            and self.stdout is sys.stdout
            and sys.stdin.isatty()
            and sys.stdout.isatty()
        )
        if not self._interactive:
            self.modo_tela = False
        self._histfile = os.path.expanduser("~/.roboscript_history")

    # ---------- ENTRY ----------
    def run(self):
        if self._interactive and _supports_readline():
            self._setup_readline()
        if self.modo_tela and self._interactive:
            init_animation(self.stdout)
        try:
            if self.banner:
                self._render()
                self._print_banner()
            while self.rodando:
                try:
                    src = self._ler_entrada_completa()
                except EOFError:
                    self._println("")
                    break
                except KeyboardInterrupt:
                    self._println("^C")
                    continue
                if src is None or src.strip() == "":
                    continue
                self._processar(src)
                if not self.rodando:
                    break
                if self.modo_tela and self._interactive:
                    self._render()
                else:
                    self._render_log()
        finally:
            if self.modo_tela and self._interactive:
                end_animation(self.stdout)
            if self._interactive and _supports_readline():
                self._save_history()

    # ---------- LEITURA ----------
    def _ler_entrada_completa(self) -> Optional[str]:
        """Le uma instrucao, possivelmente multi-linha (ate fechar todas as '{')."""
        linhas: List[str] = []
        prompt1 = f"{BOLD}{GRN}robo>{RST} " if self._interactive else "robo> "
        prompt2 = f"{DIM}....>{RST} " if self._interactive else "....> "
        while True:
            prompt = prompt1 if not linhas else prompt2
            if self._interactive:
                linha = input(prompt)
            else:
                self.stdout.write(prompt)
                self.stdout.flush()
                linha = self.stdin.readline()
                if linha == "":
                    raise EOFError()
                linha = linha.rstrip("\n")
            linhas.append(linha)
            total = "\n".join(linhas)
            # meta-comando: nao precisa de bloco
            if total.lstrip().startswith(":"):
                return total
            # se nao ha '{' nao fechado, retorna
            if self._blocos_completos(total):
                return total

    def _blocos_completos(self, src: str) -> bool:
        """Conta '{' vs '}' ignorando comentarios e strings."""
        abertos = 0
        i = 0
        n = len(src)
        in_string = False
        while i < n:
            c = src[i]
            if in_string:
                if c == "\\" and i + 1 < n:
                    i += 2
                    continue
                if c == '"':
                    in_string = False
                i += 1
                continue
            if c == '"':
                in_string = True
                i += 1
                continue
            if c == "#":
                while i < n and src[i] != "\n":
                    i += 1
                continue
            if c == "/" and i + 1 < n and src[i + 1] == "*":
                i += 2
                while i + 1 < n and not (src[i] == "*" and src[i + 1] == "/"):
                    i += 1
                i += 2
                continue
            if c == "{":
                abertos += 1
            elif c == "}":
                abertos -= 1
            i += 1
        return abertos <= 0

    # ---------- PROCESSAR ----------
    def _processar(self, src: str):
        self.ultimo_resultado = None
        self.ultimo_erro = None
        src_strip = src.strip()
        if src_strip.startswith(":"):
            self._meta(src_strip)
            return
        # 1) tenta como expressao pura (sem ';' e sem '{')
        if not src_strip.endswith(";") and "{" not in src_strip:
            try:
                toks = tokenize(src)
                expr = parse_expressao(toks)
                v = self.interp.eval_uma(expr)
                if v is not None:
                    self.ultimo_resultado = self.interp.fmt(v)
                return
            except RoboError:
                pass  # nao era expressao -> tenta como instrucao
        # 2) executa como sequencia de instrucoes
        src_norm = self._normalizar(src)
        try:
            toks = tokenize(src_norm)
            parser = Parser(toks)
            while not parser.at_end():
                ins = parser.parse_uma_instrucao()
                if ins is None:
                    break
                self.interp.exec_uma(ins)
        except RoboError as e:
            self.ultimo_erro = str(e)
        except Exception as e:
            self.ultimo_erro = f"erro interno: {type(e).__name__}: {e}"

    def _normalizar(self, src: str) -> str:
        """Adiciona ';' final se o usuario nao colocou e a entrada nao termina
        em ';' ou '}' (que ja sao terminadores validos)."""
        s = src.rstrip()
        if not s:
            return src
        # se ja termina em ; ou }, deixa como esta
        if s.endswith(";") or s.endswith("}"):
            return s
        # se contem multiplas linhas e ja ha ; ao final de alguma, mantem
        # caso simples: anexa ;
        return s + ";"

    # ---------- META-COMANDOS ----------
    def _meta(self, linha: str):
        partes = linha.split(maxsplit=1)
        cmd = partes[0]
        arg = partes[1] if len(partes) > 1 else ""
        if cmd in (":quit", ":q", ":exit"):
            self.rodando = False
            self._println(f"{CYA}Ate logo!{RST}")
            return
        if cmd in (":help", ":h"):
            self._println(HELP_TEXT)
            return
        if cmd in (":vars", ":v"):
            self._mostrar_vars()
            return
        if cmd in (":funcs", ":f"):
            self._mostrar_funcs()
            return
        if cmd == ":world":
            self._mostrar_world()
            return
        if cmd == ":reset":
            self.world = World(largura=self.world.largura, altura=self.world.altura)
            self.interp = Interpreter(self.world, on_step=None, speed=0)
            self.ultimo_resultado = "(estado reiniciado)"
            return
        if cmd == ":obstaculo":
            self._add_obj(arg, kind="obstaculo")
            return
        if cmd == ":objeto":
            self._add_obj(arg, kind="objeto")
            return
        if cmd == ":rm":
            self._rm_obj(arg)
            return
        if cmd == ":teleport":
            self._teleport(arg)
            return
        if cmd == ":speed":
            try:
                self.speed = float(arg)
                self.ultimo_resultado = f"speed = {self.speed}"
            except ValueError:
                self.ultimo_erro = f"valor invalido para :speed: {arg!r}"
            return
        if cmd == ":load":
            self._load(arg)
            return
        if cmd == ":tokens":
            self._mostrar_tokens(arg)
            return
        if cmd == ":ast":
            self._mostrar_ast(arg)
            return
        if cmd in (":redraw", ":r"):
            return  # render acontece no loop
        if cmd == ":clear":
            self.stdout.write(CLEAR)
            self.stdout.flush()
            return
        if cmd == ":mode":
            if arg.strip() == "tela":
                self.modo_tela = True
            elif arg.strip() == "log":
                self.modo_tela = False
            else:
                self.ultimo_erro = "uso: :mode tela|log"
            return
        self.ultimo_erro = f"meta-comando desconhecido: {cmd}"

    def _mostrar_vars(self):
        env = self.interp.global_env
        if not env.vars:
            self._println(f"{DIM}(nenhuma variavel){RST}")
            return
        for nome, valor in env.vars.items():
            tipo = env.types.get(nome, "?")
            self._println(f"  {tipo} {nome} = {self.interp.fmt(valor)}")

    def _mostrar_funcs(self):
        if not self.interp.funcoes:
            self._println(f"{DIM}(nenhuma funcao){RST}")
            return
        for nome, fdef in self.interp.funcoes.items():
            params = ", ".join(f"{t} {n}" for t, n in fdef.parametros)
            self._println(f"  func {nome}({params})")

    def _mostrar_world(self):
        w = self.world
        self._println(f"  Grade: {w.largura}x{w.altura}")
        self._println(f"  Robo:  ({w.x},{w.y}) virado para {NOMES_DIR.get(w.direcao, w.direcao)}")
        self._println(f"  Carregando: {'sim' if w.carregando else 'nao'}")
        self._println(f"  Obstaculos ({len(w.obstaculos)}): {sorted(w.obstaculos)}")
        self._println(f"  Objetos ({len(w.objetos)}): {sorted(w.objetos)}")

    def _add_obj(self, arg, kind):
        try:
            x, y = [int(p.strip()) for p in arg.split(",")]
        except (ValueError, TypeError):
            self.ultimo_erro = f"uso: :{kind} X,Y"
            return
        if not (0 <= x < self.world.largura and 0 <= y < self.world.altura):
            self.ultimo_erro = f"coordenada fora da grade"
            return
        if kind == "obstaculo":
            self.world.obstaculos.add((x, y))
        else:
            self.world.objetos.add((x, y))
        self.ultimo_resultado = f"{kind} em ({x},{y}) adicionado"

    def _rm_obj(self, arg):
        try:
            x, y = [int(p.strip()) for p in arg.split(",")]
        except (ValueError, TypeError):
            self.ultimo_erro = "uso: :rm X,Y"
            return
        self.world.obstaculos.discard((x, y))
        self.world.objetos.discard((x, y))
        self.ultimo_resultado = f"celula ({x},{y}) limpa"

    def _teleport(self, arg):
        try:
            x, y = [int(p.strip()) for p in arg.split(",")]
        except (ValueError, TypeError):
            self.ultimo_erro = "uso: :teleport X,Y"
            return
        if not (0 <= x < self.world.largura and 0 <= y < self.world.altura):
            self.ultimo_erro = "coordenada fora da grade"
            return
        self.world.x = x
        self.world.y = y
        self.world.trilha.append((x, y))
        self.world.ultima_acao = f"teleport para ({x},{y})"

    def _load(self, caminho):
        caminho = caminho.strip()
        if not caminho:
            self.ultimo_erro = "uso: :load arquivo.robo"
            return
        if not os.path.exists(caminho):
            self.ultimo_erro = f"arquivo nao encontrado: {caminho}"
            return
        try:
            with open(caminho, encoding="utf-8") as f:
                fonte = f.read()
        except OSError as e:
            self.ultimo_erro = f"erro ao ler arquivo: {e}"
            return
        # aplica diretivas de mundo (apenas as ainda nao aplicadas)
        cfg = parse_diretivas(fonte)
        if cfg["obstaculos"]:
            for o in cfg["obstaculos"]:
                self.world.obstaculos.add(o)
        if cfg["objetos"]:
            for o in cfg["objetos"]:
                self.world.objetos.add(o)
        # executa o codigo
        try:
            toks = tokenize(fonte)
            parser = Parser(toks)
            while not parser.at_end():
                ins = parser.parse_uma_instrucao()
                if ins is None:
                    break
                self.interp.exec_uma(ins)
            self.ultimo_resultado = f"carregado: {caminho}"
        except RoboError as e:
            self.ultimo_erro = str(e)

    def _mostrar_tokens(self, src):
        if not src.strip():
            self.ultimo_erro = "uso: :tokens <codigo>"
            return
        try:
            toks = tokenize(src)
        except RoboError as e:
            self.ultimo_erro = str(e)
            return
        for t in toks:
            if t.tipo == "EOF":
                continue
            self._println(f"  {t.lexema!r:<20}  {t.tipo}")

    def _mostrar_ast(self, src):
        if not src.strip():
            self.ultimo_erro = "uso: :ast <codigo>"
            return
        src_norm = self._normalizar(src)
        try:
            toks = tokenize(src_norm)
            parser = Parser(toks)
            saidas = []
            while not parser.at_end():
                ins = parser.parse_uma_instrucao()
                if ins is None:
                    break
                saidas.append(ast.ast_to_string(ins))
            self._println("".join(saidas), end="")
        except RoboError as e:
            self.ultimo_erro = str(e)

    # ---------- RENDER ----------
    def _render(self):
        if not self.modo_tela:
            self._render_log()
            return
        # tela cheia
        render(self.world, animado=True, file=self.stdout)
        # painel
        env = self.interp.global_env
        vars_str = ", ".join(f"{n}={self.interp.fmt(v)}" for n, v in env.vars.items()) or "(vazio)"
        funcs_str = ", ".join(self.interp.funcoes.keys()) or "(vazio)"
        self._println(f"{CYA}Vars:{RST}  {vars_str}")
        self._println(f"{CYA}Funcs:{RST} {funcs_str}")
        out_recente = self.interp.output[-4:] if self.interp.output else []
        if out_recente:
            self._println(f"{CYA}Saida (ultimas):{RST}")
            for s in out_recente:
                self._println(f"  > {s}")
        if self.ultimo_resultado is not None:
            self._println(f"{GRN}=> {self.ultimo_resultado}{RST}")
        if self.ultimo_erro is not None:
            self._println(f"{RED}{self.ultimo_erro}{RST}")

    def _render_log(self):
        if self.ultimo_resultado is not None:
            self._println(f"{GRN}=> {self.ultimo_resultado}{RST}")
        if self.ultimo_erro is not None:
            self._println(f"{RED}{self.ultimo_erro}{RST}")

    def _print_banner(self):
        self._println(f"{BOLD}{CYA}RoboScript REPL v1.0{RST} - "
                      f"digite {YEL}:help{RST} para ajuda, {YEL}:q{RST} para sair")

    def _println(self, s="", end="\n"):
        self.stdout.write(s + end)
        self.stdout.flush()

    # ---------- READLINE ----------
    def _setup_readline(self):
        import readline
        try:
            readline.read_history_file(self._histfile)
        except (OSError, FileNotFoundError):
            pass
        readline.set_history_length(1000)
        readline.parse_and_bind("tab: complete")
        readline.set_completer(self._completer)
        readline.set_completer_delims(" \t\n(),;{}")

    def _save_history(self):
        try:
            import readline
            readline.write_history_file(self._histfile)
        except Exception:
            pass

    def _completer(self, texto, estado):
        candidatos = sorted(set(
            list(PALAVRAS_RESERVADAS)
            + ["and", "or", "not"]
            + list(self.interp.global_env.vars.keys())
            + list(self.interp.funcoes.keys())
            + META_COMMANDS
        ))
        matches = [c for c in candidatos if c.startswith(texto)]
        if estado < len(matches):
            return matches[estado]
        return None


def run_repl(load_path: Optional[str] = None, speed: float = 0.1,
             grid: Optional[str] = None, banner: bool = True):
    largura, altura = 30, 20
    if grid:
        try:
            largura, altura = [int(x) for x in grid.lower().split("x")]
        except (ValueError, AttributeError):
            print(f"--grid invalido: {grid!r} (esperado WxH, ex: 30x20)", file=sys.stderr)
            sys.exit(2)
    world = World(largura=largura, altura=altura)
    repl = RoboREPL(world=world, speed=speed, banner=banner)
    if load_path:
        repl._load(load_path)
    repl.run()
