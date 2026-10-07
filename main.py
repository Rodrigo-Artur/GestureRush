"""Gesture Rush: arcade offline para feira de ADS.

Controles por gesto:
- Indicador apontado: move a mira
- Punho fechado: clique/disparo
- Palma aberta por 1,2s: pausar/continuar
- Sinal de V por 1,2s: abrir calibração / iniciar / avançar

Alternativa para desenvolvimento: python main.py --mouse
"""
import argparse
import json
import math
import os
from pathlib import Path
import random
import sys
import time

import pygame

from logica import (
    PARTIDA_SEGUNDOS,
    DetectorGestoMantido,
    DetectorPunho,
    classificar_gesto,
    criar_alvo,
    limitar,
    mapear_mira,
    pontuacao,
)

W, H = 1280, 720
FATORES_DIFICULDADE = {'facil': 0.33, 'medio': 0.66, 'dificil': 1.10}
DIFICULDADES = ('facil', 'medio', 'dificil')
MODOS_RANKING = ('webcam', 'mouse')
FUNDO = (10, 16, 33)
PAINEL = (20, 31, 54)
BRANCO = (237, 246, 255)
CINZA = (145, 163, 195)
CIANO = (72, 225, 244)
ROXO = (173, 125, 255)
OURO = (255, 208, 87)
VERMELHO = (255, 96, 114)
VERDE = (113, 235, 158)


def pasta_recursos():
    # No executável PyInstaller, assets e modelos empacotados ficam em _MEIPASS.
    return Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent))


def pasta_appdata():
    raiz = Path(os.environ.get('LOCALAPPDATA', str(Path.home()))) / 'GestureRush'
    raiz.mkdir(parents=True, exist_ok=True)
    return raiz


def arquivo_ranking():
    return pasta_appdata() / 'ranking.json'


def arquivo_config():
    return pasta_appdata() / 'config.json'


def novo_ranking():
    return {
        'versao': 2,
        'rankings': {modo: {dif: [] for dif in DIFICULDADES} for modo in MODOS_RANKING},
        'legado': [],
    }


def registros_validos(itens):
    if not isinstance(itens, list):
        return []
    resultado = []
    for item in itens:
        if (isinstance(item, dict) and isinstance(item.get('pontos'), int)
                and not isinstance(item.get('pontos'), bool)
                and isinstance(item.get('nome'), str)):
            resultado.append({'nome': item['nome'][:14], 'pontos': max(0, item['pontos'])})
    return sorted(resultado, key=lambda item: (-item['pontos'], item['nome']))[:20]


def ler_ranking():
    ranking = novo_ranking()
    try:
        dado = json.loads(arquivo_ranking().read_text(encoding='utf-8'))
        if isinstance(dado, list):
            ranking['legado'] = registros_validos(dado)
        elif isinstance(dado, dict):
            ranking['legado'] = registros_validos(dado.get('legado', []))
            grupos = dado.get('rankings', {})
            for modo in MODOS_RANKING:
                for dificuldade in DIFICULDADES:
                    ranking['rankings'][modo][dificuldade] = registros_validos(
                        grupos.get(modo, {}).get(dificuldade, [])
                        if isinstance(grupos, dict) and isinstance(grupos.get(modo, {}), dict)
                        else []
                    )
    except (OSError, ValueError, TypeError):
        pass
    return ranking


def lista_ranking(ranking, modo, dificuldade):
    modo = 'webcam' if modo in ('camera', 'webcam') else 'mouse'
    dificuldade = dificuldade if dificuldade in DIFICULDADES else 'medio'
    return ranking['rankings'][modo][dificuldade]


def salvar_ranking(nome, pontos, modo, dificuldade):
    ranking = ler_ranking()
    lista = lista_ranking(ranking, modo, dificuldade)
    lista.append({'nome': nome.strip()[:14].upper() or 'VISITANTE', 'pontos': max(0, int(pontos))})
    lista.sort(key=lambda i: (-i['pontos'], i['nome']))
    arquivo = arquivo_ranking()
    tmp = arquivo.with_suffix('.tmp')
    ranking['rankings']['webcam' if modo in ('camera', 'webcam') else 'mouse'][
        dificuldade if dificuldade in DIFICULDADES else 'medio'] = lista[:20]
    tmp.write_text(json.dumps(ranking, ensure_ascii=False, indent=2), encoding='utf-8')
    tmp.replace(arquivo)
    return lista[:20]


def carregar_config():
    padrao = {'sensibilidade': 1.6, 'resposta': 0.60}
    try:
        dados = json.loads(arquivo_config().read_text(encoding='utf-8'))
        for chave, limites in (('sensibilidade', (0.6, 3.0)), ('resposta', (0.2, 0.9))):
            valor = dados.get(chave)
            if isinstance(valor, (int, float)) and math.isfinite(valor):
                padrao[chave] = round(limitar(float(valor), *limites), 2)
    except (OSError, ValueError, TypeError, AttributeError):
        pass
    return padrao


def salvar_config(config):
    try:
        destino = arquivo_config()
        temporario = destino.with_suffix('.tmp')
        temporario.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding='utf-8')
        temporario.replace(destino)
        return True
    except OSError:
        return False


class VisualAssets:
    """Carrega e redimensiona assets do jogo."""
    def __init__(self):
        self.raiz = pasta_recursos() / 'assets'
        self.cache = {}
        self.cache_scaled = {}

    def load(self, relpath):
        relpath = str(relpath).replace('\\', '/')
        if relpath in self.cache:
            return self.cache[relpath]
        path = self.raiz / relpath
        if not path.exists():
            self.cache[relpath] = None
            return None
        try:
            img = pygame.image.load(str(path)).convert_alpha()
        except Exception:
            img = None
        self.cache[relpath] = img
        return img

    def get(self, relpath, size=None):
        img = self.load(relpath)
        if img is None:
            return None
        if size is None:
            return img
        w = max(1, int(size[0]))
        h = max(1, int(size[1]))
        key = (str(relpath), w, h)
        if key not in self.cache_scaled:
            self.cache_scaled[key] = pygame.transform.smoothscale(img, (w, h))
        return self.cache_scaled[key]

    def fit_w(self, relpath, width):
        img = self.load(relpath)
        if img is None:
            return None
        ow, oh = img.get_size()
        return self.get(relpath, (int(width), int(oh * (width / ow))))

    def fit_h(self, relpath, height):
        img = self.load(relpath)
        if img is None:
            return None
        ow, oh = img.get_size()
        return self.get(relpath, (int(ow * (height / oh)), int(height)))

    def fit_box(self, relpath, size):
        img = self.load(relpath)
        if img is None:
            return None
        ow, oh = img.get_size()
        escala = min(size[0] / ow, size[1] / oh)
        return self.get(relpath, (int(ow * escala), int(oh * escala)))

    def cover(self, relpath, size):
        img = self.load(relpath)
        if img is None:
            return None
        tw, th = size
        ow, oh = img.get_size()
        escala = max(tw / ow, th / oh)
        return self.get(relpath, (int(ow * escala), int(oh * escala)))


class Rastreador:
    """Lê imagens locais. Não envia, salva nem transmite vídeo."""
    def __init__(self, indice=0, somente_mouse=False):
        self.modo = 'mouse'
        self.mensagem = 'Modo mouse ativado (M alterna, quando houver webcam).'
        self.cap = None
        self.landmarker = None
        self.cv2 = None
        self.mp = None
        self.preview = None
        self.ultimo_ms = 0
        self.ultima_leitura = 0
        if somente_mouse:
            return
        modelo = pasta_recursos() / 'modelos' / 'hand_landmarker.task'
        if not modelo.exists():
            self.mensagem = 'Modelo ausente: execute baixar_modelo.py ANTES da feira.'
            return
        try:
            import cv2
            import mediapipe as mp
            self.cv2, self.mp = cv2, mp
            opcoes = mp.tasks.vision.HandLandmarkerOptions(
                base_options=mp.tasks.BaseOptions(model_asset_path=str(modelo)),
                running_mode=mp.tasks.vision.RunningMode.VIDEO,
                num_hands=1,
                min_hand_detection_confidence=0.56,
                min_hand_presence_confidence=0.52,
                min_tracking_confidence=0.52,
            )
            self.landmarker = mp.tasks.vision.HandLandmarker.create_from_options(opcoes)
            api = cv2.CAP_DSHOW if os.name == 'nt' else cv2.CAP_ANY
            self.cap = cv2.VideoCapture(indice, api)
            if not self.cap.isOpened() and os.name == 'nt':
                self.cap.release()
                self.cap = cv2.VideoCapture(indice, cv2.CAP_ANY)
            if not self.cap.isOpened():
                self.mensagem = f'Câmera {indice} indisponível. Teste --camera 1 ou --mouse.'
                self.close()
                return
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            self.modo = 'camera'
            self.mensagem = 'Câmera ativa. Aproxime a mão com boa iluminação.'
        except Exception as e:
            self.mensagem = f'Falha na câmera/MediaPipe: {str(e)[:92]}'
            self.close()

    def ler(self):
        if self.modo != 'camera' or not self.cap:
            return None
        agora = time.monotonic()
        if agora - self.ultima_leitura < 1 / 30:
            return 'aguardando'
        self.ultima_leitura = agora
        ok, frame = self.cap.read()
        if not ok:
            self.mensagem = 'Não foi possível ler a câmera; pressione M para usar mouse.'
            return None
        frame = self.cv2.flip(frame, 1)
        rgb = self.cv2.cvtColor(frame, self.cv2.COLOR_BGR2RGB)
        try:
            import numpy as np
            img = self.mp.Image(image_format=self.mp.ImageFormat.SRGB,
                                data=np.ascontiguousarray(rgb))
            ms = max(int(time.monotonic() * 1000), self.ultimo_ms + 1)
            self.ultimo_ms = ms
            resultado = self.landmarker.detect_for_video(img, ms)
            foto = pygame.image.frombuffer(rgb.tobytes(), (frame.shape[1], frame.shape[0]), 'RGB')
            self.preview = pygame.transform.smoothscale(foto, (176, 132))
            return classificar_gesto(resultado.hand_landmarks[0]) if resultado.hand_landmarks else None
        except Exception as e:
            self.mensagem = f'Erro na detecção: {str(e)[:80]}'
            return None

    def close(self):
        if self.cap:
            self.cap.release()
            self.cap = None
        if self.landmarker:
            self.landmarker.close()
            self.landmarker = None


class Jogo:
    def __init__(self, args):
        pygame.init()
        self.audio_disponivel = False
        try:
            pygame.mixer.init()
            pygame.mixer.music.set_volume(0.45)
            self.audio_disponivel = True
        except pygame.error:
            # Audio hardware can be unavailable; gameplay remains usable.
            pass
        pygame.display.set_caption('GESTURE RUSH | Feira ADS — 100% offline')
        self.tela = pygame.display.set_mode((W, H), pygame.RESIZABLE)
        self.relogio = pygame.time.Clock()
        self.largura, self.altura = W, H
        self.fonte_titulo = pygame.font.SysFont('segoeui', 68, bold=True)
        self.fonte_grande = pygame.font.SysFont('segoeui', 40, bold=True)
        self.fonte_media = pygame.font.SysFont('segoeui', 26, bold=True)
        self.fonte_texto = pygame.font.SysFont('segoeui', 21)
        self.fonte_pequena = pygame.font.SysFont('segoeui', 16)
        self.assets = VisualAssets()
        icone = self.assets.load('definitivos/marca/16_icone_app_64.png')
        if icone:
            pygame.display.set_icon(icone)
        self.rastreador = Rastreador(args.camera, args.mouse)
        self.prever_camera = not args.sem_preview
        self.ativo = True
        self.tela_estado = 'menu'
        self.dificuldade = 'medio'
        self.config = carregar_config()
        self.detector_punho = DetectorPunho()
        self.detector_pausa = DetectorGestoMantido(1.2)
        self.detector_vitoria = DetectorGestoMantido(1.2)
        self.cursor = (W / 2, H / 2)
        self.gesto_atual = 'sem mão'
        self.mao_presente = False
        self.pontos = 0
        self.combo = 0
        self.max_combo = 0
        self.tempo = PARTIDA_SEGUNDOS
        self.acertos = 0
        self.erros = 0
        self.alvos = []
        self.particulas = []
        self.mensagem_flutuante = None
        self.efeitos_visuais = []
        self.combo_visual = None
        self.nome = ''
        self.salvo = False
        self.rankings = ler_ranking()
        self.modo_partida = self.rastreador.modo
        self.ranking = lista_ranking(self.rankings, self.modo_partida, self.dificuldade)
        self.faixa_musica = None
        self.novo_recorde = False
        self.estrelas = [(random.randrange(W), random.randrange(H), random.choice([1, 1, 2]))
                         for _ in range(85)]
        self.acertos_teste = set()
        self.ui_rects = {}
        self.popup_textures = {
            '+10': 'fx/score_10.png',
            '+20': 'fx/score_20.png',
            '-15': 'fx/score_m15.png',
            'ERRO': 'fx/score_erro.png',
            'OK': 'fx/score_ok.png',
        }
        self.atualizar_musica()

    @property
    def nivel(self):
        return 1 + self.acertos // 7

    def musica_desejada(self):
        if self.tela_estado == 'menu':
            return '01_neon_awakening.mp3'
        if self.tela_estado in ('calibracao', 'dificuldade'):
            return '02_system_calibration.mp3'
        if self.tela_estado == 'jogando':
            return ('04_final_countdown.mp3' if self.tempo <= 10
                    else '03_reflex_overdrive.mp3')
        if self.tela_estado == 'pausado':
            return '05_frozen_time.mp3'
        if self.tela_estado == 'resultado':
            return ('06_neon_champion.mp3' if self.novo_recorde
                    else '07_digital_results.mp3')
        return None

    def atualizar_musica(self):
        desejada = self.musica_desejada()
        if not self.audio_disponivel or not desejada or desejada == self.faixa_musica:
            return
        arquivo = self.assets.raiz / 'definitivos' / 'audio' / desejada
        try:
            pygame.mixer.music.load(str(arquivo))
            pygame.mixer.music.play(-1, fade_ms=500)
            self.faixa_musica = desejada
        except (pygame.error, OSError):
            self.audio_disponivel = False

    def pontuacao_entra_no_topo(self):
        if self.pontos <= 0:
            return False
        topo = sorted(self.ranking, key=lambda item: item['pontos'], reverse=True)[:5]
        return len(topo) < 5 or self.pontos > topo[-1]['pontos']

    def reset_detectores(self):
        self.detector_punho.reiniciar()
        self.detector_pausa.reiniciar()
        self.detector_vitoria.reiniciar()

    def abrir_calibracao(self):
        self.tela_estado = 'calibracao'
        self.acertos_teste = set()
        self.reset_detectores()

    def abrir_dificuldade(self):
        self.tela_estado = 'dificuldade'
        self.reset_detectores()

    @property
    def fator_dificuldade(self):
        return FATORES_DIFICULDADE.get(self.dificuldade, FATORES_DIFICULDADE['medio'])

    def nova_partida(self):
        self.tela_estado = 'jogando'
        self.modo_partida = self.rastreador.modo
        self.ranking = lista_ranking(self.rankings, self.modo_partida, self.dificuldade)
        self.novo_recorde = False
        self.pontos = self.combo = self.max_combo = self.acertos = self.erros = 0
        self.tempo = PARTIDA_SEGUNDOS
        self.particulas = []
        self.efeitos_visuais = []
        self.combo_visual = None
        self.alvos = []
        self.nome = ''
        self.salvo = False
        self.reabastecer()
        self.reset_detectores()

    def ajustar_config(self, chave, diferenca):
        minimo, maximo = ((0.6, 3.0) if chave == 'sensibilidade' else (0.2, 0.9))
        valor = round(limitar(self.config[chave] + diferenca, minimo, maximo), 2)
        if valor != self.config[chave]:
            self.config[chave] = valor
            if not salvar_config(self.config):
                self.rastreador.mensagem = 'Aviso: não foi possível salvar a configuração.'

    def reabastecer(self):
        quantidade = min(5, 2 + self.nivel)
        while len(self.alvos) < quantidade:
            alvo = criar_alvo(self.largura, self.altura, self.alvos, self.nivel,
                              fator_ritmo=self.fator_dificuldade)
            if alvo is None:
                break
            self.alvos.append(alvo)

    def desenhar_texto(self, texto, fonte, cor, pos, centralizar=False):
        superficie = fonte.render(str(texto), True, cor)
        retangulo = superficie.get_rect(center=pos) if centralizar else superficie.get_rect(topleft=pos)
        self.tela.blit(superficie, retangulo)
        return retangulo

    def cartao(self, rect, cor=PAINEL, borda=(51, 75, 111), arredondar=17, alpha=220):
        caixa = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(caixa, (*cor, alpha), caixa.get_rect(), border_radius=arredondar)
        pygame.draw.rect(caixa, borda, caixa.get_rect(), 1, border_radius=arredondar)
        self.tela.blit(caixa, rect)

    def painel_asset(self, nome, rect):
        img = self.assets.get(f'definitivos/paineis/{nome}.png', rect.size)
        if img:
            self.tela.blit(img, rect)
            return True
        return False

    def draw_sprite_button(self, style, center, size=None, label=None, hover=False, label_color=BRANCO):
        mapa = {
            'calibrar': 'definitivos/botoes/07_button_calibrar.png',
            'iniciar': 'definitivos/botoes/08_button_iniciar_partida.png',
            'continuar': 'definitivos/botoes/09_button_continuar.png',
            'calibrarjogar': 'definitivos/botoes/10_button_calibrar_e_jogar.png',
        }
        if style == 'mini':
            acao = 'mais' if label == '+' else 'menos'
            estado = 'ativo' if hover else 'normal'
            caminho = f'definitivos/calibracao/botao_{acao}_{estado}.png'
        else:
            caminho = mapa.get(style)
        rect = pygame.Rect(0, 0, *(size or (360, 120)))
        rect.center = center
        img = self.assets.fit_box(caminho, rect.size) if caminho else None
        if img:
            self.tela.blit(img, img.get_rect(center=rect.center))
        return rect

    def menu_button_rect(self):
        return pygame.Rect(self.largura // 2 - 180, self.altura - 205, 360, 120)

    def pause_button_rect(self):
        return pygame.Rect(self.largura // 2 - 180, self.altura // 2 + 15, 360, 120)

    def result_button_rect(self):
        return pygame.Rect(self.largura // 2 - 180, self.altura - 190, 360, 120)

    def calibration_controls(self):
        esquerda = pygame.Rect(24, 145, min(600, int(self.largura * 0.48)), 360)
        direita_x = max(esquerda.right + 40, int(self.largura * 0.62))
        return {
            'painel': esquerda,
            'sens_menos': pygame.Rect(esquerda.right - 125, 254, 58, 46),
            'sens_mais': pygame.Rect(esquerda.right - 64, 254, 58, 46),
            'resp_menos': pygame.Rect(esquerda.right - 125, 394, 58, 46),
            'resp_mais': pygame.Rect(esquerda.right - 64, 394, 58, 46),
            'iniciar': pygame.Rect(self.largura // 2 - 180, self.altura - 198, 360, 120),
            'targets_center': (direita_x, int(self.altura * 0.54)),
        }

    def difficulty_card_rects(self):
        img = self.assets.load('definitivos/dificuldade/paineis_dificuldade.png')
        if img:
            ow, oh = img.get_size()
        else:
            ow, oh = 1774, 887
        escala = min((self.largura - 90) / ow, (self.altura - 130) / oh)
        largura, altura = int(ow * escala), int(oh * escala)
        esquerda = (self.largura - largura) // 2
        topo = self.altura // 2 - 10 - altura // 2
        return [
            pygame.Rect(esquerda + int(largura * 40 / ow),
                        topo + int(altura * y1 / oh),
                        int(largura * (1733 - 40) / ow),
                        int(altura * (y2 - y1) / oh))
            for y1, y2 in ((41, 269), (336, 564), (631, 858))
        ]

    def calibration_targets(self):
        base_x = int(self.largura * 0.69)
        base_y = int(self.altura * 0.50)
        dx = int(min(150, self.largura * 0.11))
        dy = int(min(110, self.altura * 0.14))
        return [
            (base_x - dx, base_y - dy),
            (base_x + dx, base_y - dy + 10),
            (base_x - dx + 30, base_y + dy),
            (base_x + dx, base_y + dy - 10),
        ]

    def hit_radius_calibration(self):
        return 34

    def fundo(self):
        nome = ('definitivos/fundos/01_menu_background.png' if self.tela_estado == 'menu'
                else 'definitivos/fundos/02_gameplay_background.png')
        bg = self.assets.cover(nome, (self.largura, self.altura))
        if bg:
            rect = bg.get_rect(center=(self.largura // 2, self.altura // 2))
            self.tela.blit(bg, rect)
            overlay = pygame.Surface((self.largura, self.altura), pygame.SRCALPHA)
            overlay.fill((5, 10, 22, 78 if self.tela_estado == 'menu' else 88))
            self.tela.blit(overlay, (0, 0))
        else:
            self.tela.fill(FUNDO)
            for y in range(0, self.altura, 8):
                fator = y / max(1, self.altura)
                pygame.draw.rect(self.tela, (10, 16 + int(fator * 11), 33 + int(fator * 19)),
                                 (0, y, self.largura, 8))
        for x, y, tam in self.estrelas:
            pygame.draw.circle(self.tela, (41, 65, 99),
                               (int(x * self.largura / W), int(y * self.altura / H)), tam)

    def hud(self):
        slot_w, slot_h, margem = 225, 73, 20
        gap = (self.largura - 2 * margem - 4 * slot_w) // 3
        caixas = [pygame.Rect(margem + i * (slot_w + gap), 12, slot_w, slot_h)
                  for i in range(4)]
        nomes = ('hud_pontos', 'hud_tempo', 'hud_combo', 'hud_nivel')
        for nome, rect in zip(nomes, caixas):
            self.painel_asset(nome, rect)
        # The supplied level panel contains the label art. Correct its missing
        # accent in place and show only the numeric value at the right.
        caixa_nivel = pygame.Rect(caixas[3].x + 18, caixas[3].y + 27, 48, 19)
        remendo = pygame.Surface(caixa_nivel.size, pygame.SRCALPHA)
        remendo.fill((8, 22, 48, 206))
        self.tela.blit(remendo, caixa_nivel)
        fonte_rotulo = pygame.font.SysFont('segoeui', 13, bold=True)
        self.desenhar_texto('NÍVEL', fonte_rotulo, (211, 91, 255),
                            (caixa_nivel.x + 2, caixa_nivel.y + 1))
        pontos = str(self.pontos)
        fonte_pontos = self.fonte_media if len(str(self.pontos)) <= 5 else self.fonte_pequena
        valores = (
            (pontos, fonte_pontos, BRANCO),
            (f'{max(0, math.ceil(self.tempo)):02d}s', self.fonte_media,
             VERMELHO if self.tempo <= 10 else BRANCO),
            (f'x{self.combo}', self.fonte_media, OURO),
            (str(self.nivel), self.fonte_media, BRANCO),
        )
        for indice, (texto, fonte, cor) in enumerate(valores):
            superficie = fonte.render(texto, True, cor)
            retangulo = superficie.get_rect(midright=(caixas[indice].right - 18, 51))
            self.tela.blit(superficie, retangulo)

    def criar_particulas(self, x, y, cor, texto):
        for _ in range(12):
            a = random.uniform(0, math.tau)
            velocidade = random.uniform(85, 225)
            self.particulas.append([x, y, math.cos(a) * velocidade,
                                    math.sin(a) * velocidade, 0.7, cor])
        self.mensagem_flutuante = [texto, x, y, 0.75, cor]
        pontos = int(texto[1:]) if texto.startswith('+') and texto[1:].isdigit() else 0
        tipo = 'bonus' if pontos >= 20 else 'negativo' if texto in ('-15', 'ERRO') else 'normal'
        self.efeitos_visuais.append([
            f'definitivos/efeitos/impacto_{tipo}.png', x, y, 0.28, 0.0, 104
        ])

    def popup_surface(self, texto):
        nomes = {
            '+10': 'pontos_mais_10', '+20': 'pontos_mais_20', '-15': 'pontos_menos_15',
            'ERRO': 'feedback_erro',
        }
        nome = nomes.get(texto)
        if nome:
            return self.assets.fit_w(f'definitivos/feedback/{nome}.png', 136)
        return None

    def efeito_alvo(self, tipo, x, y):
        chave = {'normal': 'normal', 'bonus': 'bonus', 'perigo': 'perigo'}[tipo]
        self.efeitos_visuais.extend((
            [f'definitivos/feedback/alvo_{chave}_atingido.png', x, y, 0.12, 0.0, 88],
            [f'definitivos/feedback/alvo_{chave}_destruido.png', x, y, 0.20, 0.12, 88],
            ['definitivos/efeitos/brilho_do_clique.png', x, y, 0.24, 0.0, 70],
            ['definitivos/efeitos/anel_de_acerto.png', x, y, 0.26, 0.0, 76],
        ))

    def handle_click(self, pos):
        if self.tela_estado == 'menu':
            if self.menu_button_rect().collidepoint(pos):
                self.abrir_calibracao()
            return
        if self.tela_estado == 'calibracao':
            controles = self.calibration_controls()
            if controles['iniciar'].collidepoint(pos):
                self.abrir_dificuldade()
                return
            for chave, ajuste, campo in (
                ('sens_menos', -0.1, 'sensibilidade'),
                ('sens_mais', 0.1, 'sensibilidade'),
                ('resp_menos', -0.05, 'resposta'),
                ('resp_mais', 0.05, 'resposta'),
            ):
                if controles[chave].collidepoint(pos):
                    self.ajustar_config(campo, ajuste)
                    return
            for i, (x, y) in enumerate(self.calibration_targets()):
                if math.hypot(pos[0] - x, pos[1] - y) <= self.hit_radius_calibration():
                    self.acertos_teste.add(i)
                    self.criar_particulas(x, y, VERDE, 'OK')
                    return
            return
        if self.tela_estado == 'dificuldade':
            for chave, rect in zip(('facil', 'medio', 'dificil'), self.difficulty_card_rects()):
                if rect.collidepoint(pos):
                    self.dificuldade = chave
                    self.nova_partida()
                    return
            return
        if self.tela_estado == 'pausado':
            if self.pause_button_rect().collidepoint(pos):
                self.tela_estado = 'jogando'
            return
        if self.tela_estado == 'resultado':
            if self.result_button_rect().collidepoint(pos):
                if not self.salvo:
                    self.gravar_resultado()
                self.abrir_calibracao()
            return
        if self.tela_estado != 'jogando':
            return
        for alvo in reversed(self.alvos):
            if alvo.contem(*pos):
                self.alvos.remove(alvo)
                if alvo.tipo == 'perigo':
                    self.pontos = max(0, self.pontos - 15)
                    self.combo = 0
                    self.erros += 1
                    texto, cor = '-15', VERMELHO
                else:
                    ganho = pontuacao(alvo.tipo, self.combo)
                    self.pontos += ganho
                    self.combo += 1
                    self.max_combo = max(self.max_combo, self.combo)
                    self.acertos += 1
                    texto, cor = f'+{ganho}', OURO if alvo.tipo == 'bonus' else CIANO
                    if self.combo in (2, 3, 5):
                        self.combo_visual = [f'definitivos/efeitos/combo_x{self.combo}.png', 0.8]
                    if self.combo == 5:
                        self.efeitos_visuais.append([
                            'definitivos/efeitos/explosao_combo.png', *pos, 0.36, 0.0, 144
                        ])
                self.efeito_alvo(alvo.tipo, *pos)
                self.criar_particulas(*pos, cor, texto)
                self.reabastecer()
                return
        self.combo = 0
        self.erros += 1
        self.criar_particulas(*pos, CINZA, 'ERRO')

    def gravar_resultado(self):
        if self.salvo:
            return
        try:
            self.ranking = salvar_ranking(self.nome or 'VISITANTE', self.pontos,
                                          self.modo_partida, self.dificuldade)
            self.rankings = ler_ranking()
            self.salvo = True
        except OSError as e:
            self.rastreador.mensagem = f'Não foi possível salvar ranking: {str(e)[:70]}'

    def atualizar_rastreamento(self):
        if self.rastreador.modo != 'camera':
            self.cursor = pygame.mouse.get_pos()
            self.mao_presente = True
            self.gesto_atual = 'mouse'
            return
        leitura = self.rastreador.ler()
        if leitura == 'aguardando':
            return
        if leitura is None:
            self.mao_presente = False
            self.gesto_atual = 'sem mão'
            self.reset_detectores()
            return
        x, y, gesto = leitura
        agora = time.monotonic()
        self.mao_presente = True
        self.gesto_atual = gesto
        if gesto == 'apontando':
            x, y = mapear_mira(x, y, self.largura, self.altura, self.config['sensibilidade'])
            fator = self.config['resposta']
            self.cursor = (self.cursor[0] + (x - self.cursor[0]) * fator,
                           self.cursor[1] + (y - self.cursor[1]) * fator)
        if self.detector_punho.atualizar(gesto):
            self.handle_click(self.cursor)
        if self.tela_estado in ('jogando', 'pausado'):
            if self.detector_pausa.atualizar(gesto == 'palma', agora):
                self.tela_estado = 'pausado' if self.tela_estado == 'jogando' else 'jogando'
        else:
            self.detector_pausa.reiniciar()
        if self.detector_vitoria.atualizar(gesto == 'vitoria', agora):
            if self.tela_estado == 'menu':
                self.abrir_calibracao()
            elif self.tela_estado == 'calibracao':
                self.abrir_dificuldade()
            elif self.tela_estado == 'dificuldade':
                self.nova_partida()
            elif self.tela_estado == 'resultado':
                if not self.salvo:
                    self.gravar_resultado()
                self.abrir_calibracao()

    def atualizar(self, dt):
        self.atualizar_rastreamento()
        for part in self.particulas[:]:
            part[0] += part[2] * dt
            part[1] += part[3] * dt
            part[4] -= dt
            if part[4] <= 0:
                self.particulas.remove(part)
        if self.mensagem_flutuante:
            self.mensagem_flutuante[2] -= dt * 53
            self.mensagem_flutuante[3] -= dt
            if self.mensagem_flutuante[3] <= 0:
                self.mensagem_flutuante = None
        for efeito in self.efeitos_visuais:
            if efeito[4] > 0:
                efeito[4] = max(0, efeito[4] - dt)
            else:
                efeito[3] -= dt
        self.efeitos_visuais = [efeito for efeito in self.efeitos_visuais
                                if efeito[3] > 0 or efeito[4] > 0]
        if self.combo_visual:
            self.combo_visual[1] -= dt
            if self.combo_visual[1] <= 0:
                self.combo_visual = None
        if self.tela_estado != 'jogando':
            self.atualizar_musica()
            return
        self.tempo -= dt
        if self.tempo <= 0:
            self.tempo = 0
            self.novo_recorde = self.pontuacao_entra_no_topo()
            self.tela_estado = 'resultado'
            self.atualizar_musica()
            return
        for alvo in self.alvos[:]:
            alvo.vida -= dt
            if self.nivel >= 3:
                alvo.x += (math.sin(pygame.time.get_ticks() / 420 + alvo.oscilacao)
                           * dt * 32 * self.fator_dificuldade)
                alvo.x = limitar(alvo.x, alvo.raio + 18, self.largura - alvo.raio - 18)
            if alvo.vida <= 0:
                self.alvos.remove(alvo)
                if alvo.tipo != 'perigo':
                    self.combo = 0
        self.reabastecer()
        self.atualizar_musica()

    def draw_target_sprite(self, nome, x, y, raio):
        nomes = {
            'target_normal.png': '04_target_normal.png',
            'target_bonus.png': '05_target_bonus.png',
            'target_perigo.png': '06_target_danger.png',
        }
        img = self.assets.fit_box(f'definitivos/botoes/{nomes.get(nome, nome)}',
                                  (int(raio * 2.7), int(raio * 2.7)))
        if img:
            self.tela.blit(img, img.get_rect(center=(int(x), int(y))))
            return True
        return False

    def desenhar_alvos(self):
        nomes = {'normal': 'target_normal.png', 'bonus': 'target_bonus.png', 'perigo': 'target_perigo.png'}
        cores = {'normal': CIANO, 'bonus': OURO, 'perigo': VERMELHO}
        for alvo in self.alvos:
            x, y, raio = round(alvo.x), round(alvo.y), round(alvo.raio)
            if not self.draw_target_sprite(nomes[alvo.tipo], x, y, raio):
                cor = cores[alvo.tipo]
                aura = pygame.Surface((raio * 4, raio * 4), pygame.SRCALPHA)
                pygame.draw.circle(aura, (*cor, 17), (raio * 2, raio * 2), int(raio * 1.75))
                pygame.draw.circle(aura, (*cor, 35), (raio * 2, raio * 2), int(raio * 1.40))
                self.tela.blit(aura, (x - raio * 2, y - raio * 2))
                pygame.draw.circle(self.tela, PAINEL, (x, y), raio)
                pygame.draw.circle(self.tela, cor, (x, y), raio, 4)
                pygame.draw.circle(self.tela, cor, (x, y), 9 if alvo.tipo == 'normal' else 6)
            if alvo.tipo != 'normal':
                self.desenhar_texto('!' if alvo.tipo == 'perigo' else '*', self.fonte_media,
                                    BRANCO, (x, y - 1), True)
            cor = cores[alvo.tipo]
            vida_maxima = max(1.35, 3.8 - self.nivel * 0.22) / self.fator_dificuldade
            proporcao = limitar(alvo.vida / vida_maxima, 0, 1)
            largura = int(raio * 2 * proporcao)
            pygame.draw.rect(self.tela, (18, 28, 53), (x - raio, y + raio + 8, raio * 2, 4), border_radius=2)
            pygame.draw.rect(self.tela, cor, (x - raio, y + raio + 8, largura, 4), border_radius=2)

    def desenhar_particulas(self):
        for caminho, x, y, tempo, espera, largura in self.efeitos_visuais:
            if espera > 0:
                continue
            efeito = self.assets.fit_w(caminho, largura)
            if efeito:
                copia = efeito.copy()
                copia.set_alpha(max(0, min(255, int(255 * tempo / 0.36))))
                self.tela.blit(copia, copia.get_rect(center=(int(x), int(y))))
        for x, y, vx, vy, vida, cor in self.particulas:
            pygame.draw.circle(self.tela, cor, (int(x), int(y)), max(1, int(4 * vida / 0.7)))
        if self.mensagem_flutuante:
            texto, x, y, vida, cor = self.mensagem_flutuante
            popup = self.popup_surface(texto)
            if popup:
                self.tela.blit(popup, popup.get_rect(center=(int(x), int(y - 24))))
            else:
                sombra = self.fonte_grande.render(texto, True, (0, 0, 0))
                sombra.set_alpha(120)
                srect = sombra.get_rect(center=(int(x) + 2, int(y - 22) + 2))
                self.tela.blit(sombra, srect)
                self.desenhar_texto(texto, self.fonte_grande, cor, (x, y - 22), True)

    def desenhar_cursor(self):
        x, y = int(self.cursor[0]), int(self.cursor[1])
        if self.rastreador.modo == 'camera' and not self.mao_presente:
            return
        if self.tela_estado == 'jogando':
            trilha = self.assets.fit_w('definitivos/efeitos/trilha_da_mira.png', 94)
            if trilha:
                self.tela.blit(trilha, trilha.get_rect(center=(x - 30, y)))
        img = self.assets.fit_w('definitivos/botoes/03_cursor_reticle.png', 58)
        if img:
            self.tela.blit(img, img.get_rect(center=(x, y)))
            return
        pygame.draw.circle(self.tela, (26, 70, 89), (x, y), 23)
        pygame.draw.circle(self.tela, BRANCO, (x, y), 16, 2)
        pygame.draw.circle(self.tela, CIANO, (x, y), 5)
        pygame.draw.line(self.tela, CIANO, (x - 28, y), (x - 19, y), 2)
        pygame.draw.line(self.tela, CIANO, (x + 19, y), (x + 28, y), 2)
        pygame.draw.line(self.tela, CIANO, (x, y - 28), (x, y - 19), 2)
        pygame.draw.line(self.tela, CIANO, (x, y + 19), (x, y + 28), 2)

    def tela_menu(self):
        centro = self.largura // 2
        logo = self.assets.fit_w('definitivos/marca/03_logo_completo_horizontal.png', 520)
        if logo:
            self.tela.blit(logo, logo.get_rect(center=(centro, 190)))
        painel = pygame.Rect(centro - 355, 260, 710, 400)
        self.painel_asset('painel_instrucoes', painel)
        instrucoes = (
            ('18_gesto_apontar_ciano.png', 'Aponte com o indicador para mover a mira.'),
            ('18_gesto_punho_dourado.png', 'Feche o punho para acertar os alvos.'),
            ('18_gesto_palma_verde.png', 'Mantenha a palma aberta para pausar.'),
            ('18_gesto_sinal_V_roxo.png', 'Use o sinal V para abrir a calibracao.'),
        )
        for indice, (icone, texto) in enumerate(instrucoes):
            y = 360 + indice * 39
            img = self.assets.fit_box(f'definitivos/marca/{icone}', (36, 36))
            if img:
                self.tela.blit(img, img.get_rect(center=(centro - 265, y + 8)))
            self.desenhar_texto(texto, self.fonte_texto, BRANCO, (centro - 232, y))
        rect = self.menu_button_rect()
        hover = rect.collidepoint(self.cursor if self.rastreador.modo == 'camera' else pygame.mouse.get_pos())
        self.draw_sprite_button('calibrar', rect.center, rect.size, hover=hover)
        self.desenhar_texto('ENTER ou sinal V', self.fonte_pequena, BRANCO,
                            (centro, self.altura - 70), True)

    def tela_calibracao(self):
        centro = self.largura // 2
        self.desenhar_texto('AJUSTE A MIRA', self.fonte_grande, BRANCO, (centro, 49), True)
        self.desenhar_texto('Ajuste e teste a mira antes de escolher a dificuldade.', self.fonte_texto,
                            CINZA, (centro, 96), True)
        ctr = self.calibration_controls()
        caixa = ctr['painel']
        self.painel_asset('painel_calibracao', caixa)
        self.desenhar_texto('SENSIBILIDADE', self.fonte_media, CIANO, (caixa.x + 28, 194))
        self.desenhar_texto('Maior = menos movimento da mão para cruzar a tela.', self.fonte_pequena,
                            CINZA, (caixa.x + 28, 222))
        barra_sens = self.assets.get('definitivos/calibracao/barra_sensibilidade.png', (350, 59))
        if barra_sens:
            self.tela.blit(barra_sens, (caixa.x + 24, 250))
        faixa_sens = pygame.Rect(caixa.x + 41, 275, 315, 4)
        progresso_sens = (self.config['sensibilidade'] - 0.6) / (3.0 - 0.6)
        marcador = self.assets.fit_box('definitivos/calibracao/marcador_controle.png', (28, 36))
        if marcador:
            self.tela.blit(marcador, marcador.get_rect(center=(
                int(faixa_sens.left + faixa_sens.width * progresso_sens), faixa_sens.centery)))
        self.desenhar_texto(f'{self.config["sensibilidade"]:.1f}x', self.fonte_media,
                            BRANCO, (caixa.right - 180, 255))
        self.desenhar_texto('RESPOSTA DA MIRA', self.fonte_media, CIANO, (caixa.x + 28, 327))
        self.desenhar_texto('Maior = cursor mais rápido; menor = mais estável.', self.fonte_pequena,
                            CINZA, (caixa.x + 28, 355))
        barra_resp = self.assets.get('definitivos/calibracao/barra_resposta.png', (350, 59))
        if barra_resp:
            self.tela.blit(barra_resp, (caixa.x + 24, 383))
        faixa_resp = pygame.Rect(caixa.x + 41, 408, 315, 4)
        progresso_resp = (self.config['resposta'] - 0.2) / (0.9 - 0.2)
        if marcador:
            self.tela.blit(marcador, marcador.get_rect(center=(
                int(faixa_resp.left + faixa_resp.width * progresso_resp), faixa_resp.centery)))
        self.desenhar_texto(f'{int(self.config["resposta"] * 100)}%', self.fonte_media,
                            BRANCO, (caixa.right - 180, 388))
        pos = self.cursor if self.rastreador.modo == 'camera' else pygame.mouse.get_pos()
        for chave, rotulo in (('sens_menos', '-'), ('sens_mais', '+'), ('resp_menos', '-'), ('resp_mais', '+')):
            rect = ctr[chave]
            hover = rect.collidepoint(pos)
            self.draw_sprite_button('mini', rect.center, rect.size, label=rotulo, hover=hover)
        fonte_dica = pygame.font.SysFont('segoeui', 14)
        self.desenhar_texto('Teclas: + / - sensibilidade; [ / ] resposta.', fonte_dica,
                            CINZA, (caixa.x + 28, 447))
        self.desenhar_texto('Punho nos alvos: testar clique.', fonte_dica,
                            BRANCO, (caixa.x + 28, 469))

        self.desenhar_texto('TESTE DE PRECISÃO', self.fonte_media, OURO,
                            (int(self.largura * 0.73), 186), True)
        for i, (x, y) in enumerate(self.calibration_targets()):
            em_cima = math.hypot(pos[0] - x, pos[1] - y) <= self.hit_radius_calibration()
            estado = ('alvo_teste_concluido' if i in self.acertos_teste else
                      'alvo_teste_selecionado' if em_cima else 'alvo_teste_pendente')
            imagem = self.assets.fit_box(f'definitivos/calibracao/{estado}.png', (74, 74))
            if imagem:
                self.tela.blit(imagem, imagem.get_rect(center=(x, y)))
        self.desenhar_texto(f'Testes concluídos: {len(self.acertos_teste)}/4', self.fonte_pequena,
                            VERDE if len(self.acertos_teste) == 4 else BRANCO,
                            (int(self.largura * 0.73), self.altura - 122), True)
        rect = ctr['iniciar']
        hover = rect.collidepoint(pos)
        self.draw_sprite_button('continuar', rect.center, rect.size, hover=hover)

    def tela_dificuldade(self):
        centro = self.largura // 2
        self.desenhar_texto('ESCOLHA A DIFICULDADE', self.fonte_grande, BRANCO,
                            (centro, 43), True)
        caminho = 'definitivos/dificuldade/paineis_dificuldade.png'
        imagem = self.assets.load(caminho)
        cartoes = self.difficulty_card_rects()
        if imagem:
            largura_origem, altura_origem = imagem.get_size()
            escala = min((self.largura - 90) / largura_origem,
                         (self.altura - 130) / altura_origem)
            largura_imagem = int(largura_origem * escala)
            altura_imagem = int(altura_origem * escala)
            imagem = pygame.transform.smoothscale(imagem, (largura_imagem, altura_imagem))
            area = imagem.get_rect(center=(centro, self.altura // 2 - 10))
            self.tela.blit(imagem, area)
        self.desenhar_texto('Clique para começar • teclas 1, 2 ou 3 selecionam; Enter confirma.',
                            self.fonte_pequena, BRANCO, (centro, self.altura - 69), True)
        opcoes = (
            ('facil', 'FÁCIL', 'Alvos duram mais e se movem 70% mais devagar que no difícil.', CIANO),
            ('medio', 'MÉDIO', 'Ritmo 40% abaixo do difícil, para uma partida equilibrada.', OURO),
            ('dificil', 'DIFÍCIL', 'Ritmo atual acelerado em 10%, para desafiar seus reflexos.', ROXO),
        )
        for indice, (chave, titulo, descricao, cor) in enumerate(opcoes):
            rect = cartoes[indice]
            y = rect.centery
            self.desenhar_texto(titulo, self.fonte_media, cor, (centro, y - 16), True)
            self.desenhar_texto(descricao, self.fonte_pequena, BRANCO, (centro, y + 20), True)
            if self.dificuldade == chave:
                self.desenhar_texto('SELECIONADA', self.fonte_pequena, cor,
                                    (rect.right - 125, y - 16), True)

    def tela_pausa(self):
        painel = pygame.Rect(self.largura // 2 - 310, self.altura // 2 - 186, 620, 372)
        self.painel_asset('painel_pausa', painel)
        self.desenhar_texto('Palma aberta por 1,2 s ou ESPAÇO também retomam o jogo.',
                            self.fonte_texto, CINZA, (self.largura // 2, painel.y + 145), True)
        rect = self.pause_button_rect()
        pos = self.cursor if self.rastreador.modo == 'camera' else pygame.mouse.get_pos()
        hover = rect.collidepoint(pos)
        self.draw_sprite_button('continuar', rect.center, rect.size, hover=hover)

    def tela_resultado(self):
        centro = self.largura // 2
        caixa = pygame.Rect(centro - 475, 78, 950, min(570, self.altura - 150))
        self.painel_asset('painel_resultado', caixa)
        self.desenhar_texto(f'{self.pontos} PONTOS', self.fonte_titulo, CIANO, (centro, 194), True)
        self.desenhar_texto(f'{self.acertos} acertos   •   {self.erros} erros   •   Melhor combo: x{self.max_combo}',
                            self.fonte_texto, CINZA, (centro, 250), True)
        self.desenhar_texto('SEU NOME (digite e pressione ENTER para salvar):', self.fonte_pequena,
                            CINZA, (caixa.x + 50, 315))
        campo = pygame.Rect(caixa.x + 50, 345, 300, 54)
        self.cartao(campo, (29, 49, 77), CIANO, 9, 235)
        self.desenhar_texto((self.nome or 'VISITANTE')[:14], self.fonte_media, BRANCO,
                            (campo.x + 15, campo.y + 12))
        self.desenhar_texto('RESULTADO SALVO!' if self.salvo else 'Ainda não salvo', self.fonte_pequena,
                            VERDE if self.salvo else CINZA, (caixa.x + 50, 425))
        ranking = pygame.Rect(centro + 70, 290, 360, 216)
        self.painel_asset('painel_ranking', ranking)
        modo_nome = 'WEBCAM' if self.modo_partida == 'camera' else 'MOUSE'
        dificuldade_nome = {'facil': 'FÁCIL', 'medio': 'MÉDIO',
                            'dificil': 'DIFÍCIL'}.get(self.dificuldade, 'MÉDIO')
        self.desenhar_texto(f'{modo_nome} • {dificuldade_nome}', self.fonte_pequena,
                            CIANO, (ranking.centerx, ranking.y + 34), True)
        medalhas = ('medalha_1_lugar', 'medalha_2_lugar', 'medalha_3_lugar')
        for i, item in enumerate(self.ranking[:5]):
            yy = ranking.y + 66 + i * 28
            if i < 3:
                medalha = self.assets.fit_box(f'definitivos/feedback/{medalhas[i]}.png', (25, 25))
                if medalha:
                    self.tela.blit(medalha, (ranking.x + 24, yy))
            self.desenhar_texto(f'{i + 1}. {item["nome"][:12]}', self.fonte_pequena,
                                BRANCO if i == 0 else CINZA, (ranking.x + 58, yy + 3))
            self.desenhar_texto(str(item['pontos']), self.fonte_pequena, OURO,
                                (ranking.right - 22, yy + 3), True)
        if not self.ranking:
            self.desenhar_texto('Ainda sem pontuações', self.fonte_pequena, CINZA,
                                (ranking.centerx, ranking.y + 105), True)
        pos = self.cursor if self.rastreador.modo == 'camera' else pygame.mouse.get_pos()
        rect = self.result_button_rect()
        hover = rect.collidepoint(pos)
        self.draw_sprite_button('calibrarjogar', rect.center, rect.size, hover=hover)

    def rodape(self):
        yy = self.altura - 40
        pygame.draw.line(self.tela, (52, 72, 98), (18, yy - 16), (self.largura - 18, yy - 16), 1)
        modo = 'WEBCAM' if self.rastreador.modo == 'camera' else 'MOUSE'
        self.desenhar_texto(f'MODO: {modo}   |   C: calibrar   F: tela cheia   M: modo   V: preview   ESC: sair',
                            self.fonte_pequena, CINZA, (24, yy))
        if self.rastreador.modo == 'camera' and self.prever_camera:
            px, py = self.largura - 204, 95
            nome_frame = ('webcam_mao_detectada' if self.mao_presente else
                          'webcam_sem_deteccao' if self.rastreador.preview else 'webcam_normal')
            moldura = self.assets.get(f'definitivos/paineis/{nome_frame}.png', (190, 150))
            if moldura:
                self.tela.blit(moldura, (px, py))
            if self.rastreador.preview:
                preview = pygame.transform.smoothscale(self.rastreador.preview, (172, 120))
                self.tela.blit(preview, (px + 9, py + 20))
        if (self.rastreador.mensagem and self.rastreador.modo == 'mouse'
                and not self.rastreador.mensagem.startswith('Modo mouse')):
            self.desenhar_texto(self.rastreador.mensagem[:110], self.fonte_pequena, OURO, (24, yy - 44))

    def desenhar(self):
        self.fundo()
        if self.tela_estado in ('jogando', 'pausado'):
            self.desenhar_alvos()
            self.desenhar_particulas()
            self.hud()
            if self.tela_estado == 'pausado':
                self.tela_pausa()
        elif self.tela_estado == 'menu':
            self.tela_menu()
        elif self.tela_estado == 'calibracao':
            self.tela_calibracao()
        elif self.tela_estado == 'dificuldade':
            self.tela_dificuldade()
        else:
            self.tela_resultado()
        self.rodape()
        if self.combo_visual and self.tela_estado in ('jogando', 'pausado'):
            caminho, restante = self.combo_visual
            combo = self.assets.fit_w(caminho, 180)
            if combo:
                combo = combo.copy()
                combo.set_alpha(min(255, int(255 * restante / 0.8)))
                self.tela.blit(combo, combo.get_rect(center=(self.largura // 2, 145)))
        self.desenhar_cursor()
        pygame.display.flip()

    def alternar_mouse(self):
        modo_anterior = self.rastreador.modo
        if self.rastreador.modo == 'camera':
            self.rastreador.modo = 'mouse'
            self.rastreador.mensagem = 'Modo mouse ativado manualmente.'
        elif self.rastreador.cap and self.rastreador.landmarker:
            self.rastreador.modo = 'camera'
            self.rastreador.mensagem = 'Modo webcam ativado.'
            self.reset_detectores()
        if (self.rastreador.modo != modo_anterior
                and self.tela_estado in ('jogando', 'pausado')):
            # A rodada pode trocar de controle; classifique pelo modo usado ao
            # encerrar, igual ao modo exibido no rodapé durante a partida.
            self.modo_partida = self.rastreador.modo
            self.ranking = lista_ranking(
                self.rankings, self.modo_partida, self.dificuldade)

    def tratar_evento(self, evento):
        if evento.type == pygame.QUIT:
            self.ativo = False
        elif evento.type == pygame.VIDEORESIZE:
            self.largura = max(1000, evento.w)
            self.altura = max(660, evento.h)
            self.tela = pygame.display.set_mode((self.largura, self.altura), pygame.RESIZABLE)
            if self.tela_estado == 'jogando':
                self.reabastecer()
        elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            self.handle_click(evento.pos)
        elif evento.type == pygame.KEYDOWN:
            if self.tela_estado == 'resultado' and not self.salvo:
                if evento.key == pygame.K_ESCAPE:
                    self.ativo = False
                elif evento.key == pygame.K_RETURN:
                    self.gravar_resultado()
                elif evento.key == pygame.K_BACKSPACE:
                    self.nome = self.nome[:-1]
                elif evento.unicode and evento.unicode.isprintable() and len(self.nome) < 14:
                    self.nome += evento.unicode
                return
            if evento.key == pygame.K_ESCAPE:
                self.ativo = False
            elif evento.key == pygame.K_f:
                if self.tela.get_flags() & pygame.FULLSCREEN:
                    self.tela = pygame.display.set_mode((W, H), pygame.RESIZABLE)
                    self.largura, self.altura = W, H
                else:
                    self.tela = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                    self.largura, self.altura = self.tela.get_size()
            elif evento.key == pygame.K_m:
                self.alternar_mouse()
            elif evento.key == pygame.K_v:
                self.prever_camera = not self.prever_camera
            elif evento.key == pygame.K_c and self.tela_estado in ('jogando', 'pausado', 'menu', 'resultado', 'dificuldade'):
                self.abrir_calibracao()
            elif evento.key == pygame.K_SPACE and self.tela_estado in ('jogando', 'pausado'):
                self.tela_estado = 'pausado' if self.tela_estado == 'jogando' else 'jogando'
            elif self.tela_estado == 'calibracao' and evento.key in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS):
                self.ajustar_config('sensibilidade', 0.1)
            elif self.tela_estado == 'calibracao' and evento.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                self.ajustar_config('sensibilidade', -0.1)
            elif self.tela_estado == 'calibracao' and evento.key == pygame.K_LEFTBRACKET:
                self.ajustar_config('resposta', -0.05)
            elif self.tela_estado == 'calibracao' and evento.key == pygame.K_RIGHTBRACKET:
                self.ajustar_config('resposta', 0.05)
            elif self.tela_estado == 'dificuldade' and evento.key in (pygame.K_1, pygame.K_2, pygame.K_3):
                self.dificuldade = {pygame.K_1: 'facil', pygame.K_2: 'medio',
                                    pygame.K_3: 'dificil'}[evento.key]
            elif evento.key == pygame.K_RETURN:
                if self.tela_estado == 'menu':
                    self.abrir_calibracao()
                elif self.tela_estado == 'calibracao':
                    self.abrir_dificuldade()
                elif self.tela_estado == 'dificuldade':
                    self.nova_partida()

    def executar(self):
        try:
            while self.ativo:
                dt = min(self.relogio.tick(60) / 1000.0, 0.10)
                for evento in pygame.event.get():
                    self.tratar_evento(evento)
                self.atualizar(dt)
                self.desenhar()
        finally:
            self.rastreador.close()
            pygame.quit()


def main():
    parser = argparse.ArgumentParser(description='Gesture Rush — arcade offline com webcam')
    parser.add_argument('--mouse', action='store_true', help='testa jogo sem webcam nem MediaPipe')
    parser.add_argument('--camera', type=int, default=0, help='índice da webcam (padrão 0)')
    parser.add_argument('--sem-preview', action='store_true', help='oculta o vídeo da câmera na tela')
    args = parser.parse_args()
    Jogo(args).executar()


if __name__ == '__main__':
    main()
