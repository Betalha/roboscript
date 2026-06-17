"""Visualizador ASCII do mundo do robo, com animacao via ANSI."""
import sys
from .world import World, NOMES_DIR, SIMBOLOS_ROBO


CLEAR = "\033[2J\033[H"
HIDE_CURSOR = "\033[?25l"
SHOW_CURSOR = "\033[?25h"


def render(world: World, animado: bool = True, file=sys.stdout):
    grade = [["." for _ in range(world.largura)] for _ in range(world.altura)]
    # trilha
    for (tx, ty) in world.trilha:
        if (tx, ty) != (world.x, world.y):
            if 0 <= tx < world.largura and 0 <= ty < world.altura:
                grade[ty][tx] = "+"
    # objetos
    for (ox, oy) in world.objetos:
        if 0 <= ox < world.largura and 0 <= oy < world.altura:
            grade[oy][ox] = "O"
    # obstaculos
    for (ox, oy) in world.obstaculos:
        if 0 <= ox < world.largura and 0 <= oy < world.altura:
            grade[oy][ox] = "#"
    # robo
    grade[world.y][world.x] = SIMBOLOS_ROBO.get(world.direcao, "R")

    linhas = []
    linhas.append("+" + "-" * world.largura + "+")
    for row in grade:
        linhas.append("|" + "".join(row) + "|")
    linhas.append("+" + "-" * world.largura + "+")

    carga = "sim" if world.carregando else "nao"
    dir_nome = NOMES_DIR.get(world.direcao, str(world.direcao))
    linhas.append(f"Pos: ({world.x},{world.y}) | Dir: {dir_nome} | Carregando: {carga}")
    leitura = "-" if world.ultima_leitura is None else str(world.ultima_leitura)
    linhas.append(f"Sensor (ultima leitura): {leitura}")
    linhas.append(f"Acao: {world.ultima_acao}")
    linhas.append("Legenda: ^>v< robo  # obstaculo  O objeto  + trilha  . vazio")

    out = "\n".join(linhas) + "\n"
    if animado:
        file.write(CLEAR)
    file.write(out)
    file.flush()


def init_animation(file=sys.stdout):
    file.write(HIDE_CURSOR)
    file.flush()


def end_animation(file=sys.stdout):
    file.write(SHOW_CURSOR)
    file.flush()
