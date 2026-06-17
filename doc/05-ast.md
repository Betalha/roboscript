# 05 - Nos da Arvore Sintatica Abstrata (AST)

**Arquivo:** `roboscript/ast_nodes.py`

## Proposito

Define as classes de dados (usando `@dataclass`) que representam cada construcao
sintatica do RoboScript. O parser produz uma arvore destes nos; o interpretador
a percorre recursivamente.

## Design

Cada no eh um `@dataclass` Python com:
- Atributos especificos do tipo de nó
- `linha` (padrao `0`) para rastreamento de erros

Os nos sao divididos em duas categorias: **expressoes** (produzem valores) e
**instrucoes** (nao produzem valores, mas alteram estado).

## Nos de Expressao (produzem valor)

### `Literal`

Valores constantes no codigo.

```python
@dataclass
class Literal:
    valor: Any
    tipo: str   # "int", "float", "texto", "bool"
    linha: int = 0
```

Exemplos na AST:
```
Literal(int: 5)
Literal(texto: 'Ola')
Literal(bool: True)   # "verdade"
Literal(float: 3.14)
```

### `Identificador`

Referencia a uma variavel.

```python
@dataclass
class Identificador:
    nome: str
    linha: int = 0
```

```
Identificador(nome="velocidade")
```

### `BinOp`

Operacao binaria (dois operandos).

```python
@dataclass
class BinOp:
    op: str         # "+", "-", "*", "/", "==", "<", "and", "or", etc
    esq: Any
    dir: Any
    linha: int = 0
```

```
BinOp(+)
  Identificador(x)
  Literal(int: 5)
```

### `UnOp`

Operacao unaria (um operando).

```python
@dataclass
class UnOp:
    op: str         # "-" ou "not"
    operando: Any
    linha: int = 0
```

```
UnOp(not)
  Identificador(ok)
```

### `FuncaoChamada`

Chamada de funcao com argumentos.

```python
@dataclass
class FuncaoChamada:
    nome: str
    args: List[Any] = field(default_factory=list)
    linha: int = 0
```

```
FuncaoChamada(dobro)
  Literal(int: 7)
```

## Nos de Instrucao (nao produzem valor)

### `Declaracao`

Declaracao de variavel com ou sem inicializacao.

```python
@dataclass
class Declaracao:
    tipo: str                   # "int", "float", "texto", "bool"
    nome: str
    valor: Optional[Any] = None # None se sem inicializacao
    linha: int = 0
```

```
int x = 5;
=>
Declaracao(tipo=int, nome=x)
  Literal(int: 5)
```

### `Atribuicao`

Atribuicao a variavel existente.

```python
@dataclass
class Atribuicao:
    nome: str
    valor: Any
    linha: int = 0
```

```
x = x + 1;
=>
Atribuicao(x =)
  BinOp(+)
    Identificador(x)
    Literal(int: 1)
```

### `ComandoRobo`

Comandos do robo: `mover`, `girar`, `parar`, `pegar`, `soltar`, `esperar`.

```python
@dataclass
class ComandoRobo:
    acao: str
    direcao: Optional[str] = None
    expressao: Optional[Any] = None
    unidade: Optional[str] = None  # "cm" ou "graus"
    linha: int = 0
```

```
mover frente 5 cm;
=>
ComandoRobo(mover frente cm)
  Literal(int: 5)
```

Para `parar`, apenas `acao="parar"` com todos opcionais `None`.

### `Se`

Condicional.

```python
@dataclass
class Se:
    condicao: Any
    bloco_entao: List[Any]
    bloco_senao: Optional[List[Any]] = None
    linha: int = 0
```

`bloco_senao` pode conter:
- Uma lista de instrucoes (`else { ... }`)
- Uma lista com um unico `Se` (`else if`)

### `Enquanto`

Laco com condicao.

```python
@dataclass
class Enquanto:
    condicao: Any
    bloco: List[Any]
    linha: int = 0
```

### `Repita`

Laco com contagem fixa.

```python
@dataclass
class Repita:
    vezes: Any       # expressao que produz o numero de iteracoes
    bloco: List[Any]
    linha: int = 0
```

### `FuncaoDef`

Definicao de funcao.

```python
@dataclass
class FuncaoDef:
    nome: str
    parametros: List[tuple]  # [(tipo, nome), ...]
    bloco: List[Any]
    linha: int = 0
```

```
func dobro(int n) { retorno n * 2; }
=>
FuncaoDef(dobro(int n))
  Retorno
    BinOp(*)
      Identificador(n)
      Literal(int: 2)
```

### `Imprimir`

Comando de saida.

```python
@dataclass
class Imprimir:
    expressoes: List[Any]
    linha: int = 0
```

### `Ler`

Leitura do sensor.

```python
@dataclass
class Ler:
    nome: str
    linha: int = 0
```

### `Retorno`

Retorno de funcao.

```python
@dataclass
class Retorno:
    valor: Any
    linha: int = 0
```

### `Programa`

Raiz da arvore, contendo todas as instrucoes.

```python
@dataclass
class Programa:
    instrucoes: List[Any] = field(default_factory=list)
```

## Impressao da AST

A funcao `ast_to_string(node)` formata a arvore como texto identado para
depuracao. Usada pelo subcomando `ast` do CLI.

```
Programa
  Declaracao(tipo=int, nome=velocidade)
    Literal(int: 5)
  Declaracao(tipo=texto, nome=nome)
    Literal(texto: 'Robo01')
  Imprimir
    Literal(texto: 'Iniciando robo:')
    Identificador(nome)
  ComandoRobo(mover frente cm)
    Literal(int: 5)
  ComandoRobo(parar)
```

Uso:
```bash
python3 roboscript.py ast examples/exemplo1.robo
```

## Locais Importantes no Codigo

- `roboscript/ast_nodes.py:8-145` - todas as definicoes de no
- `roboscript/ast_nodes.py:148` - `ast_to_string()` (formatacao para debug)
