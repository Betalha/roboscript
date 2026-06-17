"""Mundo simulado do robo: grade, sensor e leitor de diretivas."""
import re
from dataclasses import dataclass, field
from typing import List, Set, Tuple, Optional


# Orientacao em graus: 0=norte, 90=leste, 180=sul, 270=oeste
DIR_NORTE = 0
DIR_LESTE = 90
DIR_SUL = 180
DIR_OESTE = 270

NOMES_DIR = {
    DIR_NORTE: "Norte",
    DIR_LESTE: "Leste",
    DIR_SUL: "Sul",
    DIR_OESTE: "Oeste",
}

SIMBOLOS_ROBO = {
    DIR_NORTE: "^",
    DIR_LESTE: ">",
    DIR_SUL: "v",
    DIR_OESTE: "<",
}


@dataclass
class World:
    largura: int = 30
    altura: int = 20
    x: int = 15  # posicao do robo
    y: int = 10
    direcao: int = DIR_NORTE
    carregando: bool = False
    obstaculos: Set[Tuple[int, int]] = field(default_factory=set)
    objetos: Set[Tuple[int, int]] = field(default_factory=set)
    trilha: List[Tuple[int, int]] = field(default_factory=list)
    ultima_acao: str = "(inicio)"
    ultima_leitura: Optional[int] = None
    log: List[str] = field(default_factory=list)

    def __post_init__(self):
        # garante posicao inicial dentro da grade
        self.x = max(0, min(self.largura - 1, self.x))
        self.y = max(0, min(self.altura - 1, self.y))
        if not self.trilha or self.trilha[-1] != (self.x, self.y):
            self.trilha.append((self.x, self.y))

    # ---- vetores de movimento ----
    @staticmethod
    def _delta(direcao: int) -> Tuple[int, int]:
        # (dx, dy) em coords onde y cresce para baixo
        if direcao == DIR_NORTE:
            return (0, -1)
        if direcao == DIR_LESTE:
            return (1, 0)
        if direcao == DIR_SUL:
            return (0, 1)
        if direcao == DIR_OESTE:
            return (-1, 0)
        # fallback (nao deveria ocorrer)
        return (0, 0)

    def direcao_apos_movimento(self, palavra: str) -> int:
        """Para 'mover X cm' retorna a direcao efetiva relativa a orientacao atual."""
        if palavra == "frente":
            return self.direcao
        if palavra == "tras":
            return (self.direcao + 180) % 360
        if palavra == "esquerda":
            return (self.direcao + 270) % 360
        if palavra == "direita":
            return (self.direcao + 90) % 360
        return self.direcao

    def girar(self, palavra: str, graus: int) -> None:
        if palavra == "direita":
            self.direcao = (self.direcao + graus) % 360
        elif palavra == "esquerda":
            self.direcao = (self.direcao - graus) % 360
        # tras/frente girando nao sao usuais mas tratamos para nao quebrar
        elif palavra == "tras":
            self.direcao = (self.direcao + 180) % 360
        # normaliza para multiplos de 90 (a viz so suporta 4 direcoes)
        self.direcao = round(self.direcao / 90) * 90 % 360

    def mover(self, palavra: str, qtd: int) -> int:
        """Move ate qtd celulas na direcao indicada. Para ao bater em obstaculo
        ou nas bordas. Retorna quantas celulas efetivamente andou."""
        d = self.direcao_apos_movimento(palavra)
        dx, dy = self._delta(d)
        andados = 0
        for _ in range(int(qtd)):
            nx, ny = self.x + dx, self.y + dy
            if not self._em_grade(nx, ny):
                break
            if (nx, ny) in self.obstaculos:
                break
            self.x, self.y = nx, ny
            self.trilha.append((self.x, self.y))
            andados += 1
        return andados

    def _em_grade(self, x: int, y: int) -> bool:
        return 0 <= x < self.largura and 0 <= y < self.altura

    def sensor_distancia(self) -> int:
        """Distancia ate o proximo obstaculo (ou borda) na direcao atual."""
        dx, dy = self._delta(self.direcao)
        d = 0
        cx, cy = self.x, self.y
        while True:
            cx += dx
            cy += dy
            if not self._em_grade(cx, cy):
                return d
            if (cx, cy) in self.obstaculos:
                return d
            d += 1

    def pegar(self) -> bool:
        if (self.x, self.y) in self.objetos:
            self.objetos.discard((self.x, self.y))
            self.carregando = True
            return True
        return False

    def soltar(self) -> bool:
        if self.carregando:
            self.objetos.add((self.x, self.y))
            self.carregando = False
            return True
        return False


# ---- Parser de diretivas em comentarios ----

_RE_DIRETIVA = re.compile(r"#\s*@(\w+)\s+(.+)")


def parse_diretivas(fonte: str) -> dict:
    """Le linhas de comentario com '# @chave valor' e retorna config."""
    cfg = {
        "largura": 30,
        "altura": 20,
        "x": None,
        "y": None,
        "direcao": DIR_NORTE,
        "obstaculos": [],
        "objetos": [],
    }
    for linha in fonte.splitlines():
        m = _RE_DIRETIVA.match(linha.strip())
        if not m:
            continue
        chave, valor = m.group(1), m.group(2).strip()
        if chave == "mundo":
            mm = re.match(r"(\d+)\s*x\s*(\d+)", valor)
            if mm:
                cfg["largura"] = int(mm.group(1))
                cfg["altura"] = int(mm.group(2))
        elif chave == "inicio":
            mm = re.match(r"(\d+)\s*,\s*(\d+)", valor)
            if mm:
                cfg["x"] = int(mm.group(1))
                cfg["y"] = int(mm.group(2))
        elif chave == "direcao":
            v = valor.lower()
            cfg["direcao"] = {
                "norte": DIR_NORTE,
                "leste": DIR_LESTE,
                "sul": DIR_SUL,
                "oeste": DIR_OESTE,
            }.get(v, DIR_NORTE)
        elif chave == "obstaculo":
            mm = re.match(r"(\d+)\s*,\s*(\d+)", valor)
            if mm:
                cfg["obstaculos"].append((int(mm.group(1)), int(mm.group(2))))
        elif chave == "objeto":
            mm = re.match(r"(\d+)\s*,\s*(\d+)", valor)
            if mm:
                cfg["objetos"].append((int(mm.group(1)), int(mm.group(2))))
    return cfg


def build_world(fonte: str, override: dict = None) -> World:
    cfg = parse_diretivas(fonte)
    if override:
        cfg.update({k: v for k, v in override.items() if v is not None})
    x = cfg["x"] if cfg["x"] is not None else cfg["largura"] // 2
    y = cfg["y"] if cfg["y"] is not None else cfg["altura"] // 2
    w = World(
        largura=cfg["largura"],
        altura=cfg["altura"],
        x=x, y=y,
        direcao=cfg["direcao"],
        obstaculos=set(cfg["obstaculos"]),
        objetos=set(cfg["objetos"]),
    )
    return w
