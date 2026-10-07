# Gesture Rush

Jogo offline para feira de **Análise e Desenvolvimento de Sistemas**, controlado por **gestos com a mão** usando webcam e MediaPipe.

## Destaques

- **100% offline** durante a apresentação.
- **Controle por gestos**: apontar, fechar o punho, palma aberta e sinal de V.
- **Tela de calibração** antes da partida para ajustar a sensibilidade da mira.
- **Ranking local** salvo no computador.
- **Assets visuais neon sci-fi** já integrados ao jogo.

## Controles

### Gestos
- **Indicador apontado**: move a mira.
- **Punho fechado**: clique/disparo.
- **Palma aberta por 1,2 s**: pausar/continuar.
- **Sinal de V por 1,2 s**: abrir calibração, iniciar a partida ou avançar.

### Teclado / mouse de apoio
- **ENTER**: abrir calibração, iniciar partida ou salvar resultado.
- **ESPAÇO**: pausa/continua.
- **C**: abre a calibração.
- **M**: alterna entre webcam e mouse.
- **V**: mostra/oculta preview da webcam.
- **F**: alterna tela cheia.
- **ESC**: sair.
- **Mouse**: funciona como modo alternativo para testar tudo sem webcam.
- Na tela de resultados, antes de salvar, o teclado fica reservado ao nome;
  **Backspace** apaga e **ENTER** salva, sem acionar os atalhos do jogo.

## Calibração

Antes de cada partida, o jogo abre uma tela para:

- ajustar **sensibilidade** da mira;
- ajustar **resposta** (suavização/velocidade);
- testar o clique do punho em **4 alvos de treino**.

As configurações ficam salvas em:

`%LOCALAPPDATA%\GestureRush\config.json`

O ranking é salvo em:

`%LOCALAPPDATA%\GestureRush\ranking.json`

## Estrutura dos assets

```text
assets/
  definitivos/
    botoes/      # sprites definitivos, fundos e alvos
    calibracao/  # controles, barras e estados dos alvos de teste
    efeitos/     # impactos, combos e efeitos de mira
    feedback/    # pontuação, alvos atingidos e medalhas
    fundos/      # fundos específicos para menu e partida
    marca/       # logos, ícones e gestos
    paineis/     # calibração, resultado, HUD, ranking e webcam
    audio/       # trilhas em MP3 organizadas por tela e situação
```

Os botões são imagens PNG fornecidas com o projeto; o jogo não desenha rótulos
ou fundos de botão por código. Os PNGs preservam transparência e proporção ao
serem ajustados à tela. A pasta `assets/definitivos` contém os originais usados
pela versão atual e é incluída na build.

## Trilha sonora

As faixas são tocadas em loop e trocadas conforme a tela: **Neon Awakening** no
menu, **System Calibration** na calibração, **Reflex Overdrive** durante a
partida, **Final Countdown** nos últimos 10 segundos, **Frozen Time** na pausa
e **Digital Results** nos resultados comuns. **Neon Champion** toca quando a
pontuação entra no Top 5 atual. Se o dispositivo não tiver saída de áudio, o
jogo continua funcionando sem música.

## Como rodar em desenvolvimento

```bash
python main.py --mouse
```

## Como gerar o executável no Windows

1. Coloque o modelo `hand_landmarker.task` em `modelos/`.
2. Execute:

```bat
instalar_windows.bat
```

3. Depois gere o executável:

```bat
gerar_exe_windows.bat
```

Saída esperada:

`dist\GestureRush\GestureRush.exe`

> Importante: copie a pasta `dist\GestureRush` inteira, não apenas o `.exe`.

## Observações técnicas

- Webcam e MediaPipe são usados **localmente**.
- Nenhuma imagem da câmera é enviada para internet.
- O preview da webcam é apenas visual e não é salvo em arquivo.


## Correções visuais aplicadas

- Substituídos botões genéricos por sprites definitivos de calibração, partida,
  continuação e nova partida.
- Integrados fundos, marca, alvos, cursor, painéis de calibração e resultado,
  HUD, molduras da webcam, medalhas, feedback de pontos e efeitos de combo.
- Mantida a proporção dos sprites ao adaptar a janela e corrigidos elementos que
  invadiam a área do rodapé.
