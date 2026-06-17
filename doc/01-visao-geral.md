# 01 - Visao Geral

## Proposito

O **RoboScript** eh uma implementacao completa de um compilador/interpretador para
a linguagem de mesmo nome descrita no PDF do trabalho de Teoria dos Compiladores.
A linguagem permite programar robos simples em ambientes 2D usando sintaxe inspirada
em Logo, Python e Arduino, em portugues.

O projeto inclui:

1. **Front-end completo** (analise lexica + sintatica) que valida codigo segundo
   a especificacao formal do PDF
2. **Interpretador tree-walking** que executa programas direto da AST
3. **Mundo simulado** em grade 2D com obstaculos, objetos e sensor
4. **Visualizador ASCII** com animacao via codigos ANSI
5. **CLI completo** com subcomandos para cada fase do processamento
6. **REPL interativo** com tab completion, historico e meta-comandos
7. **Suite de 42 testes** automatizados

## Pipeline de Execucao

```
+----------------+
| codigo.robo    |   <-- arquivo texto UTF-8
+--------+-------+
         |
         v
+----------------+
|     LEXER      |   roboscript/lexer.py
+--------+-------+   converte texto em lista de Token
         |
         v   [Token(PALAVRA_CHAVE, "mover"), Token(NUMERO, 5), ...]
+----------------+
|     PARSER     |   roboscript/parser.py
+--------+-------+   constroi AST seguindo a EBNF
         |
         v   ComandoRobo(acao="mover", direcao="frente", expressao=Literal(5))
+----------------+
|  INTERPRETER   |   roboscript/interpreter.py
+--------+-------+   percorre AST e atualiza estado
         |
         v
+----------------+    +----------------+
|     WORLD      |--->|   VISUALIZER   |   tela ASCII
+----------------+    +----------------+
```

## Estrutura de Diretorios

```
roboscript_proj/
|
|-- README.md                  -- documentacao de uso
|-- roboscript.py              -- entry-point CLI (argparse + dispatch)
|
|-- roboscript/                -- pacote principal
|   |-- __init__.py            -- versao e exports
|   |-- errors.py              -- hierarquia de excecoes
|   |-- lexer.py               -- tokenizador
|   |-- parser.py              -- parser recursivo-descendente
|   |-- ast_nodes.py           -- @dataclasses dos nos da AST
|   |-- interpreter.py         -- avaliador tree-walking
|   |-- world.py               -- estado do mundo + sensor + diretivas
|   |-- visualizer.py          -- render ASCII com ANSI
|   `-- repl.py                -- shell interativo
|
|-- examples/                  -- programas de exemplo
|   |-- exemplo1.robo          -- declaracao + imprimir + mover
|   |-- exemplo2.robo          -- condicional + repeticao + sensor
|   |-- exemplo3.robo          -- funcoes + patrulha + objetos
|   |-- invalido1.robo         -- erro sintatico (mover sem direcao)
|   `-- invalido2.robo         -- erro lexico (id comeca com digito)
|
|-- tests/                     -- unittest
|   |-- test_lexer.py          -- 9 testes
|   |-- test_parser.py         -- 7 testes
|   |-- test_interpreter.py    -- 10 testes
|   |-- test_errors.py         -- 2 testes (mensagens batem com PDF)
|   `-- test_repl.py           -- 14 testes
|
`-- doc/                       -- esta documentacao
```

## Dependencias

- **Python 3.7+** (usa `@dataclass`, `typing`)
- **Apenas stdlib** - nenhum `pip install`
- `readline` (Linux/macOS) eh opcional para historico/completion no REPL

## Filosofia de Design

### 1. Aderencia ao PDF
Cada token, regra de gramatica e mensagem de erro foi implementada conforme a
especificacao do PDF. Isso eh garantido pela suite de testes (em particular
`tests/test_errors.py` que valida as mensagens exatas).

### 2. Camadas isoladas
Cada modulo tem uma responsabilidade unica:
- `lexer.py` so produz tokens; nao conhece sintaxe
- `parser.py` so consome tokens e produz AST; nao executa
- `interpreter.py` so executa AST; nao conhece tokens
- `world.py` so gerencia estado; nao sabe renderizar
- `visualizer.py` so desenha; nao executa nada
- `repl.py` orquestra mas reusa todos os anteriores

Isso permite testar cada camada em isolamento e substituir uma sem afetar as
outras (ex: trocar visualizer ASCII por uma versao com cores ou GUI).

### 3. Erros consistentes
Toda excecao herda de `RoboError` e tem o formato `[Linha N] <Tipo>: <mensagem>`.
Isso facilita captura uniforme no CLI e no REPL.

### 4. Estado explicito
O estado do robo vive em uma instancia de `World` separada do `Interpreter`. O
mesmo World pode ser passado para multiplos interpretadores (ex: no REPL ele
persiste entre comandos).

## Conceitos-Chave

| Conceito | Onde vive | Resumo |
|----------|-----------|--------|
| **Token** | `lexer.py` | Unidade lexical: tipo + lexema + valor + linha/coluna |
| **AST** | `ast_nodes.py` | Arvore de nos dataclass representando o programa |
| **Environment** | `interpreter.py` | Tabela de simbolos encadeada (escopo) |
| **World** | `world.py` | Estado fisico do robo (x, y, direcao, obstaculos, ...) |
| **Diretiva** | `world.py` | Comentario `# @chave valor` que configura o mundo |
| **Sensor** | `world.py` | `sensor_distancia()` retorna celulas livres a frente |
| **Frame** | `visualizer.py` | Renderizacao ASCII de um estado do World |
| **Meta-comando** | `repl.py` | Comando do REPL prefixado com `:` (ex: `:vars`) |

## Proximos Passos

- Leia `02-linguagem.md` para conhecer a sintaxe completa
- Leia `12-fluxo-execucao.md` para acompanhar um programa do inicio ao fim
- Cada modulo tem seu proprio documento com explicacao detalhada
