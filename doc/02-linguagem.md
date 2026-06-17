# 02 - Especificacao da Linguagem RoboScript

Este documento espelha a especificacao do PDF e mostra exemplos praticos. Para
detalhes de implementacao do lexer/parser, veja `03-lexer.md` e `04-parser.md`.

## Tipos Primitivos

| Tipo | Valores | Default | Exemplo |
|------|---------|---------|---------|
| `int` | inteiros | `0` | `int x = 5;` |
| `float` | reais com `.` | `0.0` | `float v = 3.14;` |
| `texto` | strings entre `"..."` | `""` | `texto s = "ola";` |
| `bool` | `verdade`, `falso` | `falso` | `bool ok = verdade;` |

## Identificadores

Regra (do PDF):
```
IDENTIFICADOR ::= LETRA (LETRA | DIGITO | "_")*
```
Devem comecar com letra e podem conter letras, digitos e `_`.

Validos: `velocidade`, `i`, `_temp` (na verdade `_` no inicio NAO eh permitido
pela regra), `posicao_x`, `robo1`

Invalido: `2robo` (comeca com digito), `mover` (palavra reservada)

## Palavras Reservadas (28)

```
mover    girar    parar    pegar    soltar   esperar  sensor
se       senao    enquanto repita   vezes
func     retorno  imprimir ler
int      float    texto    bool     verdade  falso
frente   tras     esquerda direita  graus    cm
```

## Literais

```
int x  = 42;
int n  = -10;            # operador unario '-'
float p = 3.14;
texto s = "Robo01";
texto e = "linha1\nlinha2";   # escapes: \n \t \" \\
bool ok = verdade;
bool no = falso;
```

## Operadores e Precedencia (do menor para o maior)

| Nivel | Operadores | Tipo |
|-------|-----------|------|
| 1 | `or` | logico |
| 2 | `and` | logico |
| 3 | `not` | logico (unario) |
| 4 | `==` `!=` `>` `<` `>=` `<=` | relacional |
| 5 | `+` `-` | aritmetico binario |
| 6 | `*` `/` | aritmetico |
| 7 | `-` (unario) | aritmetico |
| 8 | `()` | agrupamento |

Exemplo:
```
int r = 1 + 2 * 3;             # 7 (multiplicacao primeiro)
bool ok = x > 0 and x < 10;    # comparacao antes do 'and'
bool y = not (a or b);
```

## Comentarios

```
# comentario de linha
/* comentario
   em bloco
   de varias linhas */
```

Comentarios sao descartados pelo lexer. Excecao: linhas comecando com `# @` no
inicio do arquivo sao **diretivas** lidas pelo runtime (veja `07-world.md`).

## Declaracao e Atribuicao

```
int x = 5;                # declaracao com inicializacao
int y;                    # declaracao -- valor padrao do tipo
texto nome = "Bot";

x = x + 1;                # atribuicao (variavel ja declarada)
nome = "Robo2";
```

A linguagem eh **estaticamente tipada** com checagem em runtime: passar `texto`
onde se espera `int` gera erro.

## Comandos do Robo

### `mover <direcao> <expressao> cm`

Move o robo `N` celulas na direcao indicada (relativa a orientacao atual).
Direcoes: `frente`, `tras`, `esquerda`, `direita`.
```
mover frente 5 cm;
mover tras 2 cm;
mover esquerda 3 cm;      # vai para o lado esquerdo do robo
```

### `girar <direcao> <expressao> graus`

Roda o robo. Direcoes uteis: `direita`, `esquerda`.
```
girar direita 90 graus;
girar esquerda 180 graus;
```

Internamente, a orientacao eh normalizada para multiplos de 90 (norte/leste/sul/oeste).

### `parar` / `pegar` / `soltar` / `esperar`

```
parar;                    # registra "parar" no log; nao halta o programa
pegar;                    # pega objeto na celula atual (se houver)
soltar;                   # deposita objeto sendo carregado
esperar 2;                # pausa N "unidades de tempo" (animacao)
```

## Condicional `se ... senao`

```
se (distancia < 10) {
    girar direita 90 graus;
}

se (x > 0) {
    imprimir("positivo");
} senao {
    imprimir("nao positivo");
}

# encadeamento (senao se)
se (n == 0) {
    imprimir("zero");
} senao se (n > 0) {
    imprimir("positivo");
} senao {
    imprimir("negativo");
}
```

## Repeticao

### `enquanto`
```
int i = 0;
enquanto (i < 10) {
    mover frente 1 cm;
    i = i + 1;
}
```

### `repita N vezes`
```
repita 5 vezes {
    girar direita 90 graus;
    mover frente 2 cm;
}
```

## Funcoes

```
func dobro(int n) {
    retorno n * 2;
}

func saudar(texto nome) {
    imprimir("Ola, ", nome);
}

# chamada
int r = dobro(7);            # r = 14
saudar("Robo01");
```

- Parametros sao tipados
- `retorno expressao;` interrompe a funcao e devolve o valor
- Funcoes sem `retorno` retornam `(nulo)`
- Funcoes podem se chamar recursivamente

## Entrada/Saida

### `imprimir(expr1, expr2, ...)`
```
imprimir("velocidade:", velocidade);
imprimir(x + y);
```
Cada argumento eh formatado e separados por espaco.

### `ler(variavel)`
Atribui a `variavel` a **leitura do sensor**: distancia em celulas ate o proximo
obstaculo (ou borda) na direcao atual do robo.
```
int dist = 0;
ler(dist);
imprimir("livre:", dist);
```

A variavel **deve existir** antes do `ler`.

## Diretivas de Mundo (extensao)

Linhas de comentario que comecam com `# @` configuram o mundo. Sao lidas pelo
runtime mas ignoradas pelo lexer (sao apenas comentarios da linguagem).

```
# @mundo 30x20            largura x altura da grade
# @inicio 5,10            posicao inicial (x, y)
# @direcao norte          norte | leste | sul | oeste
# @obstaculo 10,7         celula com obstaculo
# @objeto 14,7            celula com objeto pegavel
```

## Programa Completo

```
# @mundo 25x15
# @inicio 2,12
# @direcao leste
# @obstaculo 8,12

int tentativas = 5;
int distancia = 0;

repita tentativas vezes {
    ler(distancia);
    se (distancia < 5) {
        girar direita 90 graus;
        mover frente 3 cm;
    } senao {
        mover frente 4 cm;
    }
}
parar;
imprimir("Missao concluida.");
```

## Gramatica EBNF (resumo)

```
programa     ::= { instrucao }
instrucao    ::= declaracao ";"
              | atribuicao ";"
              | comando_robo ";"
              | condicional
              | repeticao
              | funcao_def
              | entrada_saida ";"
              | retorno ";"

declaracao   ::= tipo IDENTIFICADOR [ "=" expressao ]
atribuicao   ::= IDENTIFICADOR "=" expressao
comando_robo ::= "mover" direcao expressao "cm"
              | "girar" direcao expressao "graus"
              | "parar" | "pegar" | "soltar"
              | "esperar" expressao

condicional  ::= "se" "(" expressao ")" bloco [ "senao" (bloco | condicional) ]
bloco        ::= "{" { instrucao } "}"
repeticao    ::= "enquanto" "(" expressao ")" bloco
              | "repita" expressao "vezes" bloco
funcao_def   ::= "func" IDENTIFICADOR "(" [ parametros ] ")" bloco
parametros   ::= tipo IDENTIFICADOR { "," tipo IDENTIFICADOR }

expressao    ::= expressao_ou
expressao_ou ::= expressao_e { "or" expressao_e }
expressao_e  ::= expressao_nao { "and" expressao_nao }
expressao_nao::= "not" expressao_nao | expressao_relacional
expressao_relacional ::= expressao_adit [ OP_RELACIONAL expressao_adit ]
expressao_adit  ::= expressao_mult { ("+"|"-") expressao_mult }
expressao_mult  ::= expressao_unaria { ("*"|"/") expressao_unaria }
expressao_unaria::= "-" expressao_unaria | primario
primario     ::= NUMERO | STRING | "verdade" | "falso"
              | IDENTIFICADOR | funcao_chamada
              | "(" expressao ")"

direcao      ::= "frente" | "tras" | "esquerda" | "direita"
tipo         ::= "int" | "float" | "texto" | "bool"
```

A implementacao completa esta em `04-parser.md`.
