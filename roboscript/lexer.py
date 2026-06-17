"""Lexer do RoboScript - Etapa 2 do PDF."""
from dataclasses import dataclass
from typing import List, Optional
from .errors import RoboLexError


PALAVRAS_RESERVADAS = {
    "mover", "girar", "parar", "pegar", "soltar", "esperar", "sensor",
    "se", "senao", "enquanto", "repita", "vezes",
    "func", "retorno", "imprimir", "ler",
    "int", "float", "texto", "bool",
    "verdade", "falso",
    "frente", "tras", "esquerda", "direita", "graus", "cm",
}

OP_LOGICOS = {"and", "or", "not"}


@dataclass
class Token:
    tipo: str
    lexema: str
    valor: object = None
    linha: int = 0
    coluna: int = 0

    def __repr__(self):
        if self.valor is not None and self.valor != self.lexema:
            return f"Token({self.tipo}, {self.lexema!r}, {self.valor!r}, L{self.linha})"
        return f"Token({self.tipo}, {self.lexema!r}, L{self.linha})"


class Lexer:
    def __init__(self, fonte: str):
        self.fonte = fonte
        self.pos = 0
        self.linha = 1
        self.coluna = 1
        self.tokens: List[Token] = []

    # ---- helpers ----
    def _peek(self, k=0) -> Optional[str]:
        p = self.pos + k
        if p < len(self.fonte):
            return self.fonte[p]
        return None

    def _avancar(self) -> str:
        c = self.fonte[self.pos]
        self.pos += 1
        if c == "\n":
            self.linha += 1
            self.coluna = 1
        else:
            self.coluna += 1
        return c

    def _at_end(self) -> bool:
        return self.pos >= len(self.fonte)

    # ---- principal ----
    def tokenize(self) -> List[Token]:
        while not self._at_end():
            c = self._peek()
            # espacos em branco
            if c in (" ", "\t", "\r", "\n"):
                self._avancar()
                continue
            # comentario de linha
            if c == "#":
                while not self._at_end() and self._peek() != "\n":
                    self._avancar()
                continue
            # comentario de bloco
            if c == "/" and self._peek(1) == "*":
                self._avancar(); self._avancar()
                while not self._at_end() and not (self._peek() == "*" and self._peek(1) == "/"):
                    self._avancar()
                if self._at_end():
                    raise RoboLexError(self.linha, "comentario de bloco nao fechado")
                self._avancar(); self._avancar()
                continue
            # string
            if c == '"':
                self._string()
                continue
            # numero
            if c.isdigit():
                self._numero()
                continue
            # identificador / palavra-chave
            if c.isalpha() or c == "_":
                self._identificador()
                continue
            # operadores e delimitadores
            if self._operador_ou_delim():
                continue

            # caso nao reconhecido
            raise RoboLexError(self.linha, f"caractere inesperado {c!r}")

        self.tokens.append(Token("EOF", "", None, self.linha, self.coluna))
        return self.tokens

    def _string(self):
        linha_ini = self.linha
        col_ini = self.coluna
        self._avancar()  # "
        buf = []
        while not self._at_end() and self._peek() != '"':
            c = self._avancar()
            if c == "\\":
                if self._at_end():
                    raise RoboLexError(linha_ini, "escape invalido em string")
                esc = self._avancar()
                if esc == "n":
                    buf.append("\n")
                elif esc == "t":
                    buf.append("\t")
                elif esc == '"':
                    buf.append('"')
                elif esc == "\\":
                    buf.append("\\")
                else:
                    raise RoboLexError(linha_ini, f"sequencia de escape invalida '\\{esc}'")
            else:
                buf.append(c)
        if self._at_end():
            raise RoboLexError(linha_ini, "string nao terminada")
        self._avancar()  # "
        s = "".join(buf)
        self.tokens.append(Token("STRING", f'"{s}"', s, linha_ini, col_ini))

    def _numero(self):
        linha_ini = self.linha
        col_ini = self.coluna
        ini = self.pos
        while not self._at_end() and self._peek().isdigit():
            self._avancar()
        eh_decimal = False
        if not self._at_end() and self._peek() == "." and self._peek(1) and self._peek(1).isdigit():
            eh_decimal = True
            self._avancar()  # .
            while not self._at_end() and self._peek().isdigit():
                self._avancar()
        lexema = self.fonte[ini:self.pos]
        # verifica se ha letra colada (ex: 2robo) -> erro lexico
        if not self._at_end() and (self._peek().isalpha() or self._peek() == "_"):
            # consome o resto para mostrar o lexema invalido
            inv_ini = ini
            while not self._at_end() and (self._peek().isalnum() or self._peek() == "_"):
                self._avancar()
            lex_inv = self.fonte[inv_ini:self.pos]
            raise RoboLexError(
                linha_ini,
                f"identificador nao pode comecar com digito -- encontrado '{lex_inv}'"
            )
        if eh_decimal:
            self.tokens.append(Token("NUMERO_DECIMAL", lexema, float(lexema), linha_ini, col_ini))
        else:
            self.tokens.append(Token("NUMERO_INTEIRO", lexema, int(lexema), linha_ini, col_ini))

    def _identificador(self):
        linha_ini = self.linha
        col_ini = self.coluna
        ini = self.pos
        while not self._at_end() and (self._peek().isalnum() or self._peek() == "_"):
            self._avancar()
        lex = self.fonte[ini:self.pos]
        if lex in PALAVRAS_RESERVADAS:
            self.tokens.append(Token("PALAVRA_CHAVE", lex, lex, linha_ini, col_ini))
        elif lex in OP_LOGICOS:
            self.tokens.append(Token("OP_LOGICO", lex, lex, linha_ini, col_ini))
        else:
            self.tokens.append(Token("IDENTIFICADOR", lex, lex, linha_ini, col_ini))

    def _operador_ou_delim(self) -> bool:
        linha_ini = self.linha
        col_ini = self.coluna
        c = self._peek()
        c2 = self._peek(1)
        dois = (c or "") + (c2 or "")

        # operadores de 2 chars
        if dois in ("==", "!=", ">=", "<="):
            self._avancar(); self._avancar()
            self.tokens.append(Token("OP_RELACIONAL", dois, dois, linha_ini, col_ini))
            return True
        # operadores de 1 char
        if c in (">", "<"):
            self._avancar()
            self.tokens.append(Token("OP_RELACIONAL", c, c, linha_ini, col_ini))
            return True
        if c in ("+", "-", "*", "/"):
            self._avancar()
            self.tokens.append(Token("OP_ARIT", c, c, linha_ini, col_ini))
            return True
        if c == "=":
            self._avancar()
            self.tokens.append(Token("OP_ATRIB", c, c, linha_ini, col_ini))
            return True
        if c in ("(", ")", "{", "}", ",", ";", ":"):
            self._avancar()
            self.tokens.append(Token("DELIMITADOR", c, c, linha_ini, col_ini))
            return True
        return False


def tokenize(fonte: str) -> List[Token]:
    return Lexer(fonte).tokenize()
