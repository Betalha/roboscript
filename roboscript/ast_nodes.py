"""Nos da AST do RoboScript."""
from dataclasses import dataclass, field
from typing import Any, List, Optional, Union


# ---- Expressoes ----

@dataclass
class Literal:
    valor: Any
    tipo: str  # "int", "float", "texto", "bool"
    linha: int = 0


@dataclass
class Identificador:
    nome: str
    linha: int = 0


@dataclass
class BinOp:
    op: str
    esq: Any
    dir: Any
    linha: int = 0


@dataclass
class UnOp:
    op: str
    operando: Any
    linha: int = 0


@dataclass
class FuncaoChamada:
    nome: str
    args: List[Any] = field(default_factory=list)
    linha: int = 0


# ---- Instrucoes ----

@dataclass
class Declaracao:
    tipo: str
    nome: str
    valor: Optional[Any] = None
    linha: int = 0


@dataclass
class Atribuicao:
    nome: str
    valor: Any
    linha: int = 0


@dataclass
class ComandoRobo:
    acao: str  # "mover", "girar", "parar", "pegar", "soltar", "esperar"
    direcao: Optional[str] = None  # "frente", "tras", "esquerda", "direita"
    expressao: Optional[Any] = None
    unidade: Optional[str] = None  # "cm" ou "graus"
    linha: int = 0


@dataclass
class Se:
    condicao: Any
    bloco_entao: List[Any]
    bloco_senao: Optional[List[Any]] = None  # lista de instrucoes OU [Se] aninhado
    linha: int = 0


@dataclass
class Enquanto:
    condicao: Any
    bloco: List[Any]
    linha: int = 0


@dataclass
class Repita:
    vezes: Any
    bloco: List[Any]
    linha: int = 0


@dataclass
class FuncaoDef:
    nome: str
    parametros: List[tuple]  # [(tipo, nome), ...]
    bloco: List[Any]
    linha: int = 0


@dataclass
class Imprimir:
    expressoes: List[Any]
    linha: int = 0


@dataclass
class Ler:
    nome: str
    linha: int = 0


@dataclass
class Retorno:
    valor: Any
    linha: int = 0


@dataclass
class Programa:
    instrucoes: List[Any] = field(default_factory=list)


# ---- Helper para imprimir AST como arvore ----

def ast_to_string(node, indent=0):
    pad = "  " * indent
    if isinstance(node, Programa):
        out = f"{pad}Programa\n"
        for i in node.instrucoes:
            out += ast_to_string(i, indent + 1)
        return out
    if isinstance(node, Declaracao):
        out = f"{pad}Declaracao(tipo={node.tipo}, nome={node.nome})\n"
        if node.valor is not None:
            out += ast_to_string(node.valor, indent + 1)
        return out
    if isinstance(node, Atribuicao):
        out = f"{pad}Atribuicao({node.nome} =)\n"
        out += ast_to_string(node.valor, indent + 1)
        return out
    if isinstance(node, ComandoRobo):
        partes = [node.acao]
        if node.direcao:
            partes.append(node.direcao)
        if node.unidade:
            partes.append(node.unidade)
        out = f"{pad}ComandoRobo({' '.join(partes)})\n"
        if node.expressao is not None:
            out += ast_to_string(node.expressao, indent + 1)
        return out
    if isinstance(node, Se):
        out = f"{pad}Se\n"
        out += f"{pad}  condicao:\n"
        out += ast_to_string(node.condicao, indent + 2)
        out += f"{pad}  entao:\n"
        for i in node.bloco_entao:
            out += ast_to_string(i, indent + 2)
        if node.bloco_senao:
            out += f"{pad}  senao:\n"
            for i in node.bloco_senao:
                out += ast_to_string(i, indent + 2)
        return out
    if isinstance(node, Enquanto):
        out = f"{pad}Enquanto\n"
        out += f"{pad}  condicao:\n"
        out += ast_to_string(node.condicao, indent + 2)
        out += f"{pad}  bloco:\n"
        for i in node.bloco:
            out += ast_to_string(i, indent + 2)
        return out
    if isinstance(node, Repita):
        out = f"{pad}Repita\n"
        out += f"{pad}  vezes:\n"
        out += ast_to_string(node.vezes, indent + 2)
        out += f"{pad}  bloco:\n"
        for i in node.bloco:
            out += ast_to_string(i, indent + 2)
        return out
    if isinstance(node, FuncaoDef):
        params = ", ".join(f"{t} {n}" for t, n in node.parametros)
        out = f"{pad}FuncaoDef({node.nome}({params}))\n"
        for i in node.bloco:
            out += ast_to_string(i, indent + 1)
        return out
    if isinstance(node, FuncaoChamada):
        out = f"{pad}FuncaoChamada({node.nome})\n"
        for a in node.args:
            out += ast_to_string(a, indent + 1)
        return out
    if isinstance(node, Imprimir):
        out = f"{pad}Imprimir\n"
        for e in node.expressoes:
            out += ast_to_string(e, indent + 1)
        return out
    if isinstance(node, Ler):
        return f"{pad}Ler({node.nome})\n"
    if isinstance(node, Retorno):
        out = f"{pad}Retorno\n"
        out += ast_to_string(node.valor, indent + 1)
        return out
    if isinstance(node, BinOp):
        out = f"{pad}BinOp({node.op})\n"
        out += ast_to_string(node.esq, indent + 1)
        out += ast_to_string(node.dir, indent + 1)
        return out
    if isinstance(node, UnOp):
        out = f"{pad}UnOp({node.op})\n"
        out += ast_to_string(node.operando, indent + 1)
        return out
    if isinstance(node, Literal):
        return f"{pad}Literal({node.tipo}: {node.valor!r})\n"
    if isinstance(node, Identificador):
        return f"{pad}Identificador({node.nome})\n"
    return f"{pad}<desconhecido {type(node).__name__}>\n"
