#!/usr/bin/env python3
"""CLI principal do RoboScript.

Subcomandos:
  run     <arquivo.robo>   executa o programa com visualizacao animada
  tokens  <arquivo.robo>   imprime a tabela de tokens (Etapa 4 do PDF)
  ast     <arquivo.robo>   imprime a AST em forma de arvore
  check   <arquivo.robo>   apenas valida lexico + sintatico
"""
import argparse
import sys
import os

# permite executar este arquivo direto
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from roboscript.lexer import tokenize
from roboscript.parser import parse
from roboscript.ast_nodes import ast_to_string
from roboscript.interpreter import Interpreter
from roboscript.world import build_world
from roboscript.visualizer import render, init_animation, end_animation
from roboscript.errors import RoboError
from roboscript.repl import run_repl


def _ler_arquivo(caminho: str) -> str:
    with open(caminho, "r", encoding="utf-8") as f:
        return f.read()


def cmd_tokens(args):
    fonte = _ler_arquivo(args.arquivo)
    try:
        toks = tokenize(fonte)
    except RoboError as e:
        print(e, file=sys.stderr)
        sys.exit(1)
    largura_lex = max((len(t.lexema) for t in toks if t.tipo != "EOF"), default=10)
    largura_lex = max(largura_lex, 8)
    print(f"{'Lexema'.ljust(largura_lex)}  Tipo")
    print(f"{'-' * largura_lex}  {'-' * 20}")
    for t in toks:
        if t.tipo == "EOF":
            continue
        print(f"{t.lexema.ljust(largura_lex)}  {t.tipo}")


def cmd_ast(args):
    fonte = _ler_arquivo(args.arquivo)
    try:
        toks = tokenize(fonte)
        prog = parse(toks)
    except RoboError as e:
        print(e, file=sys.stderr)
        sys.exit(1)
    print(ast_to_string(prog), end="")


def cmd_check(args):
    fonte = _ler_arquivo(args.arquivo)
    try:
        toks = tokenize(fonte)
        parse(toks)
    except RoboError as e:
        print(e, file=sys.stderr)
        sys.exit(1)
    print(f"OK: {args.arquivo} - analise lexica e sintatica concluida sem erros.")


def cmd_run(args):
    fonte = _ler_arquivo(args.arquivo)
    try:
        toks = tokenize(fonte)
        prog = parse(toks)
    except RoboError as e:
        print(e, file=sys.stderr)
        sys.exit(1)

    world = build_world(fonte)

    animado = not args.no_anim
    speed = 0.0 if args.no_anim else args.speed

    def on_step(w):
        render(w, animado=animado)

    if animado:
        init_animation()
    try:
        interp = Interpreter(world, on_step=on_step, speed=speed)
        try:
            interp.run(prog)
        except RoboError as e:
            print(e, file=sys.stderr)
            sys.exit(1)
        # render final em modo no-anim (para mostrar estado)
        if args.no_anim:
            render(world, animado=False)
    finally:
        if animado:
            end_animation()

    if interp.output:
        print("\n--- Saida do programa ---")
        for linha in interp.output:
            print(linha)


def main():
    p = argparse.ArgumentParser(
        prog="roboscript",
        description="Executor de programas RoboScript com visualizacao ASCII.",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    pr = sub.add_parser("run", help="executa um programa .robo")
    pr.add_argument("arquivo")
    pr.add_argument("--speed", type=float, default=0.25,
                    help="segundos de delay entre passos (default 0.25)")
    pr.add_argument("--no-anim", action="store_true",
                    help="executa sem animacao; mostra apenas estado final")
    pr.set_defaults(func=cmd_run)

    pt = sub.add_parser("tokens", help="lista tokens (Etapa 4)")
    pt.add_argument("arquivo")
    pt.set_defaults(func=cmd_tokens)

    pa = sub.add_parser("ast", help="imprime a AST")
    pa.add_argument("arquivo")
    pa.set_defaults(func=cmd_ast)

    pc = sub.add_parser("check", help="valida lexico+sintatico")
    pc.add_argument("arquivo")
    pc.set_defaults(func=cmd_check)

    pl = sub.add_parser("repl", help="abre shell interativo (REPL)")
    pl.add_argument("--load", default=None, help="pre-carrega um arquivo .robo")
    pl.add_argument("--speed", type=float, default=0.1,
                    help="delay entre passos da animacao")
    pl.add_argument("--grid", default=None, help="dimensoes WxH (default 30x20)")
    pl.add_argument("--no-banner", action="store_true")
    pl.set_defaults(func=cmd_repl)

    args = p.parse_args()
    args.func(args)


def cmd_repl(args):
    run_repl(load_path=args.load, speed=args.speed,
             grid=args.grid, banner=not args.no_banner)


if __name__ == "__main__":
    main()
