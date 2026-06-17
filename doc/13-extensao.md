# 13 - Estendendo o RoboScript

Este documento explica como adicionar novos recursos a linguagem ou ao executor.
Cada secao aborda uma camada diferente do pipeline.

## Indice de Alteracoes Comuns

| Voce quer... | Modificar |
|-------------|-----------|
| Nova palavra-chave | `lexer.py` (tabela) + `parser.py` (gramatica) |
| Novo comando do robo | `parser.py` (gramatica) + `interpreter.py` (execucao) + `world.py` (logica) |
| Novo tipo de operador | `lexer.py` + `parser.py` (precedencia) + `interpreter.py` (eval) |
| Nova estrutura de controle | `parser.py` (gramatica) + `ast_nodes.py` (no) + `interpreter.py` (execucao) |
| Novo simbolo na grade | `world.py` (estado) + `visualizer.py` (render) |
| Nova funcao builtin | `interpreter.py` (detectar e executar) |
| Novo meta-comando no REPL | `repl.py` (metodo + tabela de comandos) |
| Nova diretiva de mundo | `world.py` (`parse_diretivas()`) |
| Novo formato de saida (JSON, etc) | `visualizer.py` ou nova funcao chamada pelo CLI |

## Exemplo 1: Novo Comando do Robo -- `piscar`

Vamos adicionar `piscar N vezes;` que faz o robo piscar um LED no terminal.

### 1. `lexer.py`

Adicionar `"piscar"` ao set `PALAVRAS_RESERVADAS`:

```python
PALAVRAS_RESERVADAS = {
    # ... ja existentes
    "piscar",
}
```

### 2. `ast_nodes.py`

Nenhuma alteracao necessaria. A classe `ComandoRobo` ja tem `acao`, `direcao`,
`expressao` opcionais. Para `piscar`, usaremos `acao="piscar"` e `expressao`
para o numero de vezes.

### 3. `parser.py`

Adicionar o reconhecimento em `_comando_robo()`:

```python
if acao == "piscar":
    expr = self._expressao()
    self._esperar("PALAVRA_CHAVE", "vezes", msg="esperado 'vezes' apos expressao em 'piscar'")
    return ast.ComandoRobo(acao="piscar", expressao=expr, linha=tok.linha)
```

### 4. `world.py`

Adicionar estado para o LED (se precisar persistir):

```python
class World:
    # ...
    led_aceso: bool = False
```

E um metodo:

```python
def piscar(self, vezes):
    import time
    for _ in range(int(vezes)):
        self.led_aceso = not self.led_aceso
        self.ultima_acao = f"piscar (LED {'aceso' if self.led_aceso else 'apagado'})"
        # notify para animacao
```

### 5. `interpreter.py`

Adicionar case em `_exec_ComandoRobo`:

```python
if node.acao == "piscar":
    n = self._eval(node.expressao, env)
    self.world.piscar(n)
    self._step(f"piscar {n} vezes")
    return
```

### 6. `visualizer.py`

Adicionar indicacao do LED no painel de status:

```python
led = "LED: aceso" if world.led_aceso else ""
if led:
    linhas.append(led)
```

### 7. Testes

```python
def test_piscar(self):
    src = "piscar 3 vezes;"
    _, w = _run(src)
    # verifica que o comando executou sem erro
```

## Exemplo 2: Novo Simbolo na Grade -- `?` (portal)

### 1. `world.py`

```python
class World:
    portais: Set[Tuple[int, int]] = field(default_factory=set)
```

Adicionar em `parse_diretivas()`:

```python
elif chave == "portal":
    mm = re.match(r"(\d+)\s*,\s*(\d+)", valor)
    if mm:
        cfg["portais"].append((int(mm.group(1)), int(mm.group(2))))
```

### 2. `visualizer.py`

Adicionar no loop de render, antes do robo:

```python
for (px, py) in world.portais:
    if 0 <= px < world.largura and 0 <= py < world.altura:
        grade[py][px] = "?"
```

### 3. Legenda

Adicionar no painel:

```python
linhas.append("Legenda: ^>v< robo  # obstaculo  O objeto  ? portal  + trilha  . vazio")
```

## Exemplo 3: Nova Funcao Builtin -- `aleatorio(N)`

### 1. `interpreter.py`

No metodo `_eval_FuncaoChamada`, antes de buscar em `self.funcoes`,
verificar se eh builtin:

```python
builtins = {"aleatorio": self._builtin_aleatorio}

if node.nome in builtins:
    return builtins[node.nome](node, env)
```

Implementar:

```python
def _builtin_aleatorio(self, node, env):
    import random
    if len(node.args) != 1:
        raise RoboRuntimeError(node.linha, "aleatorio() espera 1 argumento")
    max_val = self._eval(node.args[0], env)
    return random.randint(0, int(max_val))
```

### 2. Teste

```python
def test_aleatorio(self):
    interp, _ = _run("int r = aleatorio(10);")
    self.assertIn("r", interp.global_env.vars)
    self.assertGreaterEqual(interp.global_env.vars["r"], 0)
    self.assertLessEqual(interp.global_env.vars["r"], 10)
```

## Guia Rapido: Onde Cada Coisa Mora

```
                     lexer    parser   ast      interp   world    visual   repl
Nova palavra-chave    X        X
Novo comando          X        X                 X        X
Nova expressao        X        X                 X
Nova estrutura                X        X        X
Novo simbolo                                       X        X
Nova builtin                              X
Novo meta-comando                                            X
Nova diretiva                                   X
```

## Padroes

### Adicionar uma palavra-chave
Sempre: `PALAVRAS_RESERVADAS` em `lexer.py` + regra em `parser.py`.
Se a palavra faz parte de um comando que ja existe (ex: nova direcao),
talvez so o `parser.py` precise mudar.

### Adicionar uma instrucao
Sempre: `ast_nodes.py` (se nao couber em no existente) + `parser.py` (gramatica)
+ `interpreter.py` (`_exec_`).

### Adicionar um estado ao mundo
Sempre: `world.py` (atributo + metodos) + `visualizer.py` (renderizar).
Opcionalmente `parse_diretivas()` se vier de configuracao.

## Convencoes de Estilo

- Nomes em **portugues** para tudo relacionado a linguagem (palavras-chave,
  mensagens de erro, nomes de funcoes do usuario)
- Nomes em **ingles** para codigo interno (`tokenize`, `parse`, `run`)
- Mensagens de erro seguem o padrao:
  ```
  [Linha N] Erro <tipo>: <mensagem>
  ```
- `@dataclass` para nos da AST
- Toda excecao herda de `RoboError`
- Testes usam `unittest.TestCase`
