# Registro do projeto — Gesture Rush

Atualizado em 2026-10-07.

## Objetivo

Jogo offline para feira de ADS, controlado por gestos da mão com webcam ou por mouse, com calibração, pontuação e ranking local.

## Estrutura mantida no Git

- `main.py`: telas, entrada por teclado/mouse/gestos, áudio, ranking e loop do jogo.
- `logica.py`: regras e detectores de gesto.
- `assets/definitivos/`: interface, fundos, alvos, efeitos, marca e as sete trilhas MP3.
- `assets/definitivos/dificuldade/`: arte dos três painéis de seleção.
- `modelos/hand_landmarker.task`: modelo local necessário para a detecção de mão.
- `testes/`: testes-fonte da lógica.
- `requirements.txt`: dependências Python.
- `README.md` e scripts de instalação/execução/empacotamento.

## Funcionalidade registrada

- Música por estado: Neon Awakening no menu; System Calibration na calibração; Reflex Overdrive na partida; Final Countdown nos últimos dez segundos; Frozen Time na pausa; Digital Results nos resultados comuns; Neon Champion quando a pontuação se qualifica para o Top 5.
- Na tela de resultados, o teclado fica reservado ao nome até salvar; Enter salva e Backspace apaga.
- Os valores do HUD são alinhados pela margem direita dos respectivos painéis.
- O áudio é opcional para que a aplicação continue abrindo em máquinas sem saída de áudio disponível.
- Após a calibração, a tela de dificuldade oferece Fácil (33% do ritmo difícil), Médio (66%) e Difícil (110% do ritmo atual). Cada opção ajusta duração dos alvos e movimento lateral; a partida continua com 60 segundos.
- Os painéis de dificuldade usam sprite PNG; os rótulos e explicações são texto do jogo para manter acentuação correta. Mouse inicia ao clicar; teclas 1/2/3 selecionam e Enter inicia. Médio vem pré-selecionado.
- O Top 5 agora usa seis listas independentes: webcam/mouse × fácil/médio/difícil. A categoria acompanha o modo que estiver ativo ao fim da rodada, incluindo alternâncias durante a partida; recorde, música de campeão, salvamento e tela de resultado usam a mesma categoria.
- O ranking JSON migra da lista antiga para um objeto versionado no próximo salvamento. Registros anteriores sem modo/dificuldade ficam preservados em `legado`, sem atribuição arbitrária a um novo quadro.

## Exclusões do Git

`.gitignore` exclui ambientes virtuais, caches, temporários e saídas repetidas do PyInstaller (`build*`, `dist*` e o `.spec` gerado). Os arquivos ignorados permanecem no disco. Assets, músicas, modelo e fontes de teste não são ignorados.

## Repositório remoto

- `origin`: `https://github.com/Rodrigo-Artur/GestureRush.git`.
- Branch publicada: `chore/initial-project-upload`, rastreando `origin/chore/initial-project-upload`.
- O repositório remoto estava vazio antes do envio. O primeiro snapshot foi publicado nessa branch; nenhum arquivo foi enviado diretamente para `main`.

## Validação já realizada

- O carregamento das sete faixas e as mudanças de faixa por estado foram exercitados com o driver de áudio dummy do Pygame.
- Os nomes `maria`, `fernanda` e `carla` foram digitados em eventos de teclado sem acionar os atalhos M, F ou C.
- As builds Windows recentes incluíram os assets e foram empacotadas separadamente por versão.
- Nesta atualização: `py_compile` passou; teste direcionado com Pygame verificou transições de mouse/teclado, vida proporcional dos alvos e seleção nas três opções; a imagem da tela foi revisada visualmente para conferir textos e áreas de clique.
- A build Windows isolada passou no `--help`, e o ZIP final contém executável, sprite de dificuldade, modelo local e trilha principal. Isso confirma o empacotamento dos arquivos, não a experiência com webcam/áudio físicos.
- ZIP entregue fora do repositório: `D:\Downloads\GestureRush_dificuldade_final_20261007.zip`.

## Limitações conhecidas

- Builds PyInstaller existentes são específicas do Windows e estão excluídas do repositório; para Linux, execute o código-fonte com as dependências da plataforma.
- A validação de webcam, áudio físico e gestos ainda precisa ocorrer no computador final da apresentação.
- Os fatores de dificuldade foram validados como regra de código; o equilíbrio percebido deve ser ajustado apenas após comparar partidas reais.

## Atualização de ranking — 2026-10-07

- O ranking mantém seis Top 5 independentes: webcam/mouse × fácil/médio/difícil. Correção: se o controle for alternado durante a rodada, a categoria acompanha o modo ativo ao final; recorde, música de campeão, salvamento e resultado consultam a mesma lista.
- A migração do formato antigo preserva entradas sem metadados em `legado`, sem classificá-las artificialmente nos quadros novos.
- Verificados: compilação Python, teste de migração/persistência, isolamento das seis categorias no Pygame e revisão visual da tela de resultado.
- PyInstaller concluiu; o executável respondeu a `--help` com código 0. O pacote contém 2.291 itens e os assets necessários.
- ZIP entregue: `D:\Downloads\GestureRush_ranking_separado_20261007.zip`.
- Pendentes: teste completo com webcam/áudio físicos e rodada completa no computador da feira; os registros antigos só migram para `legado` quando um novo resultado for salvo.

## Correção do modo exibido no resultado — 2026-10-07

- A captura enviada mostrou rodapé `MODO: MOUSE` com quadro `WEBCAM • FÁCIL`. A causa era atualizar o rodapé durante a rodada, mas manter congelada a categoria do ranking na largada.
- Ao alternar o controle durante a partida/pausa, modo da pontuação e lista consultada agora acompanham o modo ativo. A tela de resultado, a verificação de Top 5 e o salvamento ficam alinhados.
- Validação específica passou: compilação Python, alternância webcam→mouse→webcam durante uma rodada simulada, seleção do quadro correspondente a cada modo e persistência no modo ativo ao final. A build PyInstaller atualizada respondeu a `--help` com código 0; ZIP validado com 2.268 arquivos.
- ZIP atualizado: `D:\Downloads\GestureRush_correcao_modo_ranking_20261007.zip`.

## README detalhado e capturas — 2026-10-07

- README refeito em português para explicar a proposta do jogo, fluxo completo, pontuação, progressão, controles, seis categorias de ranking, sete faixas, instalação/uso e limitações.
- Adicionadas cinco capturas reais das telas do jogo em execução em modo mouse: menu, calibração, dificuldade, partida e pausa. Não foram inventados nomes, placares ou registros.
- Caminho das imagens: `docs/screenshots/`.
- Validação: cinco referências de imagem conferidas no README; todos os PNGs existem com 1280×720, e `git diff --check` passou.
- Próxima verificação: depois da publicação da alteração, abrir o README no GitHub para conferir a renderização da galeria; na máquina de apresentação, substituir/acrescentar captura da webcam apenas com autorização de quem estiver no enquadramento.
