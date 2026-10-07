# Registro do projeto — Gesture Rush

Atualizado em 2026-10-06.

## Objetivo

Jogo offline para feira de ADS, controlado por gestos da mão com webcam ou por mouse, com calibração, pontuação e ranking local.

## Estrutura mantida no Git

- `main.py`: telas, entrada por teclado/mouse/gestos, áudio, ranking e loop do jogo.
- `logica.py`: regras e detectores de gesto.
- `assets/definitivos/`: interface, fundos, alvos, efeitos, marca e as sete trilhas MP3.
- `modelos/hand_landmarker.task`: modelo local necessário para a detecção de mão.
- `testes/`: testes-fonte da lógica.
- `requirements.txt`: dependências Python.
- `README.md` e scripts de instalação/execução/empacotamento.

## Funcionalidade registrada

- Música por estado: Neon Awakening no menu; System Calibration na calibração; Reflex Overdrive na partida; Final Countdown nos últimos dez segundos; Frozen Time na pausa; Digital Results nos resultados comuns; Neon Champion quando a pontuação se qualifica para o Top 5.
- Na tela de resultados, o teclado fica reservado ao nome até salvar; Enter salva e Backspace apaga.
- Os valores do HUD são alinhados pela margem direita dos respectivos painéis.
- O áudio é opcional para que a aplicação continue abrindo em máquinas sem saída de áudio disponível.

## Exclusões do Git

`.gitignore` exclui ambientes virtuais, caches, temporários e saídas repetidas do PyInstaller (`build*`, `dist*` e o `.spec` gerado). Os arquivos ignorados permanecem no disco. Assets, músicas, modelo e fontes de teste não são ignorados.

## Validação já realizada

- O carregamento das sete faixas e as mudanças de faixa por estado foram exercitados com o driver de áudio dummy do Pygame.
- Os nomes `maria`, `fernanda` e `carla` foram digitados em eventos de teclado sem acionar os atalhos M, F ou C.
- As builds Windows recentes incluíram os assets e foram empacotadas separadamente por versão.

## Limitações conhecidas

- Builds PyInstaller existentes são específicas do Windows e estão excluídas do repositório; para Linux, execute o código-fonte com as dependências da plataforma.
- A validação de webcam, áudio físico e gestos ainda precisa ocorrer no computador final da apresentação.
