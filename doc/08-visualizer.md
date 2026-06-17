# 08 - Visualizador ASCII

**Arquivo:** `roboscript/visualizer.py`

## Responsabilidade

Renderizar o estado atual do `World` em uma grade de caracteres ASCII no terminal,
com animacao via codigos ANSI.

## Constantes ANSI

```python
CLEAR = "\033[2J\033[H"          # Limpa tela e move cursor para (0,0)
HIDE_CURSOR = "\033[?25l"        # Esconde cursor durante animacao
SHOW_CURSOR = "\033[?25h"        # Mostra cursor ao finalizar
```

## Funcao `render(world, animado=True, file=sys.stdout)`

### Passo 1: Constroi a grade

Cria uma matriz de caracteres `(altura x largura)` preenchida com `"."`:

```python
grade = [["." for _ in range(world.largura)] for _ in range(world.altura)]
```

### Passo 2: Desenha elementos na grade

| Simbolo | Elemento | Fonte |
|---------|----------|-------|
| `+` | Trilha (posicoes visitadas) | `world.trilha` |
| `O` | Objeto (pegavel) | `world.objetos` |
| `#` | Obstaculo | `world.obstaculos` |
| `^ > v <` | Robo (conforme orientacao) | `SIMBOLOS_ROBO[direcao]` |

Ordem de desenho (ultimo tem prioridade visual):
1. Trilha
2. Objetos
3. Obstaculos
4. Robo (sempre no topo)

```python
for (tx, ty) in world.trilha:
    if (tx, ty) != (world.x, world.y):  # nao sobrescreve o robo
        grade[ty][tx] = "+"
for (ox, oy) in world.objetos:
    grade[oy][ox] = "O"
for (ox, oy) in world.obstaculos:
    grade[oy][ox] = "#"
grade[world.y][world.x] = SIMBOLOS_ROBO.get(world.direcao, "R")
```

### Passo 3: Renderiza moldura e conteudo

```
+------------------------------+
|..............................|
|....##........................|
|....##......O.................|
|..............................|
|...............^..............|
|..............+...............|
+------------------------------+
Pos: (15,4) | Dir: Norte | Carregando: nao
Sensor (ultima leitura): 6
Acao: mover frente 3 cm
Legenda: ^>v< robo  # obstaculo  O objeto  + trilha  . vazio
```

### Passo 4: Animacao

Se `animado=True`, usa `CLEAR` para limpar e redesenhar no lugar (in-place):

```python
if animado:
    file.write(CLEAR)
file.write(out)
file.flush()
```

## Funcoes de Controle de Animacao

```python
def init_animation(file=sys.stdout):
    """Esconde cursor no inicio da execucao."""
    file.write(HIDE_CURSOR)
    file.flush()

def end_animation(file=sys.stdout):
    """Mostra cursor ao finalizar."""
    file.write(SHOW_CURSOR)
    file.flush()
```

## Painel Informativo

Abaixo da grade, 4 linhas de status:

| Linha | Conteudo | Exemplo |
|-------|----------|---------|
| 1 | Posicao + Direcao + Carga | `Pos: (5,8) | Dir: Norte | Carregando: nao` |
| 2 | Ultima leitura do sensor | `Sensor (ultima leitura): 6` |
| 3 | Ultima acao | `Acao: mover frente 5 cm` |
| 4 | Legenda | `Legenda: ^>v< robo  # obstaculo  O objeto  + trilha  . vazio` |

## Boas Praticas

- **Nao sobrescreve cursor se nao animado** (`--no-anim`): usa `animado=False`
- **In-place animation**: `\033[2J\033[H` limpa e reposiciona o cursor,
  dando efeito fluido sem scroll infinito
- **Compativel com pipe**: se stdout nao for TTY, as constantes ANSI e
  funcionalidades de esconder cursor sao controladas pelo chamador (REPL ou CLI)
- **Thread-safety**: o modulo nao usa estado global; recebe World por parametro

## Locais Importantes no Codigo

- `roboscript/visualizer.py:1` - constantes ANSI
- `roboscript/visualizer.py:10` - funcao `render()`
- `roboscript/visualizer.py:52` - `init_animation()` / `end_animation()`
