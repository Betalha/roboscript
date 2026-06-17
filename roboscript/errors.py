"""Excecoes do RoboScript."""


class RoboError(Exception):
    """Base para todos os erros da linguagem."""

    def __init__(self, linha, mensagem):
        self.linha = linha
        self.mensagem = mensagem
        super().__init__(self.format())

    def format(self):
        return f"[Linha {self.linha}] {self.kind()}: {self.mensagem}"

    def kind(self):
        return "Erro"


class RoboLexError(RoboError):
    def kind(self):
        return "Erro lexico"


class RoboSyntaxError(RoboError):
    def kind(self):
        return "Erro sintatico"


class RoboRuntimeError(RoboError):
    def kind(self):
        return "Erro de execucao"


class RoboTypeError(RoboError):
    def kind(self):
        return "Erro de tipo"
