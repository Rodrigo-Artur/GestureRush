# Gesture Rush

Jogo offline para feira de **Análise e Desenvolvimento de Sistemas**, controlado por **gestos com a mão** usando webcam e MediaPipe.

## Destaques

- **100% offline** durante a apresentação.
- **Controle por gestos**: apontar, fechar o punho, palma aberta e sinal de V.
- **Tela de calibração** antes da partida para ajustar a sensibilidade da mira.
- **Três dificuldades** escolhidas depois da calibração: Fácil, Médio e Difícil.
- **Ranking local** salvo no computador.
- **Assets visuais neon sci-fi** já integrados ao jogo.

## Controles

### Gestos
- **Indicador apontado**: move a mira.
- **Punho fechado**: clique/disparo.
- **Palma aberta por 1,2 s**: pausar/continuar.
- **Sinal de V por 1,2 s**: avançar da calibração para a escolha; na escolha, confirmar a dificuldade selecionada.

### Teclado / mouse de apoio
- **ENTER**: abrir calibração, avançar para a escolha, iniciar a dificuldade selecionada ou salvar resultado.
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
- escolher a dificuldade antes de iniciar a partida.

## Dificuldade

O ritmo altera a duração dos alvos e a velocidade lateral deles nos níveis mais
altos. Difícil acelera o ritmo atual em 10%; Médio fica 40% abaixo do Difícil;
Fácil fica 70% abaixo do Difícil. A partida continua com 60 segundos em todas
as opções. Na tela de escolha, clique em uma opção ou use 1, 2 ou 3 e pressione
Enter. O Médio vem pré-selecionado.

As configurações ficam salvas em:

`%LOCALAPPDATA%\GestureRush\config.json`

O ranking é salvo em:

`%LOCALAPPDATA%\GestureRush\ranking.json`

O Top 5 é separado em seis quadros: **Webcam** e **Mouse**, cada um com
**Fácil**, **Médio** e **Difícil**. Se o jogador alternar entre webcam e mouse
durante a partida, a pontuação é registrada no modo que estiver ativo ao final
da rodada; o ranking e o recorde consultam esse mesmo quadro. Registros antigos
sem esses dados são preservados no campo `legado` do JSON e não são atribuídos
a uma categoria por suposição.

## Estrutura dos assets

```text
assets/
  definitivos/
    botoes/      # sprites definitivos, fundos e alvos
    calibracao/  # controles, barras e estados dos alvos de teste
    dificuldade/ # painéis ilustrados para a escolha de ritmo
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
e **Digital Results** nos resultados comuns. A escolha de dificuldade mantém
**System Calibration**. **Neon Champion** toca quando a
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
