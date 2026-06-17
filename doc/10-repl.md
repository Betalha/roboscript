# 10 - REPL Interativo

**Arquivo:** `roboscript/repl.py`

## Responsabilidade

Prover um shell interativo onde o usuario escreve codigo RoboScript linha a
linha e ve imediatamente o resultado visual e textual. O estado (variaveis,
funcoes, posicao do robo, obstaculos) persiste entre comandos.

## Arquitetura

A classe `RoboREPL` orquestra:

1. **Leitura**: captura input, detecta blocos multi-linha, mantem historio
2. **Processamento**: decide se eh meta-comando / expressao / instrucao e executa
3. **Renderizacao**: desenha grade + painel de status no terminal

```
 +----------+      +------------+      +----------+
 |  input() | ---> | _processar | ---> | _render  |
 |  readline|      | src        |      | grade    |
 +----------+      +-----+------+      +----------+
                         |
                    +----v----+
                    | lexer   |
                    | parser  |
                    | interp  |
                    +---------+
```

## Ciclo Principal

```python
def run(self):
    if self._interactive:
        self._setup_readline()     # ativa readline + completer
        self._render()             # desenha grade inicial
    while self.rodando:
        try:
            src = self._ler_entrada_completa()   # suporta multi-linha
        except EOFError:
            break              # Ctrl+D
        except KeyboardInterrupt:
            continue           # Ctrl+C cancela linha
        if not src.strip():
            continue
        self._processar(src)   # executa
        self._render()         # redesenha
```

## Leitura Multi-linha

O REPL detecta automaticamente blocos que precisam de mais linhas (funcoes,
ifs, loops) contando `{` vs `}` abertos:

```
robo> func dobro(int n) {
....>   retorno n * 2;
....> }
```

O metodo `_blocos_completos(src)` conta chaves ignorando comentarios e strings:

```python
def _blocos_completos(self, src):
    abertos = 0
    # percorre caractere por caractere ignorando "#", "/* */" e strings
    if abertos <= 0: return True
```

Quando `abertos > 0`, o prompt muda de `robo>` para `....>`.

## Processamento de Cada Entrada

`_processar(src)` segue 3 etapas:

### 1. Meta-comando (`:help`, `:vars`, etc.)

Despacha para `_meta()` que executa funcoes rapidas sem tocar no interpretador.

### 2. Tentativa como expressao pura

```python
if not src_strip.endswith(";") and "{" not in src_strip:
    try:
        toks = tokenize(src)
        expr = parse_expressao(toks)
        v = self.interp.eval_uma(expr)
        self.ultimo_resultado = self.interp.fmt(v)
        return
    except RoboError:
        pass  # nao era expressao -> tenta como instrucao
```

Expressoes nuas sao avaliadas e o resultado mostrado com `=> 5`.

### 3. Execucao como instrucao

```python
src_norm = self._normalizar(src)
toks = tokenize(src_norm)
parser = Parser(toks)
while not parser.at_end():
    ins = parser.parse_uma_instrucao()
    self.interp.exec_uma(ins)
```

## Normalizacao de `;`

```python
def _normalizar(self, src):
    s = src.rstrip()
    if s.endswith(";") or s.endswith("}"):
        return s
    return s + ";"
```

Se a linha nao termina em `;` ou `}`, adiciona `;` automaticamente.

## Meta-comandos

Implementados em `_meta(linha)`. Tabela completa:

| Comando | Ação |
|---------|------|
| `:help`, `:h` | Mostra ajuda |
| `:vars`, `:v` | Lista variaveis e tipos |
| `:funcs`, `:f` | Lista funcoes |
| `:world` | Mostra estado do mundo |
| `:reset` | Reinicia mundo, variaveis e funcoes |
| `:obstaculo X,Y` | Adiciona obstaculo |
| `:objeto X,Y` | Adiciona objeto |
| `:rm X,Y` | Remove objeto/obstaculo |
| `:teleport X,Y` | Move robo |
| `:speed N` | Ajusta delay da animacao |
| `:load arquivo.robo` | Carrega e executa arquivo |
| `:tokens <codigo>` | Mostra tokens |
| `:ast <codigo>` | Mostra AST |
| `:redraw`, `:r` | Redesenha grade |
| `:clear` | Limpa terminal |
| `:mode tela|log` | Alterna modo de exibicao |
| `:quit`, `:q`, `:exit` | Sai |

## Tab Completion

```python
def _completer(self, texto, estado):
    candidatos = sorted(set(
        list(PALAVRAS_RESERVADAS)
        + ["and", "or", "not"]
        + list(self.interp.global_env.vars.keys())
        + list(self.interp.funcoes.keys())
        + META_COMMANDS
    ))
    matches = [c for c in candidatos if c.startswith(texto)]
```

Completa:
- Palavras reservadas fixas (`mover`, `se`, `int`, ...)
- Variaveis declaradas (dinamico)
- Funcoes definidas (dinamico)
- Meta-comandos (`:vars`, `:q`, ...)

Ativado por `readline.parse_and_bind("tab: complete")`.

## Historico

Salvo em `~/.roboscript_history` com ate 1000 entradas:

```python
self._histfile = os.path.expanduser("~/.roboscript_history")

def _setup_readline(self):
    import readline
    try:
        readline.read_history_file(self._histfile)
    except OSError:
        pass
    readline.set_history_length(1000)

def _save_history(self):
    try:
        readline.write_history_file(self._histfile)
    except Exception:
        pass
```

## Modos de Exibicao

### Modo `tela` (default)

Usa `\033[2J\033[H` para limpar e redesenhar toda a tela a cada comando.
Inclui:
- Grade do mundo
- Painel: Vars, Funcs, Saida (ultimos 4), Resultados, Erros

### Modo `log`

Nao limpa a tela. Apenas mostra resultado/erro de cada comando inline.
Util quando redirecionando saida para arquivo ou pipe.

A deteccao de TTY (`sys.stdin.isatty()` e `sys.stdout.isatty()`) automaticamente
desabilita o modo tela em pipes.

## Tratamento de Erros

Toda excecao da cadeia `RoboError` eh capturada e exibida em vermelho:

```python
except RoboError as e:
    self.ultimo_erro = str(e)
except Exception as e:
    self.ultimo_erro = f"erro interno: {type(e).__name__}: {e}"
```

O erro **nao** interrompe o REPL. O usuario pode corrigir e tentar novamente.

## Locais Importantes no Codigo

- `roboscript/repl.py:60` - classe `RoboREPL`
- `roboscript/repl.py:70` - `run()` loop principal
- `roboscript/repl.py:120` - `_ler_entrada_completa()` multi-linha
- `roboscript/repl.py:168` - `_processar()` dispatcher
- `roboscript/repl.py:233` - `_meta()` meta-comandos
- `roboscript/repl.py:390` - `_completer()` tab completion
- `roboscript/repl.py:410` - `run_repl()` funcao de conveniencia
