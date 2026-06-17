# 12 - Fluxo de Execucao (End-to-End)

Este documento mostra o caminho completo de um programa RoboScript, desde o
arquivo `.robo` ate a animacao no terminal, usando `exemplo1.robo` como exemplo.

## Codigo Fonte

```python
# @mundo 20x10
# @inicio 5,8
# @direcao norte

int velocidade = 5;
texto nome = "Robo01";
imprimir("Iniciando robo:", nome);
mover frente 5 cm;
parar;
```

## Etapa 1: Leitura do Arquivo

**Onde:** `roboscript.py:14` (`_ler_arquivo()`)

O CLI le o arquivo como string UTF-8. Mundo e diretivas sao lidas antes do
lexer executar.

## Etapa 2: Construcao do Mundo

**Onde:** `roboscript/world.py:160` (`build_world()`)

A funcao `build_world(fonte)` extrai as diretivas `# @`:

```python
cfg = parse_diretivas(fonte)
# cfg = {
#   "largura": 20, "altura": 10,
#   "x": 5, "y": 8,
#   "direcao": 0,  # norte
#   "obstaculos": [],
#   "objetos": [],
# }
World(largura=20, altura=10, x=5, y=8, direcao=0)
```

O mundo eh criado **antes** do lexer/parser porque o interpretador precisa
dele para callbacks de animacao.

## Etapa 3: Analise Lexica

**Onde:** `roboscript/lexer.py:62` (`Lexer.tokenize()`)

O lexer percorre o texto caractere por caractere e produz:

```python
tokens = tokenize(fonte)
# [
#   Token(PALAVRA_CHAVE, "int"),
#   Token(IDENTIFICADOR, "velocidade"),
#   Token(OP_ATRIB, "="),
#   Token(NUMERO_INTEIRO, 5),
#   Token(DELIMITADOR, ";"),
#   Token(PALAVRA_CHAVE, "texto"),
#   Token(IDENTIFICADOR, "nome"),
#   Token(OP_ATRIB, "="),
#   Token(STRING, "Robo01"),
#   Token(DELIMITADOR, ";"),
#   ... (imprimir, mover, parar)
#   Token(EOF, ...)
# ]
```

Comentarios `# ...` e `/* ... */` sao descartados neste passo.

## Etapa 4: Analise Sintatica

**Onde:** `roboscript/parser.py:40` (`Parser.parse()`)

O parser recursivo-descendente consome os tokens e constroi a AST:

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

Cada no eh uma instancia de `@dataclass` definida em `ast_nodes.py`.

## Etapa 5: Execucao (Interpretacao)

**Onde:** `roboscript/interpreter.py:76` (`Interpreter.run()`)

### Passo 5a: Registro de funcoes

O interpretador varre a AST em busca de `FuncaoDef` e as registra em
`self.funcoes`. No exemplo1 nao ha funcoes, entao este passo eh vazio.

### Passo 5b: Execucao sequencial

Cada instrucao (que nao seja `FuncaoDef`) eh executada em ordem:

1. **`int velocidade = 5`** (_Declaracao_):
   - Avalia a expressao `5` -> `Literal(int: 5)` -> valor `5`
   - Chama `self.global_env.declare("velocidade", "int", 5, linha)`
   - Ambiente global: `{ velocidade: 5 }`

2. **`texto nome = "Robo01"`** (_Declaracao_):
   - Avalia `"Robo01"` -> `Literal(texto: 'Robo01')` -> valor `"Robo01"`
   - `global_env.declare("nome", "texto", "Robo01", linha)`
   - Ambiente: `{ velocidade: 5, nome: "Robo01" }`

3. **`imprimir("Iniciando robo:", nome)`**:
   - Avalia primeiro argumento: `"Iniciando robo:"` -> string
   - Avalia segundo argumento: `nome` -> busca no env -> `"Robo01"`
   - Concatena: `"Iniciando robo: Robo01"`
   - Adiciona a `self.output` e chama `self._step("imprimir: ...")`
   - `_step()` aciona `on_step(world)` -> `render(world)` (animacao)

4. **`mover frente 5 cm`** (_ComandoRobo_):
   - Avalia `5` -> 5 as celulas
   - Chama `world.mover("frente", 5)`:
     - Calcula delta: `direcao_apos_movimento("frente")` -> norte -> delta(0, -1)
     - Loop de 5 iteracoes: `y -= 1` a cada passo
     - Nenhum obstaculo atrapalha, entao move 5 celulas
     - `world.x = 5, world.y = 3` (de y=8 para y=3)
     - `world.trilha` recebe 5 novas entradas
   - `_step("mover frente 5 cm")` -> renderiza grade

5. **`parar`**:
   - Apenas registra `_step("parar")` -> renderiza

### Estado final apos execucao

```
World:
  Posicao: (5, 3)
  Direcao: Norte
  Trilha: [(5,8), (5,7), ..., (5,3)]
  Acao: "parar"

Interpreter:
  output: ["Iniciando robo: Robo01"]
```

## Etapa 6: Renderizacao (a cada passo)

**Onde:** `roboscript/visualizer.py:10`

A cada `_step()`, a funcao `render()` eh chamada:

```python
def on_step(w):
    render(w, animado=animado)
```

1. Limpa a tela (se animado): `\033[2J\033[H`
2. Constroi matriz de caracteres 10x20 com `"."`
3. Desenha elementos na ordem: trilha -> objetos -> obstaculos -> robo
4. Imprime moldura com `+---+`
5. Imprime painel informativo

A animacao produz uma sequencia como:

```
Frame 1 (inicio): robo no centro (5,8), sem trilha
Frame 2 (imprimir): mesmo, sem movimento
Frame 3 (mover): trilha descendo ate (5,3), robo no topo
Frame 4 (parar): estado final
```

## Resumo do Fluxo

```
[.robo] --> 1. leitura do arquivo
                |
                +---> 2. build_world() -> World
                |
                +---> 3. tokenize() -> Tokens
                             |
                             v
                          4. parse() -> AST
                             |
                             v
                          5. interpreter.run(AST)
                             |
                             +---> para cada instrucao:
                                          |
                                          +-> _exec(node, env)
                                          +-> world.alterado
                                          +-> _step() -> render()
```

## Exemplo de Saida Visual

```
+--------------------+
|....................|
|....................|
|....................|
|.....^..............|
|.....+..............|
|.....+..............|
|.....+..............|
|.....+..............|
|.....+..............|
|....................|
+--------------------+
Pos: (5,3) | Dir: Norte | Carregando: nao
Sensor (ultima leitura): -
Acao: parar
Legenda: ^>v< robo  # obstaculo  O objeto  + trilha  . vazio

--- Saida do programa ---
Iniciando robo: Robo01
```
