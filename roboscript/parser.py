"""Parser recursivo-descendente do RoboScript - Etapa 3 do PDF."""
from typing import List
from .lexer import Token
from .errors import RoboSyntaxError
from . import ast_nodes as ast


TIPOS = {"int", "float", "texto", "bool"}
DIRECOES = {"frente", "tras", "esquerda", "direita"}


class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    # ---- helpers ----
    def _atual(self) -> Token:
        return self.tokens[self.pos]

    def _avancar(self) -> Token:
        t = self.tokens[self.pos]
        if t.tipo != "EOF":
            self.pos += 1
        return t

    def _check(self, tipo: str, lexema: str = None) -> bool:
        t = self._atual()
        if t.tipo != tipo:
            return False
        if lexema is not None and t.lexema != lexema:
            return False
        return True

    def _match(self, tipo: str, lexema: str = None) -> bool:
        if self._check(tipo, lexema):
            self._avancar()
            return True
        return False

    def _esperar(self, tipo: str, lexema: str = None, msg: str = None) -> Token:
        if self._check(tipo, lexema):
            return self._avancar()
        t = self._atual()
        descricao = f"{lexema!r}" if lexema else tipo
        msg_final = msg or f"esperado {descricao}, encontrado {t.lexema!r}"
        raise RoboSyntaxError(t.linha, msg_final)

    # ---- entrada ----
    def parse(self) -> ast.Programa:
        instrucoes = []
        while not self._check("EOF"):
            instrucoes.append(self._instrucao())
        return ast.Programa(instrucoes=instrucoes)

    # ---- instrucoes ----
    def _instrucao(self):
        t = self._atual()

        # declaracao: comeca com tipo
        if t.tipo == "PALAVRA_CHAVE" and t.lexema in TIPOS:
            ins = self._declaracao()
            self._esperar("DELIMITADOR", ";", "esperado ';' apos declaracao")
            return ins

        # comandos do robo
        if t.tipo == "PALAVRA_CHAVE" and t.lexema in (
            "mover", "girar", "parar", "pegar", "soltar", "esperar"
        ):
            ins = self._comando_robo()
            self._esperar("DELIMITADOR", ";", "esperado ';' apos comando do robo")
            return ins

        if t.tipo == "PALAVRA_CHAVE" and t.lexema == "se":
            return self._condicional()

        if t.tipo == "PALAVRA_CHAVE" and t.lexema in ("enquanto", "repita"):
            return self._repeticao()

        if t.tipo == "PALAVRA_CHAVE" and t.lexema == "func":
            return self._funcao_def()

        if t.tipo == "PALAVRA_CHAVE" and t.lexema in ("imprimir", "ler"):
            ins = self._entrada_saida()
            self._esperar("DELIMITADOR", ";", "esperado ';' apos comando E/S")
            return ins

        if t.tipo == "PALAVRA_CHAVE" and t.lexema == "retorno":
            ins = self._retorno()
            self._esperar("DELIMITADOR", ";", "esperado ';' apos retorno")
            return ins

        # atribuicao: IDENT = expressao ;
        if t.tipo == "IDENTIFICADOR":
            # pode ser atribuicao ou chamada de funcao como instrucao
            prox = self.tokens[self.pos + 1] if self.pos + 1 < len(self.tokens) else None
            if prox and prox.tipo == "OP_ATRIB":
                ins = self._atribuicao()
                self._esperar("DELIMITADOR", ";", "esperado ';' apos atribuicao")
                return ins
            if prox and prox.tipo == "DELIMITADOR" and prox.lexema == "(":
                # chamada de funcao como statement
                chamada = self._primario()
                self._esperar("DELIMITADOR", ";", "esperado ';' apos chamada de funcao")
                return chamada

        raise RoboSyntaxError(t.linha, f"instrucao invalida iniciada por {t.lexema!r}")

    def _declaracao(self):
        tipo_tok = self._avancar()
        nome_tok = self._esperar("IDENTIFICADOR", msg="esperado nome de variavel apos tipo")
        valor = None
        if self._match("OP_ATRIB"):
            valor = self._expressao()
        return ast.Declaracao(tipo=tipo_tok.lexema, nome=nome_tok.lexema,
                              valor=valor, linha=tipo_tok.linha)

    def _atribuicao(self):
        nome_tok = self._avancar()  # IDENT
        self._esperar("OP_ATRIB", msg="esperado '=' em atribuicao")
        valor = self._expressao()
        return ast.Atribuicao(nome=nome_tok.lexema, valor=valor, linha=nome_tok.linha)

    def _comando_robo(self):
        tok = self._avancar()
        acao = tok.lexema
        if acao == "mover":
            d = self._direcao()
            expr = self._expressao()
            unid = self._esperar("PALAVRA_CHAVE", "cm",
                                 msg=f"esperada unidade 'cm' apos expressao em 'mover'")
            return ast.ComandoRobo(acao="mover", direcao=d, expressao=expr,
                                   unidade=unid.lexema, linha=tok.linha)
        if acao == "girar":
            d = self._direcao()
            expr = self._expressao()
            unid = self._esperar("PALAVRA_CHAVE", "graus",
                                 msg=f"esperada unidade 'graus' apos expressao em 'girar'")
            return ast.ComandoRobo(acao="girar", direcao=d, expressao=expr,
                                   unidade=unid.lexema, linha=tok.linha)
        if acao == "esperar":
            expr = self._expressao()
            return ast.ComandoRobo(acao="esperar", expressao=expr, linha=tok.linha)
        # parar, pegar, soltar
        return ast.ComandoRobo(acao=acao, linha=tok.linha)

    def _direcao(self) -> str:
        t = self._atual()
        if t.tipo == "PALAVRA_CHAVE" and t.lexema in DIRECOES:
            self._avancar()
            return t.lexema
        raise RoboSyntaxError(
            t.linha,
            f"esperada direcao ('frente', 'tras', 'esquerda' ou 'direita') "
            f"apos '{self.tokens[self.pos-1].lexema}', encontrado '{t.lexema}'"
        )

    def _condicional(self):
        tok = self._avancar()  # se
        self._esperar("DELIMITADOR", "(", msg="esperado '(' apos 'se'")
        cond = self._expressao()
        self._esperar("DELIMITADOR", ")", msg="esperado ')' apos condicao")
        bloco_entao = self._bloco()
        bloco_senao = None
        if self._check("PALAVRA_CHAVE", "senao"):
            self._avancar()
            if self._check("PALAVRA_CHAVE", "se"):
                bloco_senao = [self._condicional()]
            else:
                bloco_senao = self._bloco()
        return ast.Se(condicao=cond, bloco_entao=bloco_entao,
                     bloco_senao=bloco_senao, linha=tok.linha)

    def _bloco(self):
        self._esperar("DELIMITADOR", "{", msg="esperado '{' iniciando bloco")
        instrucoes = []
        while not self._check("DELIMITADOR", "}") and not self._check("EOF"):
            instrucoes.append(self._instrucao())
        self._esperar("DELIMITADOR", "}", msg="esperado '}' fechando bloco")
        return instrucoes

    def _repeticao(self):
        tok = self._avancar()
        if tok.lexema == "enquanto":
            self._esperar("DELIMITADOR", "(", msg="esperado '(' apos 'enquanto'")
            cond = self._expressao()
            self._esperar("DELIMITADOR", ")", msg="esperado ')' apos condicao")
            bloco = self._bloco()
            return ast.Enquanto(condicao=cond, bloco=bloco, linha=tok.linha)
        # repita
        expr = self._expressao()
        self._esperar("PALAVRA_CHAVE", "vezes", msg="esperado 'vezes' em 'repita'")
        bloco = self._bloco()
        return ast.Repita(vezes=expr, bloco=bloco, linha=tok.linha)

    def _funcao_def(self):
        tok = self._avancar()  # func
        nome = self._esperar("IDENTIFICADOR", msg="esperado nome de funcao apos 'func'")
        self._esperar("DELIMITADOR", "(", msg="esperado '(' apos nome de funcao")
        parametros = []
        if not self._check("DELIMITADOR", ")"):
            parametros = self._parametros()
        self._esperar("DELIMITADOR", ")", msg="esperado ')' apos parametros")
        bloco = self._bloco()
        return ast.FuncaoDef(nome=nome.lexema, parametros=parametros,
                             bloco=bloco, linha=tok.linha)

    def _parametros(self):
        params = []
        while True:
            t = self._atual()
            if t.tipo != "PALAVRA_CHAVE" or t.lexema not in TIPOS:
                raise RoboSyntaxError(t.linha,
                                      f"esperado tipo em parametro, encontrado '{t.lexema}'")
            self._avancar()
            n = self._esperar("IDENTIFICADOR", msg="esperado nome de parametro apos tipo")
            params.append((t.lexema, n.lexema))
            if not self._match("DELIMITADOR", ","):
                break
        return params

    def _entrada_saida(self):
        tok = self._avancar()
        if tok.lexema == "imprimir":
            self._esperar("DELIMITADOR", "(", msg="esperado '(' apos 'imprimir'")
            exprs = [self._expressao()]
            while self._match("DELIMITADOR", ","):
                exprs.append(self._expressao())
            self._esperar("DELIMITADOR", ")", msg="esperado ')' em 'imprimir'")
            return ast.Imprimir(expressoes=exprs, linha=tok.linha)
        # ler
        self._esperar("DELIMITADOR", "(", msg="esperado '(' apos 'ler'")
        nome = self._esperar("IDENTIFICADOR", msg="esperado nome de variavel em 'ler'")
        self._esperar("DELIMITADOR", ")", msg="esperado ')' em 'ler'")
        return ast.Ler(nome=nome.lexema, linha=tok.linha)

    def _retorno(self):
        tok = self._avancar()
        valor = self._expressao()
        return ast.Retorno(valor=valor, linha=tok.linha)

    # ---- expressoes ----
    def _expressao(self):
        return self._expr_ou()

    def _expr_ou(self):
        esq = self._expr_e()
        while self._check("OP_LOGICO", "or"):
            op = self._avancar()
            dir = self._expr_e()
            esq = ast.BinOp(op="or", esq=esq, dir=dir, linha=op.linha)
        return esq

    def _expr_e(self):
        esq = self._expr_nao()
        while self._check("OP_LOGICO", "and"):
            op = self._avancar()
            dir = self._expr_nao()
            esq = ast.BinOp(op="and", esq=esq, dir=dir, linha=op.linha)
        return esq

    def _expr_nao(self):
        if self._check("OP_LOGICO", "not"):
            op = self._avancar()
            operando = self._expr_nao()
            return ast.UnOp(op="not", operando=operando, linha=op.linha)
        return self._expr_relacional()

    def _expr_relacional(self):
        esq = self._expr_adit()
        if self._check("OP_RELACIONAL"):
            op = self._avancar()
            dir = self._expr_adit()
            return ast.BinOp(op=op.lexema, esq=esq, dir=dir, linha=op.linha)
        return esq

    def _expr_adit(self):
        esq = self._expr_mult()
        while self._check("OP_ARIT") and self._atual().lexema in ("+", "-"):
            op = self._avancar()
            dir = self._expr_mult()
            esq = ast.BinOp(op=op.lexema, esq=esq, dir=dir, linha=op.linha)
        return esq

    def _expr_mult(self):
        esq = self._expr_unaria()
        while self._check("OP_ARIT") and self._atual().lexema in ("*", "/"):
            op = self._avancar()
            dir = self._expr_unaria()
            esq = ast.BinOp(op=op.lexema, esq=esq, dir=dir, linha=op.linha)
        return esq

    def _expr_unaria(self):
        if self._check("OP_ARIT") and self._atual().lexema == "-":
            op = self._avancar()
            operando = self._expr_unaria()
            return ast.UnOp(op="-", operando=operando, linha=op.linha)
        return self._primario()

    def _primario(self):
        t = self._atual()
        if t.tipo == "NUMERO_INTEIRO":
            self._avancar()
            return ast.Literal(valor=t.valor, tipo="int", linha=t.linha)
        if t.tipo == "NUMERO_DECIMAL":
            self._avancar()
            return ast.Literal(valor=t.valor, tipo="float", linha=t.linha)
        if t.tipo == "STRING":
            self._avancar()
            return ast.Literal(valor=t.valor, tipo="texto", linha=t.linha)
        if t.tipo == "PALAVRA_CHAVE" and t.lexema == "verdade":
            self._avancar()
            return ast.Literal(valor=True, tipo="bool", linha=t.linha)
        if t.tipo == "PALAVRA_CHAVE" and t.lexema == "falso":
            self._avancar()
            return ast.Literal(valor=False, tipo="bool", linha=t.linha)
        if t.tipo == "DELIMITADOR" and t.lexema == "(":
            self._avancar()
            expr = self._expressao()
            self._esperar("DELIMITADOR", ")", msg="esperado ')' fechando expressao")
            return expr
        if t.tipo == "IDENTIFICADOR":
            self._avancar()
            # funcao_chamada?
            if self._check("DELIMITADOR", "("):
                self._avancar()
                args = []
                if not self._check("DELIMITADOR", ")"):
                    args.append(self._expressao())
                    while self._match("DELIMITADOR", ","):
                        args.append(self._expressao())
                self._esperar("DELIMITADOR", ")", msg="esperado ')' fechando chamada")
                return ast.FuncaoChamada(nome=t.lexema, args=args, linha=t.linha)
            return ast.Identificador(nome=t.lexema, linha=t.linha)
        raise RoboSyntaxError(t.linha, f"expressao invalida em {t.lexema!r}")


    # ---- API publica para REPL ----
    def parse_uma_instrucao(self):
        """Consome e retorna apenas uma instrucao. Nao exige EOF."""
        if self._check("EOF"):
            return None
        return self._instrucao()

    def parse_expressao_publica(self):
        """Tenta parsear uma expressao pura. Levanta RoboSyntaxError se falhar."""
        expr = self._expressao()
        if not self._check("EOF"):
            t = self._atual()
            raise RoboSyntaxError(t.linha, f"sobra apos expressao: {t.lexema!r}")
        return expr

    def at_end(self) -> bool:
        return self._check("EOF")


def parse(tokens: List[Token]) -> ast.Programa:
    return Parser(tokens).parse()


def parse_uma(tokens: List[Token]):
    """Wrapper: retorna apenas a primeira instrucao."""
    return Parser(tokens).parse_uma_instrucao()


def parse_expressao(tokens: List[Token]):
    """Wrapper: tenta parsear como expressao pura."""
    return Parser(tokens).parse_expressao_publica()
