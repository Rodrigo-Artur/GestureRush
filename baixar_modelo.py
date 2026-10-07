"""Executar UMA VEZ, COM internet, antes da feira."""
from pathlib import Path
from urllib.request import urlopen
import shutil

URL = 'https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task'
DESTINO = Path(__file__).resolve().parent / 'modelos' / 'hand_landmarker.task'
if DESTINO.exists() and DESTINO.stat().st_size > 1_000_000:
    print(f'Modelo já disponível: {DESTINO}')
else:
    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    print('Baixando modelo oficial MediaPipe (apenas na preparação)...')
    with urlopen(URL, timeout=60) as resposta, open(DESTINO, 'wb') as arquivo:
        shutil.copyfileobj(resposta, arquivo)
    if DESTINO.stat().st_size < 1_000_000:
        DESTINO.unlink(missing_ok=True)
        raise RuntimeError('Download incompleto. Tente novamente antes da feira.')
    print(f'Modelo salvo em: {DESTINO}')
