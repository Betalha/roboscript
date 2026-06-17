# 09 - CLI (Linha de Comando)

**Arquivo:** `roboscript.py`

## Responsabilidade

Entry-point do projeto. Usa `argparse` para definir subcomandos e chama o modulo
apropriado para cada acao.

## Uso Geral

```bash
python3 roboscript.py <subcomando> [opcoes]
```

## Subcomandos

### `run` -- Executa programa com visualizacao

```bash
python3 roboscript.py run examples/exemplo3.robo
python3 roboscript.py run examples/exemplo3.robo --no-anim
python3 roboscript.py run examples/exemplo2.robo --speed 0.4
```

Fluxo interno:
1. Le o arquivo
2. `tokenize()` -> List[Token]
3. `parse()` -> AST
4. `build_world()` + `Interpreter()` com callback `on_step` que chama `render()`
5. `interp.run(prog)` executa e anima passo-a-passo

Flags:
- `--speed`: delay em segundos entre comandos (default 0.25)
- `--no-anim`: imprime quadro final sem animacao

### `tokens` -- Lista tokens (formato Etapa 4 do PDF)

```bash
python3 roboscript.py tokens examples/exemplo1.robo
```

Saida:
```
Lexema             Tipo
-----------------  --------------------
int                PALAVRA_CHAVE
velocidade         IDENTIFICADOR
=                  OP_ATRIB
5                  NUMERO_INTEIRO
;                  DELIMITADOR
...
```

### `ast` -- Imprime AST em arvore

```bash
python3 roboscript.py ast examples/exemplo1.robo
```

Saida:
```
Programa
  Declaracao(tipo=int, nome=velocidade)
    Literal(int: 5)
  ...
```

### `check` -- Valida lexico + sintatico

```bash
python3 roboscript.py check examples/exemplo1.robo
# OK: examples/exemplo1.robo - analise lexica e sintatica concluida sem erros.

python3 roboscript.py check examples/invalido1.robo
# [Linha 2] Erro sintatico: esperada direcao ...
```

Exit code: `0` se OK, `1` se erro.

### `repl` -- Shell interativo

```bash
python3 roboscript.py repl
python3 roboscript.py repl --load examples/exemplo3.robo
python3 roboscript.py repl --grid 40x15
python3 roboscript.py repl --speed 0.15 --no-banner
```

Veja `10-repl.md` para detalhes.

Flags:
- `--load <arquivo>`: pre-carrega e executa arquivo
- `--speed <N>`: delay entre passos (default 0.1)
- `--grid <WxH>`: dimensoes da grade (default 30x20)
- `--no-banner`: nao mostra mensagem de boas-vindas

## Funcoes Internas

Cada subcomando tem seu handler:

```python
def cmd_run(args):
    fonte = _ler_arquivo(args.arquivo)
    toks = tokenize(fonte)
    prog = parse(toks)
    world = build_world(fonte)
    # ... animacao ...

def cmd_tokens(args):
    fonte = _ler_arquivo(args.arquivo)
    toks = tokenize(fonte)
    # ... imprime tabela ...

def cmd_ast(args):
    fonte = _ler_arquivo(args.arquivo)
    toks = tokenize(fonte)
    prog = parse(toks)
    print(ast_to_string(prog))

def cmd_check(args):
    fonte = _ler_arquivo(args.arquivo)
    toks = tokenize(fonte)
    parse(toks)
    print(f"OK: {args.arquivo} ...")

def cmd_repl(args):
    run_repl(load_path=args.load, ...)
```

## Tratamento de Erros

```python
try:
    toks = tokenize(fonte)
    prog = parse(toks)
except RoboError as e:
    print(e, file=sys.stderr)
    sys.exit(1)
```

Toda excecao `RoboError` eh capturada, impressa em stderr e o processo termina
com codigo 1. No REPL, erros sao capturados dentro do loop e nao terminam o
processo.

## Locais Importantes no Codigo

- `roboscript.py:14` - `_ler_arquivo()`
- `roboscript.py:20` - `cmd_tokens()`
- `roboscript.py:48` - `cmd_run()`
- `roboscript.py:96` - `cmd_repl()`
- `roboscript.py:117` - `main()`
