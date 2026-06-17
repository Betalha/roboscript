# 06 - Interpretador

**Arquivo:** `roboscript/interpreter.py`

## Responsabilidade

Percorrer a AST produzida pelo parser e **executar** cada no, atualizando o
estado do mundo e das variaveis. Eh um interpretador **tree-walking** classico:
cada metodo visita (visitor pattern) um tipo de no da AST e faz o que ele
significa.

## API Publica

```python
from roboscript.interpreter import Interpreter
from roboscript.world import World

world = World(largura=30, altura=20)
interp = Interpreter(world, on_step=None, speed=0)

# Execucao normal: recebe o programa completo (ast.Programa)
interp.run(programa)

# Execucao passo-a-passo (para REPL):
interp.exec_uma(declaracao)    # executa uma instrucao
resultado = interp.eval_uma(expressao)  # avalia expressao e retorna valor
```

## Estrutura Interna

### `Environment` -- tabela de simbolos

```python
class Environment:
    def __init__(self, parent: Optional["Environment"] = None):
        self.vars: Dict[str, Any] = {}    # nome -> valor
        self.types: Dict[str, str] = {}   # nome -> tipo
        self.parent = parent              # escopo pai (encadeamento)
```

Cada funcao cria um `Environment` filho (com escopo `parent` apontando para
o ambiente global). A resolucao de variaveis sobe na cadeia:

```
global: { x=5, dobro=<func> }
  └── env_dobro (parent=global): { n=7 }
```

Quando uma variavel nao existe no ambiente atual, `_find` pergunta ao
`parent` recursivamente.

### `Interpreter` -- estado principal

```python
class Interpreter:
    def __init__(self, world, on_step=None, speed=0.2):
        self.global_env = Environment()
        self.funcoes = {}          # nome -> ast.FuncaoDef
        self.world = world
        self.on_step = on_step     # callback para redesenhar a grade
        self.speed = speed         # delay entre comandos
        self.output = []           # lista de strings do "imprimir"
```

## Metodos de Execucao

### `_exec(node, env)` -- dispatcher de instrucoes

```python
def _exec(self, node, env):
    m = getattr(self, f"_exec_{type(node).__name__}", None)
    if m is None:
        raise RoboRuntimeError(linha, f"nao sei executar {type(node).__name__}")
    return m(node, env)
```

Cada tipo de no tem seu handler: `_exec_Declaracao`, `_exec_ComandoRobo`, etc.

### `_eval(node, env)` -- dispatcher de expressoes

```python
def _eval(self, node, env):
    m = getattr(self, f"_eval_{type(node).__name__}", None)
    if m is None:
        raise RoboRuntimeError(linha, f"nao sei avaliar {type(node).__name__}")
    return m(node, env)
```

### Funcoes e `_ReturnSignal`

Funcoes sao executadas via chamada ao `_eval_FuncaoChamada`, que:
1. Cria um novo `Environment` filho com parametros
2. Executa o bloco da funcao
3. Se encontra `retorno`, lanca `_ReturnSignal(valor)` -- capturado no `try/except`
4. Se nao ha retorno, devolve `None`

```python
class _ReturnSignal(Exception):
    def __init__(self, valor):
        self.valor = valor
```

## Dispatcher de cada tipo

### Declaracoes e Atribuicoes

```python
_decl_ "int x = 5"  -> env.declare("x", "int", 5, linha)
_atrib_ "x = x + 1" -> env.assign("x", valor, linha)
```

- `declare()` da erro se variavel ja existe no escopo
- `assign()` usa `_find()` que aceita escopo pai (para reatribuir variavel global
  dentro de funcao)

### Comandos do Robo

Cada comando chama metodos no `world` e dispara o callback `_step()`:

```python
def _step(self, acao, leitura=None):
    self.world.ultima_acao = acao
    if self.on_step:
        self.on_step(self.world)      # -> visualizer.render()
        time.sleep(self.speed)
```

**Mover:** chama `world.mover(direcao, qtd)` que retorna quantas celulas
efetivamente andou (para em obstaculos e bordas).

**Girar:** chama `world.girar(palavra, graus)` que normaliza para 0/90/180/270.

**Pegar/Soltar:** chama `world.pegar()` / `world.soltar()` que atualizam
`carregando` e movem objetos entre robo e grade.

**Esperar:** faz `time.sleep(min(float(qtd) * 0.1, 2.0))` se `speed > 0`.

### Controle de Fluxo

**`se`:** avalia condicao, usa `_truthy()` para decidir:

```python
def _truthy(self, v):
    if isinstance(v, bool): return v
    if isinstance(v, (int, float)): return v != 0
    if isinstance(v, str): return len(v) > 0
    return bool(v)
```

**`enquanto`:** loop com limite de 100.000 iteracoes para evitar travamento:

```python
i = 0
while self._truthy(self._eval(node.condicao, env)):
    <executa bloco>
    i += 1
    if i > 100000:
        raise RoboRuntimeError(...)
```

**`repita N vezes`:**
```python
for _ in range(int(n)):
    <executa bloco>
```

### `imprimir`

```python
partes = [self._fmt(self._eval(e, env)) for e in node.expressoes]
self.output.append(" ".join(partes))
```

### `ler(distancia)` -- sensor automatico

```python
d = self.world.sensor_distancia()  # celulas ate obstaculo na direcao atual
env.assign(node.nome, d, linha)
```

Nao le do stdin. A simulacao retorna a distancia real baseada no mundo atual.

### Operadores Binarios

Avalia operando esquerdo e direito, depois aplica o operador:

```python
if op == "and":   # short-circuit
    a = self._eval(node.esq, env)
    return self._truthy(a) and self._truthy(self._eval(node.dir, env))
if op == "or":    # short-circuit
    a = self._eval(node.esq, env)
    return self._truthy(a) or self._truthy(self._eval(node.dir, env))
if op == "/" and b == 0:
    raise RoboRuntimeError(...)
```

## Formatacao de Valores

`_fmt()` garante que `verdade`/`falso` aparecem em portugues:

```python
def _fmt(self, v):
    if isinstance(v, bool): return "verdade" if v else "falso"
    if v is None: return "(nulo)"
    return str(v)
```

## Fluxo de Execucao do `run()`

```python
def run(self, programa):
    # 1a passada: registra todas as funcoes
    for ins in programa.instrucoes:
        if isinstance(ins, ast.FuncaoDef):
            self.funcoes[ins.nome] = ins
    self._step("(inicio)")
    # 2a passada: executa instrucoes (pulando defs)
    for ins in programa.instrucoes:
        if isinstance(ins, ast.FuncaoDef):
            continue
        self._exec(ins, self.global_env)
```

## Tratamento de Erros

- `RoboRuntimeError` para erros de execucao (variavel nao declarada, divisao
  por zero, loop infinito, etc.)
- `RoboTypeError` para incompatibilidade de tipos (ex: atribuir `texto` a `int`)
- `_ReturnSignal` nao eh excecao de erro; eh mecanismo de controle de fluxo

## Locais Importantes no Codigo

- `roboscript/interpreter.py:15` - class Environment
- `roboscript/interpreter.py:49` - class Interpreter
- `roboscript/interpreter.py:76` - `run()` (loop principal)
- `roboscript/interpreter.py:103` - `_exec_ComandoRobo` (comandos do robo)
- `roboscript/interpreter.py:180` - `_eval_BinOp` (operadores)
- `roboscript/interpreter.py:246` - `exec_uma()` / `eval_uma()` (API REPL)
