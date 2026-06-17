# 07 - Mundo Simulado

**Arquivo:** `roboscript/world.py`

## Responsabilidade

Modelar o estado fisico do mundo onde o robo opera: posicao, orientacao,
obstaculos, objetos, e a logica do sensor de distancia.

## API Publica

```python
from roboscript.world import World, build_world, parse_diretivas

# Criacao direta
world = World(largura=30, altura=20, x=15, y=10)

# Criacao a partir de codigo-fonte (lendo diretivas)
world = build_world(codigo_fonte)

# Criacao com override de parametros
world = build_world(codigo_fonte, override={"largura": 40, "altura": 15})
```

## A classe `World`

```python
@dataclass
class World:
    largura: int = 30          # numero de colunas
    altura: int = 20           # numero de linhas
    x: int = 15                # posicao x do robo (coluna)
    y: int = 10                # posicao y do robo (linha)
    direcao: int = 0           # 0=Norte, 90=Leste, 180=Sul, 270=Oeste
    carregando: bool = False   # robo esta carregando um objeto?
    obstaculos: set = ...      # conjunto de (x, y) ocupados
    objetos: set = ...         # conjunto de (x, y) com objetos
    trilha: list = ...         # historico de posicoes do robo
    ultima_acao: str = "(inicio)"
    ultima_leitura: int | None = None
    log: list = ...            # historico de acoes
```

**Coordenadas:**
- `x` cresce para a direita (coluna)
- `y` cresce para baixo (linha)
- Origem `(0, 0)` no canto superior esquerdo
- Isso coincide com como a grade ASCII eh renderizada

## Orientacao

| Constante | Graus | Simbolo | Nome |
|-----------|-------|---------|------|
| `DIR_NORTE` | 0 | `^` | Norte |
| `DIR_LESTE` | 90 | `>` | Leste |
| `DIR_SUL` | 180 | `v` | Sul |
| `DIR_OESTE` | 270 | `<` | Oeste |

```python
SIMBOLOS_ROBO = {0: "^", 90: ">", 180: "v", 270: "<"}
NOMES_DIR = {0: "Norte", 90: "Leste", 180: "Sul", 270: "Oeste"}
```

### `direcao_apos_movimento(palavra)`

Calcula a direcao efetiva de um movimento dado a orientacao atual. Exemplo:
- Robo virado para Norte, `mover frente` -> delta(0, -1) (cima)
- Robo virado para Norte, `mover direita` -> delta(1, 0) (direita)
- Robo virado para Norte, `mover tras` -> delta(0, 1) (baixo)

### `girar(palavra, graus)`

Ajusta `self.direcao` em graus:

```python
if palavra == "direita":   self.direcao = (self.direcao + graus) % 360
if palavra == "esquerda":  self.direcao = (self.direcao - graus) % 360
self.direcao = round(self.direcao / 90) * 90 % 360  # normaliza
```

### `mover(palavra, qtd) -> int`

Tenta mover `qtd` celulas na direcao relativa. Retorna quantas efetivamente
andou. Para em:
- **Obstaculo** (celula ocupada)
- **Borda** da grade (fora de 0..largura-1 / 0..altura-1)

```python
def mover(self, palavra, qtd):
    d = self.direcao_apos_movimento(palavra)
    dx, dy = self._delta(d)
    andados = 0
    for _ in range(int(qtd)):
        nx, ny = self.x + dx, self.y + dy
        if not self._em_grade(nx, ny): break
        if (nx, ny) in self.obstaculos: break
        self.x, self.y = nx, ny
        self.trilha.append((self.x, self.y))
        andados += 1
    return andados
```

### `sensor_distancia() -> int`

Disparo de raio na direcao atual ate encontrar um obstaculo ou a borda.
Retorna o numero de celulas **livres** a frente (excluindo a posicao atual).

```python
def sensor_distancia(self) -> int:
    dx, dy = self._delta(self.direcao)
    d = 0
    cx, cy = self.x, self.y
    while True:
        cx += dx; cy += dy
        if not self._em_grade(cx, cy): return d
        if (cx, cy) in self.obstaculos: return d
        d += 1
```

### `pegar()` e `soltar()`

`pegar()`: se ha objeto na celula atual, remove da grade e marca carregando.
`soltar()`: se carregando, deposita objeto na celula atual.

## Diretivas de Mundo

Comentarios com `# @` configuram o mundo sem violar a gramatica da linguagem:

```
# @mundo 30x20
# @inicio 5,10
# @direcao leste
# @obstaculo 8,12
# @objeto 14,7
```

### `parse_diretivas(fonte)`

Le o codigo-fonte com regex `#\s*@(\w+)\s+(.+)` e retorna dict de configuracao:

```python
cfg = {
    "largura": 30, "altura": 20,
    "x": None, "y": None,     # None -> centro
    "direcao": DIR_NORTE,
    "obstaculos": [(8,12)],
    "objetos": [(14,7)],
}
```

### `build_world(fonte, override=None)`

Combina as diretivas do codigo com overrides opcionais (usado no REPL com `--grid`).

## Log e Estado

- `ultima_acao`: string descritiva da ultima operacao
- `ultima_leitura`: ultimo valor lido pelo sensor
- `trilha`: lista de posicoes (usada para desenhar o rastro `+` na grade)
- `log`: lista de strings do historico de acoes (usado pelo REPL)
- `carregando`: flag que indica se o robo esta segurando um objeto

## Locais Importantes no Codigo

- `roboscript/world.py:7` - constantes de direcao
- `roboscript/world.py:26` - classe World
- `roboscript/world.py:88` - `sensor_distancia()`
- `roboscript/world.py:104` - `pegar()` / `soltar()`
- `roboscript/world.py:118` - `parse_diretivas()`
- `roboscript/world.py:160` - `build_world()`
