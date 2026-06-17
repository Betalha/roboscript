# 03 - Analise Lexica (Lexer)

**Arquivo:** `roboscript/lexer.py`

## Responsabilidade

Converter o texto fonte em uma sequencia linear de **tokens**. O lexer **nao**
verifica sintaxe; ele apenas reconhece padroes regulares (palavras-chave,
identificadores, numeros, strings, operadores, delimitadores).

## API Publica

```python
from roboscript.lexer import tokenize, Token, PALAVRAS_RESERVADAS

tokens = tokenize("mover frente 5 cm;")
# [Token(PALAVRA_CHAVE, 'mover', ...), Token(PALAVRA_CHAVE, 'frente', ...), ...]
```

## Estrutura `Token`

```python
@dataclass
class Token:
    tipo: str        # ex: "PALAVRA_CHAVE", "IDENTIFICADOR", "NUMERO_INTEIRO"
    lexema: str      # texto original tal como apareceu no codigo
    valor: object    # valor convertido (int para NUMERO, str para STRING, etc)
    linha: int       # numero da linha (1-indexed)
    coluna: int      # coluna onde o token comeca
```

## Tipos de Token Produzidos

| Tipo | Exemplo | `valor` |
|------|---------|---------|
| `PALAVRA_CHAVE` | `mover`, `se`, `int` | mesmo que lexema |
| `IDENTIFICADOR` | `velocidade`, `meu_robo` | mesmo que lexema |
| `NUMERO_INTEIRO` | `42`, `0` | `int(42)` |
| `NUMERO_DECIMAL` | `3.14` | `float(3.14)` |
| `STRING` | `"ola"` | `"ola"` (sem aspas, escapes interpretados) |
| `OP_RELACIONAL` | `==`, `>=`, `<` | mesmo que lexema |
| `OP_LOGICO` | `and`, `or`, `not` | mesmo que lexema |
| `OP_ARIT` | `+`, `-`, `*`, `/` | mesmo que lexema |
| `OP_ATRIB` | `=` | `"="` |
| `DELIMITADOR` | `(`, `)`, `{`, `}`, `,`, `;`, `:` | mesmo que lexema |
| `EOF` | (fim do arquivo) | `None` |

## Tabela de Palavras Reservadas

Definida como `set` na constante `PALAVRAS_RESERVADAS`:

```python
PALAVRAS_RESERVADAS = {
    "mover", "girar", "parar", "pegar", "soltar", "esperar", "sensor",
    "se", "senao", "enquanto", "repita", "vezes",
    "func", "retorno", "imprimir", "ler",
    "int", "float", "texto", "bool",
    "verdade", "falso",
    "frente", "tras", "esquerda", "direita", "graus", "cm",
}

OP_LOGICOS = {"and", "or", "not"}
```

**Regra critica do PDF:** quando o lexer le uma sequencia que casa com
`IDENTIFICADOR`, ele consulta esta tabela. Se o lexema esta na tabela, emite
como `PALAVRA_CHAVE`; senao, como `IDENTIFICADOR`. Isso garante que `mover` eh
sempre reservado mas `movimento` eh um identificador valido.

## Algoritmo Principal

O lexer eh um **automato de estados implicito** implementado como loop que
inspeciona o caractere atual e despacha para um dos handlers especializados:

```python
def tokenize(self) -> List[Token]:
    while not self._at_end():
        c = self._peek()
        if c in (" ", "\t", "\r", "\n"):    # whitespace -> ignora
            self._avancar()
        elif c == "#":                       # comentario de linha
            <consome ate \n>
        elif c == "/" and self._peek(1) == "*":   # comentario de bloco
            <consome ate */>
        elif c == '"':
            self._string()
        elif c.isdigit():
            self._numero()
        elif c.isalpha() or c == "_":
            self._identificador()
        elif self._operador_ou_delim():
            pass
        else:
            raise RoboLexError(self.linha, f"caractere inesperado {c!r}")
    self.tokens.append(Token("EOF", ...))
    return self.tokens
```

## Handlers Especializados

### `_string()` - literais de texto

Le caracteres entre aspas duplas, interpretando escapes:

| Escape | Significado |
|--------|-------------|
| `\n` | nova linha |
| `\t` | tab |
| `\"` | aspas |
| `\\` | barra invertida |

Erros possiveis:
- string nao terminada (EOF antes de fechar `"`)
- escape invalido (ex: `\q`)

### `_numero()` - literais numericos

1. Consome digitos
2. Se ve `.` seguido de mais digitos, considera decimal
3. Apos consumir, verifica se ha letra colada -- nesse caso eh **erro**:

```python
if not self._at_end() and (self._peek().isalpha() or self._peek() == "_"):
    # consome o resto para mostrar o lexema invalido (ex: "2robo")
    raise RoboLexError(
        linha_ini,
        f"identificador nao pode comecar com digito -- encontrado '{lex_inv}'"
    )
```

Esta verificacao garante a mensagem **exata** do PDF para o caso `int 2robo = 3;`.

### `_identificador()` - palavras-chave ou identificadores

```python
def _identificador(self):
    ini = self.pos
    while not self._at_end() and (self._peek().isalnum() or self._peek() == "_"):
        self._avancar()
    lex = self.fonte[ini:self.pos]
    if lex in PALAVRAS_RESERVADAS:
        self.tokens.append(Token("PALAVRA_CHAVE", lex, lex, ...))
    elif lex in OP_LOGICOS:
        self.tokens.append(Token("OP_LOGICO", lex, lex, ...))
    else:
        self.tokens.append(Token("IDENTIFICADOR", lex, lex, ...))
```

### `_operador_ou_delim()` - simbolos

Tenta primeiro casar com operadores de **2 caracteres** (`==`, `!=`, `>=`, `<=`).
Se nao bater, tenta de **1 caractere** (`>`, `<`, `+`, `-`, `*`, `/`, `=`).
Por fim, delimitadores (`(`, `)`, `{`, `}`, `,`, `;`, `:`).

Retorna `True` se reconheceu algo, `False` caso contrario (que dispara erro
"caractere inesperado" no loop principal).

## Rastreamento de Linha/Coluna

O metodo `_avancar()` mantem `self.linha` e `self.coluna` atualizados:

```python
def _avancar(self) -> str:
    c = self.fonte[self.pos]
    self.pos += 1
    if c == "\n":
        self.linha += 1
        self.coluna = 1
    else:
        self.coluna += 1
    return c
```

Isso permite que toda excecao reporte a linha correta no formato do PDF:
```
[Linha 2] Erro lexico: identificador nao pode comecar com digito -- encontrado '2robo'
```

## Tratamento de Comentarios

```python
# comentario de linha     -> descartado ate \n
/* comentario de bloco */ -> descartado ate */
```

Comentarios **nao geram tokens**. Entretanto, o codigo-fonte original (incluindo
comentarios) ainda eh acessivel ao `world.py` para extrair diretivas `# @...`
antes mesmo do lexer rodar.

## Exemplo Completo

Entrada:
```
int x = 5;
mover frente x cm;
```

Tokens produzidos (ignorando `EOF` final):

| # | tipo | lexema | linha |
|---|------|--------|-------|
| 1 | PALAVRA_CHAVE | int | 1 |
| 2 | IDENTIFICADOR | x | 1 |
| 3 | OP_ATRIB | = | 1 |
| 4 | NUMERO_INTEIRO | 5 | 1 |
| 5 | DELIMITADOR | ; | 1 |
| 6 | PALAVRA_CHAVE | mover | 2 |
| 7 | PALAVRA_CHAVE | frente | 2 |
| 8 | IDENTIFICADOR | x | 2 |
| 9 | PALAVRA_CHAVE | cm | 2 |
| 10 | DELIMITADOR | ; | 2 |

## Erros Lexicais

Todos lancam `RoboLexError` (definida em `errors.py`):

| Causa | Mensagem |
|-------|----------|
| caractere desconhecido | `caractere inesperado '?'` |
| `2robo` | `identificador nao pode comecar com digito -- encontrado '2robo'` |
| string sem fechar | `string nao terminada` |
| escape invalido | `sequencia de escape invalida '\q'` |
| comentario `/* */` sem fechar | `comentario de bloco nao fechado` |

## Testes Relacionados

`tests/test_lexer.py` (9 testes):
- palavras reservadas vs identificadores
- todos os operadores relacionais
- strings com escape `\n`
- comentarios descartados (linha e bloco)
- identificador comecando com digito (mensagem exata do PDF)
- numeros inteiros e decimais
- delimitadores

`tests/test_errors.py` valida que a mensagem do erro lexico bate exatamente
com a descrita no PDF para `Invalido 2`.

## Locais Importantes do Codigo

- `roboscript/lexer.py:7` - `PALAVRAS_RESERVADAS`
- `roboscript/lexer.py:19` - dataclass `Token`
- `roboscript/lexer.py:31` - classe `Lexer`
- `roboscript/lexer.py:62` - metodo `tokenize` (loop principal)
- `roboscript/lexer.py:96` - `_string`
- `roboscript/lexer.py:125` - `_numero` (com checagem `2robo`)
- `roboscript/lexer.py:154` - `_identificador`
- `roboscript/lexer.py:168` - `_operador_ou_delim`
