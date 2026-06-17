# 11 - Suite de Testes

**Arquivo:** `tests/`

## Visao Geral

42 testes automatizados distribuidos em 5 arquivos, todos usando `unittest` da
stdlib. Zero dependencias externas.

```bash
python3 -m unittest discover tests -v
# Ran 42 tests in 0.006s
# OK
```

## Estrutura

```
tests/
├── __init__.py
├── test_lexer.py          # 9 testes
├── test_parser.py         # 7 testes
├── test_interpreter.py    # 10 testes
├── test_errors.py         # 2 testes
└── test_repl.py           # 14 testes
```

## `test_lexer.py` (9 testes)

Cobre todos os aspectos da Etapa 2 do PDF:

| Teste | O que verifica |
|-------|---------------|
| `test_palavras_reservadas` | `mover` -> PALAVRA_CHAVE, nao IDENTIFICADOR |
| `test_identificador_simples` | `movimento` -> IDENTIFICADOR (nao eh reservada) |
| `test_operadores_relacionais` | `== != >= <= > <` todos reconhecidos |
| `test_string_com_escape` | `\n` dentro de string vira quebra de linha |
| `test_comentarios_descartados` | `# texto\n mover` so tem o token `mover` |
| `test_comentario_bloco` | `/* ... */` descartado |
| `test_erro_identificador_iniciando_com_digito` | `2robo` dispara RoboLexError |
| `test_numero_decimal` | `3.14` -> NUMERO_DECIMAL com valor float |
| `test_delimitadores` | `( ) { } , ; :` todos reconhecidos |

## `test_parser.py` (7 testes)

Cobre a gramatica da Etapa 3 do PDF:

| Teste | O que verifica |
|-------|---------------|
| `test_declaracao_simples` | `int x = 5` produz nó `Declaracao` |
| `test_comando_mover` | `mover frente 10 cm` produz `ComandoRobo` |
| `test_condicional_com_senao` | `se (x < 10) { } senao { }` produz `Se` |
| `test_funcao_definicao_e_chamada` | `func soma(int a, int b) { } int r = soma(1,2);` |
| `test_erro_falta_direcao_em_mover` | `mover 10 cm;` lanca RoboSyntaxError com mensagem do PDF |
| `test_precedencia_operadores` | `1 + 2 * 3` arvore: BinOp(+, 1, BinOp(*, 2, 3)) |
| `test_repita_vezes` | `repita 3 vezes { }` produz nó `Repita` |

## `test_interpreter.py` (10 testes)

Cobre a execucao runtime:

| Teste | O que verifica |
|-------|---------------|
| `test_imprimir_simples` | `imprimir("ola")` -> output `["ola"]` |
| `test_mover_atualiza_posicao` | mover 3 cm leste -> x incrementa 3 |
| `test_girar` | girar 90 direita -> direcao vira Leste |
| `test_repita` | repita 4 vezes mover 1 cm -> x=4 |
| `test_funcao_retorno` | `dobro(7)` -> `14` |
| `test_se_senao` | `x > 5` -> imprime "maior" |
| `test_obstaculo_bloqueia_movimento` | obstaculo em x=3, robo em x=0, move 10 -> para em x=2 |
| `test_sensor_distancia` | obstaculo em x=4, robo em x=0 -> ler retorna 3 |
| `test_pegar_objeto` | objeto na mesma celula -> carregando = True |
| `test_exemplos_pdf_executam_sem_erro` | carrega e executa os 3 exemplos validos sem excecao |

## `test_errors.py` (2 testes)

Validacao que as mensagens de erro **batem exatamente** com as descritas
no PDF (Etapa 4, exemplos Invalidos 1 e 2):

```python
def test_invalido1_mover_sem_direcao(self):
    # Verifica string contem: "esperada direcao", "'frente'", "'10'", etc.
    with self.assertRaises(RoboSyntaxError) as ctx:
        parse(tokenize("mover 10 cm;"))
    msg = str(ctx.exception)
    self.assertIn("[Linha 1]", msg)
    self.assertIn("Erro sintatico", msg)
    self.assertIn("esperada direcao", msg)

def test_invalido2_identificador_iniciado_com_digito(self):
    # Verifica "identificador nao pode comecar com digito -- encontrado '2robo'"
```

## `test_repl.py` (14 testes)

Cobre o shell interativo via simulacao de entrada com `io.StringIO`:

| Teste | O que verifica |
|-------|---------------|
| `test_help_e_quit` | `:help` mostra texto; `:q` sai |
| `test_declaracao_sem_ponto_virgula` | `int x = 5` sem `;` funciona |
| `test_expressao_pura_imprime_resultado` | `2 + 3` -> `=> 5` |
| `test_comando_mover` | mover atualiza world.x |
| `test_vars_meta_comando` | `:vars` mostra variaveis declaradas |
| `test_funcao_multilinha` | funcao `dobro` definida e chamada |
| `test_erro_nao_derruba_repl` | sintaxe errada nao interrompe; comando seguinte ainda funciona |
| `test_reset_limpa_estado` | `:reset` zera variaveis |
| `test_obstaculo_meta` | `:obstaculo 7,5` adiciona ao mundo |
| `test_teleport` | `:teleport 10,3` move robo |
| `test_load_arquivo` | `:load exemplo1.robo` carrega e executa |
| `test_meta_desconhecido` | `:naoexiste` mostra erro |
| `test_tokens_meta` | `:tokens mover frente 5 cm` mostra tipos dos tokens |
| `test_normalizacao_auto_semicolon` | `int x = 5` seguido de `x = x + 10` produz x=15 |

## Como Rodar

```bash
# Todos os testes
python3 -m unittest discover tests -v

# Um arquivo especifico
python3 -m unittest tests.test_lexer -v

# Um teste especifico
python3 -m unittest tests.test_lexer.TestLexer.test_palavras_reservadas
```

## Cobertura

Cada camada do pipeline tem testes:

```
Lexer  ---- 9 testes ----> tokens corretos + erros lexicos
Parser ---- 7 testes ----> AST correta + erros sintaticos
Interp  --- 10 testes ---> execucao correta + erros runtime
Erros   --- 2 testes ----> mensagens batem com PDF
REPL    --- 14 testes ---> comandos, meta, persistencia, erros
```
