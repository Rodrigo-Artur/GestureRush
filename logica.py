"""Regras puras, independentes da webcam e da interface gráfica."""
from dataclasses import dataclass
import math
import random

PARTIDA_SEGUNDOS = 60


def limitar(valor, minimo, maximo):
    return max(minimo, min(maximo, valor))


def distancia(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def mapear_mira(x, y, largura, altura, sensibilidade=1.6):
    """Amplifica o movimento em torno do centro e limita ao tamanho da tela."""
    ganho = limitar(float(sensibilidade), 0.6, 3.0) / 0.84
    nx = limitar(0.5 + (x - 0.5) * ganho, 0, 1)
    ny = limitar(0.5 + (y - 0.5) * ganho, 0, 1)
    return nx * largura, ny * altura


class DetectorPunho:
    """Um clique por fechamento de punho; exige abrir antes do próximo."""
    def __init__(self, quadros=2):
        self.quadros = max(1, int(quadros))
        self.reiniciar()

    def reiniciar(self):
        self.armado = False
        self.fechados = 0
        self.abertos = 0

    def atualizar(self, gesto):
        if gesto is None:
            self.reiniciar()
            return False
        if gesto == 'punho':
            self.fechados += 1
            self.abertos = 0
            if self.armado and self.fechados >= self.quadros:
                self.armado = False
                return True
            return False
        self.abertos += 1
        self.fechados = 0
        if self.abertos >= self.quadros:
            self.armado = True
        return False


class DetectorGestoMantido:
    """Dispara uma vez após manter o gesto pelo tempo exigido."""
    def __init__(self, segundos=1.2):
        self.segundos = float(segundos)
        self.reiniciar()

    def reiniciar(self):
        self.inicio = None
        self.disparado = False

    def atualizar(self, ativo, agora):
        if not ativo:
            self.reiniciar()
            return False
        if self.inicio is None:
            self.inicio = agora
        if not self.disparado and agora - self.inicio >= self.segundos:
            self.disparado = True
            return True
        return False


def pontuacao(tipo, combo):
    """Alvos bons: 10/20 pontos com bônus de combo. Obstáculo: -15."""
    if tipo == 'perigo':
        return -15
    base = 20 if tipo == 'bonus' else 10
    return base + min(max(combo, 0), 10) * 2


@dataclass
class Alvo:
    x: float
    y: float
    raio: float
    tipo: str
    vida: float
    oscilacao: float = 0.0

    def contem(self, x, y):
        return distancia((self.x, self.y), (x, y)) <= self.raio + 9


def criar_alvo(largura, altura, atuais, nivel=1, gerador=None):
    rng = gerador or random
    topo = 116
    rodape = altura - 70
    raio = max(23, 41 - min(12, nivel * 2))
    for _ in range(75):
        x = rng.randint(raio + 28, max(raio + 28, largura - raio - 28))
        y = rng.randint(topo + raio, max(topo + raio, rodape - raio))
        if all(distancia((x, y), (a.x, a.y)) > raio + a.raio + 30 for a in atuais):
            break
    else:
        return None
    chance = rng.random()
    tipo = 'perigo' if nivel >= 3 and chance < 0.11 else 'bonus' if chance > 0.86 else 'normal'
    vida = max(1.35, 3.8 - nivel * 0.22)
    return Alvo(x, y, raio, tipo, vida, rng.random() * math.tau)


def classificar_gesto(marcos):
    """Devolve (x, y, gesto): apontando, punho, palma, vitoria ou outro."""
    if marcos is None or len(marcos) < 21:
        return None
    p = lambda n: (marcos[n].x, marcos[n].y)
    estendidos = [
        distancia(p(ponta), p(0)) > distancia(p(base), p(0)) * 1.17
        for ponta, base in ((8, 6), (12, 10), (16, 14), (20, 18))
    ]
    indicador, medio, anelar, minimo = estendidos
    if not any(estendidos):
        gesto = 'punho'
    elif all(estendidos):
        gesto = 'palma'
    elif indicador and medio and not anelar and not minimo:
        gesto = 'vitoria'
    elif indicador and not medio and not anelar and not minimo:
        gesto = 'apontando'
    else:
        gesto = 'outro'
    return p(8)[0], p(8)[1], gesto
