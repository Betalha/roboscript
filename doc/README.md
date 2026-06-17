# Documentacao do RoboScript

Esta pasta contem a documentacao tecnica completa do projeto **RoboScript** -
um executor de linguagem com visualizacao ASCII para robos simples, baseado na
especificacao do PDF `RoboScript_Trabalho.pdf` (Teoria dos Compiladores).

## Indice

| # | Documento | Descricao |
|---|-----------|-----------|
| 01 | [Visao Geral](01-visao-geral.md) | Arquitetura, fluxo geral e estrutura de diretorios |
| 02 | [Especificacao da Linguagem](02-linguagem.md) | Sintaxe completa do RoboScript |
| 03 | [Lexer](03-lexer.md) | Analise lexica - como o codigo vira tokens |
| 04 | [Parser](04-parser.md) | Analise sintatica - como tokens viram AST |
| 05 | [AST](05-ast.md) | Estrutura e nos da arvore sintatica abstrata |
| 06 | [Interpretador](06-interpreter.md) | Avaliacao da AST e execucao do programa |
| 07 | [Mundo Simulado](07-world.md) | Estado do robo, sensor e diretivas |
| 08 | [Visualizador ASCII](08-visualizer.md) | Renderizacao da grade no terminal |
| 09 | [CLI](09-cli.md) | Subcomandos `run`, `tokens`, `ast`, `check`, `repl` |
| 10 | [REPL](10-repl.md) | Shell interativo: meta-comandos, completion, multi-linha |
| 11 | [Testes](11-testes.md) | Suite de testes (42 testes) |
| 12 | [Fluxo de Execucao](12-fluxo-execucao.md) | End-to-end: codigo-fonte ate animacao |
| 13 | [Estendendo a Linguagem](13-extensao.md) | Como adicionar novos comandos ou recursos |

## Como Ler

Se voce eh **novo no projeto**, siga em ordem: 01 -> 02 -> 12 -> demais.

Se quer **modificar o codigo**, leia o documento da camada que vai mexer:
- Adicionar palavra-chave: 03 (lexer) + 04 (parser)
- Novo comando do robo: 04 (parser) + 06 (interpretador) + 07 (world)
- Novo simbolo na grade: 08 (visualizer)
- Novo meta-comando: 10 (REPL)

## Arquivos do Codigo Documentados

```
roboscript_proj/
├── roboscript.py              -> doc/09-cli.md
├── roboscript/
│   ├── errors.py              -> doc/03-lexer.md e doc/06-interpreter.md
│   ├── lexer.py               -> doc/03-lexer.md
│   ├── parser.py              -> doc/04-parser.md
│   ├── ast_nodes.py           -> doc/05-ast.md
│   ├── interpreter.py         -> doc/06-interpreter.md
│   ├── world.py               -> doc/07-world.md
│   ├── visualizer.py          -> doc/08-visualizer.md
│   └── repl.py                -> doc/10-repl.md
├── tests/                     -> doc/11-testes.md
└── examples/*.robo            -> doc/02-linguagem.md
```
