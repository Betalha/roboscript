# RoboScript - Executor com Visualizacao ASCII

Implementacao em Python 3 (apenas stdlib) da linguagem **RoboScript** especificada
no PDF `RoboScript_Trabalho.pdf` (Trabalho Pratico de Teoria dos Compiladores).

Inclui:
- Lexer conforme Etapa 2 do PDF
- Parser recursivo-descendente conforme EBNF da Etapa 3
- Interpretador tree-walking
- Visualizacao ASCII animada do robo no terminal
- **REPL interativo** com tab completion e historico
- Suite de testes (42 testes) cobrindo lexico, sintatico, runtime, REPL e os 5 exemplos do PDF

## Requisitos
- Python 3.7+
- Terminal compativel com ANSI (Linux/macOS/WSL/Windows Terminal)

## Estrutura
```
roboscript_proj/
├── roboscript.py            # CLI entry-point
├── roboscript/
│   ├── lexer.py             # Tokenizador (Etapa 2)
│   ├── parser.py            # Parser EBNF (Etapa 3)
│   ├── ast_nodes.py         # Nos da AST
│   ├── interpreter.py       # Tree-walking interpreter
│   ├── world.py             # Mundo simulado + sensor + diretivas
│   ├── visualizer.py        # Render ASCII com ANSI
│   ├── repl.py              # Shell interativo
│   └── errors.py            # Excecoes
├── examples/
│   ├── exemplo1.robo        # Exemplos do PDF
│   ├── exemplo2.robo
│   ├── exemplo3.robo
│   ├── invalido1.robo       # Casos invalidos do PDF
│   └── invalido2.robo
└── tests/                   # Testes unittest
```

## Uso

```bash
# Shell interativo (REPL) - digite comandos linha a linha
python3 roboscript.py repl

# REPL pre-carregando um arquivo (variaveis/funcoes ja disponiveis)
python3 roboscript.py repl --load examples/exemplo3.robo

# REPL com grade customizada
python3 roboscript.py repl --grid 40x15

# Executa um programa com animacao no terminal
python3 roboscript.py run examples/exemplo3.robo

# Executa sem animacao (mostra cada frame em sequencia)
python3 roboscript.py run examples/exemplo3.robo --no-anim

# Controla velocidade da animacao (segundos entre passos)
python3 roboscript.py run examples/exemplo2.robo --speed 0.4

# Lista tokens (formato da Etapa 4 do PDF)
python3 roboscript.py tokens examples/exemplo1.robo

# Imprime AST em forma de arvore
python3 roboscript.py ast examples/exemplo1.robo

# Apenas valida lexico+sintatico
python3 roboscript.py check examples/exemplo2.robo
```

## Modo Interativo (REPL)

O REPL abre um shell onde voce escreve codigo RoboScript linha a linha e ve o
robo responder. O estado (variaveis, funcoes, posicao do robo, obstaculos)
persiste entre comandos.

```
$ python3 roboscript.py repl
RoboScript REPL v1.0 - digite :help para ajuda, :q para sair

+------------------------------+
|..............................|
|...............^..............|
|..............................|
+------------------------------+
Pos: (15,10) | Dir: Norte | Carregando: nao
Vars:  (vazio)
Funcs: (vazio)

robo> int v = 5            # ';' eh opcional no REPL
robo> mover frente v cm
robo> 2 * v + 1
=> 11
robo> func dobro(int n) {
....>   retorno n * 2;
....> }
robo> dobro(7)
=> 14
robo> :obstaculo 15,3      # adiciona obstaculo em tempo real
robo> int d = 0
robo> ler(d)
robo> d
=> 6
robo> :q
```

### Recursos do REPL

- **Auto `;`**: voce nao precisa colocar `;` ao final de cada comando
- **Expressoes nuas**: digite `2 + 3` e o REPL imprime `=> 5`
- **Blocos multi-linha**: `func`, `se`, `enquanto`, `repita` sao detectados
  automaticamente; o prompt vira `....>` ate fechar todas as `{`
- **Historico persistente**: setas ↑/↓ navegam comandos passados
  (salvos em `~/.roboscript_history`)
- **Tab completion**: completa palavras-chave, variaveis declaradas, funcoes
  definidas e meta-comandos
- **Erros nao matam o REPL**: mensagem em vermelho e voce continua

### Meta-comandos do REPL

| Comando | Funcao |
|---|---|
| `:help`, `:h` | Lista todos os comandos |
| `:vars`, `:v` | Lista variaveis no escopo global |
| `:funcs`, `:f` | Lista funcoes definidas |
| `:world` | Mostra estado completo do mundo |
| `:reset` | Reinicia tudo (variaveis, funcoes, mundo) |
| `:obstaculo X,Y` | Adiciona obstaculo na celula (X,Y) |
| `:objeto X,Y` | Adiciona objeto pegavel |
| `:rm X,Y` | Remove obstaculo/objeto |
| `:teleport X,Y` | Move o robo instantaneamente |
| `:speed N` | Ajusta delay da animacao |
| `:load arquivo.robo` | Carrega e executa um arquivo |
| `:tokens <codigo>` | Mostra tokens da linha sem executar |
| `:ast <codigo>` | Mostra AST sem executar |
| `:redraw` | Redesenha a grade |
| `:clear` | Limpa o terminal |
| `:mode tela\|log` | Alterna entre tela cheia e log incremental |
| `:quit`, `:q` | Sai (Ctrl+D tambem) |

## Configurando o Mundo (diretivas em comentarios)

O programa pode definir seu mundo usando comentarios especiais. Eles sao lidos
pelo runtime e ignorados pelo lexer (sao apenas comentarios normais).

```
# @mundo 30x15           largura x altura
# @inicio 5,7            posicao inicial do robo (x,y)
# @direcao leste         norte | leste | sul | oeste
# @obstaculo 10,7        adiciona obstaculo na celula (10,7)
# @objeto 14,7           adiciona objeto pegavel
```

## Simbolos da Visualizacao

| Simbolo | Significado          |
|---------|----------------------|
| `^>v<`  | Robo (orientacao)    |
| `#`     | Obstaculo            |
| `O`     | Objeto (pegavel)     |
| `+`     | Trilha percorrida    |
| `.`     | Celula vazia         |

## Comandos da Linguagem (Etapa 3 do PDF)

- Declaracao: `int x = 5;` (tipos: `int`, `float`, `texto`, `bool`)
- Atribuicao: `x = x + 1;`
- Movimento: `mover frente|tras|esquerda|direita N cm;`
- Giro: `girar esquerda|direita N graus;`
- Comandos: `parar;` `pegar;` `soltar;` `esperar N;`
- Condicional: `se (cond) { ... } senao { ... }`
- Loops: `enquanto (cond) { ... }` / `repita N vezes { ... }`
- Funcoes: `func nome(int a, texto b) { ... retorno x; }`
- E/S: `imprimir(a, b, c);` `ler(var);` (ler retorna distancia do sensor)
- Comentarios: `# linha` ou `/* bloco */`
- Operadores: `==` `!=` `>` `<` `>=` `<=` `and` `or` `not` `+` `-` `*` `/`

## O Sensor `ler(var)`

A funcao `ler(var)` atribui a `var` a **distancia em celulas ate o proximo
obstaculo (ou borda) na direcao atual do robo**. Util para desviar de paredes.

## Mensagens de Erro

Conforme PDF, todas as mensagens seguem o formato:
```
[Linha N] Erro lexico|sintatico|de execucao: <descricao>
```

Exemplos:
```bash
$ python3 roboscript.py check examples/invalido1.robo
[Linha 2] Erro sintatico: esperada direcao ('frente', 'tras', 'esquerda' ou 'direita') apos 'mover', encontrado '10'

$ python3 roboscript.py check examples/invalido2.robo
[Linha 2] Erro lexico: identificador nao pode comecar com digito -- encontrado '2robo'
```

## Rodando os Testes

```bash
python3 -m unittest discover -v tests
```

