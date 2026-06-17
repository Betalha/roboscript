# 04 - Analise Sintatica (Parser)

**Arquivo:** `roboscript/parser.py`

## Responsabilidade

Converter a lista de tokens em uma **Arvore Sintatica Abstrata (AST)**,
verificando se a sequencia obedece a gramatica EBNF do PDF (Etapa 3). O parser
**nao** executa o codigo; apenas valida a estrutura.

## API Publica

```python
from roboscript.parser import parse, parse_uma, parse_expressao

# Parsing completo (programa)
tokens = tokenize("int x = 5; mover frente 3 cm;")
prog = parse(tokens)           # retorna ast.Programa

# Parsing de uma instrucao (usado no REPL)
ins = parse_uma(tokens)        # retorna primeira instrucao (ast)

# Parsing de expressao pura (usado no REPL)
expr = parse_expressao(tokenize("2 + 3"))
```

## Organizacao Interna

O parser implementa um **analisador recursivo-descendente** com uma funcao para
cada nao-terminal da gramatica. A classe principal eh `Parser`:

```python
class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    def parse(self) -> ast.Programa:
        instrucoes = []
        while not self._check("EOF"):
            instrucoes.append(self._instrucao())
        return ast.Programa(instrucoes=instrucoes)
```

## Metodos Auxiliares

Cada metodo auxiliar manipula o token atual e verifica o tipo/proximo token:

| Metodo | Funcao |
|--------|--------|
| `_atual()` | Retorna token na posicao atual (sem consumir) |
| `_avancar()` | Consome e retorna o token atual, avanca |
| `_check(tipo, [lexema])` | Verifica se token atual casa (sem consumir) |
| `_match(tipo, [lexema])` | Se casar, consome e retorna `True` |
| `_esperar(tipo, [lexema], [msg])` | Se casar, consome; senao, lanca `RoboSyntaxError` |

## Arvore de Chamadas (Metodos por Nao-Terminal)

Cada metodo segue exatamente a EBNF do PDF:

```
_instrucao()
├── tipo? -> _declaracao()
├── "mover"/"girar"/... -> _comando_robo()
├── "se" -> _condicional()
├── "enquanto"/"repita" -> _repeticao()
├── "func" -> _funcao_def()
├── "imprimir"/"ler" -> _entrada_saida()
├── "retorno" -> _retorno()
├── IDENT + "=" -> _atribuicao()
└── IDENT + "(" -> _primario() (chamada de funcao)

_expressao()
└── _expr_ou()  # nivel mais baixo de precedencia
    └── _expr_e()
        └── _expr_nao()
            └── _expr_relacional()
                └── _expr_adit()
                    └── _expr_mult()
                        └── _expr_unaria()
                            └── _primario()
```

### Exemplo: precedencia na expressao `1 + 2 * 3`

```
1 + 2 * 3
├── _expr_ou -> _expr_e -> ... -> _expr_adit (loop "+")
│   ├── esq: _expr_mult -> _expr_unaria -> _primario -> 1
│   ├── op: "+"
│   └── dir: _expr_mult (loop "*")
│       ├── esq: _expr_unaria -> _primario -> 2
│       ├── op: "*"
│       └── dir: _expr_unaria -> _primario -> 3
```

Resultado: `BinOp(+, 1, BinOp(*, 2, 3))` -- corretamente precedencia.

## Destaques da Implementacao

### 1. `_instrucao()` -- deteccao de qual construto usar

Como diferentes instrucoes podem comecar com tokens parecidos
(ex: `IDENTIFICADOR` pode ser atribuicao `x = 5` ou chamada `x()`),
olhamos **2 tokens a frente** (lookahead de 1):

```python
if t.tipo == "IDENTIFICADOR":
    prox = self.tokens[self.pos + 1] if self.pos + 1 < len(self.tokens) else None
    if prox and prox.tipo == "OP_ATRIB":        # x = ... -> atribuicao
        ins = self._atribuicao()
    elif prox and prox.tipo == "DELIMITADOR" and prox.lexema == "(":  # x() -> chamada
        chamada = self._primario()
```

### 2. `_comando_robo()` -- comandos com e sem expressao

```python
if acao == "mover":
    d = self._direcao()
    expr = self._expressao()
    unid = self._esperar("PALAVRA_CHAVE", "cm", ...)
    return ast.ComandoRobo(acao="mover", direcao=d, expressao=expr, ...)
elif acao == "girar":
    d = self._direcao()
    expr = self._expressao()
    unid = self._esperar("PALAVRA_CHAVE", "graus", ...)
elif acao == "esperar":
    expr = self._expressao()
    return ast.ComandoRobo(acao="esperar", expressao=expr, ...)
else:  # parar, pegar, soltar
    return ast.ComandoRobo(acao=acao, ...)
```

### 3. `_condicional()` -- encadeamento `senao se`

```python
def _condicional(self):
    self._avancar()  # "se"
    <consumir ( condicao )>
    bloco_entao = self._bloco()
    bloco_senao = None
    if self._check("PALAVRA_CHAVE", "senao"):
        self._avancar()
        if self._check("PALAVRA_CHAVE", "se"):
            bloco_senao = [self._condicional()]  # senao se -> aninha
        else:
            bloco_senao = self._bloco()
```

### 4. `_bloco()` -- conteudo entre `{}`

Consome instrucoes ate encontrar `}`, depois verifica fechamento.

### 5. `_primario()` -- identificador vs chamada de funcao

Se encontra `IDENTIFICADOR` seguido de `(`, trata como `FuncaoChamada`:

```python
if t.tipo == "IDENTIFICADOR":
    self._avancar()
    if self._check("DELIMITADOR", "("):
        # consome args...
        return ast.FuncaoChamada(nome=t.lexema, args=args, ...)
    return ast.Identificador(nome=t.lexema, ...)
```

## API Estendida para o REPL

O `Parser` expoe metodos publicos adicionais para o REPL poder processar
comandos um por vez:

```python
def parse_uma_instrucao(self):
    """Consome e retorna apenas uma instrucao. Nao exige EOF."""
    if self._check("EOF"):
        return None
    return self._instrucao()

def parse_expressao_publica(self):
    """Tenta parsear uma expressao pura. Levanta erro se falhar."""
    expr = self._expressao()
    # garante que nao sobrou nada
    if not self._check("EOF"):
        raise RoboSyntaxError(...)
    return expr

def at_end(self) -> bool:
    return self._check("EOF")
```

## Erros Sintaticos

Todos lancam `RoboSyntaxError` com o formato do PDF:
```
[Linha N] Erro sintatico: <mensagem>
```

| Situacao | Mensagem |
|----------|----------|
| `mover 10 cm;` (falta direcao) | `esperada direcao ('frente', 'tras', 'esquerda' ou 'direita') apos 'mover', encontrado '10'` |
| `int ;` (falta nome) | `esperado nome de variavel apos tipo` |
| `se x > 0 { }` (falta parenteses) | `esperado '(' apos 'se'` |
| `mover frente 5` (falta cm) | `esperada unidade 'cm' apos expressao em 'mover'` |
| `func 123()` | `esperado nome de funcao apos 'func'` |
| `;` (solto) | `instrucao invalida iniciada por ';'` |

## Testes Relacionados

`tests/test_parser.py` (7 testes):
- declaracao simples
- comando `mover`
- condicional com senao
- definicao e chamada de funcao
- erro da direcao faltando (mensagem exata do PDF)
- precedencia de operadores
- `repita ... vezes`

## Locais Importantes no Codigo

- `roboscript/parser.py:12` - classe Parser
- `roboscript/parser.py:95` - `_instrucao()` (dispatcher principal)
- `roboscript/parser.py:199` - `_comando_robo()`
- `roboscript/parser.py:236` - `_condicional()`
- `roboscript/parser.py:278` - `_expressao()` ate `_primario()`
- `roboscript/parser.py:365` - `parse_uma_instrucao()` (REPL API)
