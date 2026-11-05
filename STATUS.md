# STATUS — Protheus 2610 Lab

Última atualização: 2026-11-03 (correções L1–L9 da revisão em PR)

## Fase atual

Gate final da constituição executado em 03/11/2026 (T051–T053): relatório em
`docs/relatorio-final-2026-11-03.md`. US1–US5 verificadas do zero; US6 concluída para o Gemini (chave de API);
opencode fora desta versão por decisão do dono em 03/11/2026. Publicação pública: só com nova autorização do dono.

## Decisões vigentes

- Releases: 12.1.2610 e 12.1.2510, lado a lado (pedido do dono em 2026-11-02).
- Fonte principal das duas: imagens de comunidade `emebatista/*:1.0.0` (base restaurada), fixadas
  por digest no `.env.example`. Não existe tag 2610 oficial (Docker Hub verificado em 2026-11-02);
  o dono autorizou fonte não oficial.
- Fonte reserva (FR-005, T018): **não implementada nesta versão**. Desvio registrado abaixo.
- Fora: DeskFlow, SmartView, container exclusivo, `docker.sock`, `pid: host`, `privileged`.
- Portas: 2610 → 26234/26321/26181/26432/26020; 2510 → 25234/25321/25181/25432/25020, todas em
  `127.0.0.1` e configuráveis no `.env`.
- Skill TIR: `testes-protheus` 1.3.0 (integração EngPro `tir-test-generator` 5.1.0 no commit
  `41504805e419b72232885f7575d54dfd573fea1b` + complemento Playwright); EngPro clonada no setup,
  não vendorizada.
- Renovação da data de troca de senha do Admin (`stacks/sql/renova-senha-admin.sql`): ver
  "Decisões de governança".

## Concluído (com evidência)

| Tarefa | Evidência |
|---|---|
| Spec Kit (constituição, spec, plan, tasks) | `.specify/memory/constitution.md`, `specs/001-protheus-2610-lab/` |
| T001 baseline | contêineres pré-existentes registrados fora do repositório; todos healthy antes e depois |
| T003 `.env.example` | 8 digests verificados; senhas vazias; `.env` ignorado pelo git |
| T004–T006 wrappers | `plab.ps1` e `plab`: `net`, `ports`, `up`, `down`, `status`, `logs`, `smoke`, `restart`, `setup`, `scan` |
| T009–T012 stack 2610 | subida em 32 s (imagens em cache); login PO UI Admin → 99/01 → menu; sem privilégios extras |
| T013–T016 stack 2510 | primeira subida 283 s (restore da base); login PO UI → menu; AppServer 24.3.1.1, DBAccess 24.1.1.0, License 24.3.0.11 |
| T017 isolamento | `down --volumes` + `up` da 2510 do zero com a 2610 monitorada a cada 5 s: 55/55 ok |
| T019–T021 imagem lab | `lab versions`: Python 3.12.3, TIR 2.14.12, Playwright 1.64.1, Chrome/chromedriver 156.0.8078.80, Node 22.23.4, TDS-LS 2.2.7; usuário `lab` uid 1000; senhas como secrets em `/run/secrets` |
| T023–T025 hello | símbolos conferidos no TDN; `LABHELLO.prw` 541 bytes, CP1252 + CRLF; `lab compile` → `SUCCESS=1` nas duas releases |
| T026–T028 smoke | `plab smoke 2610` → PRONTO; `plab smoke 2510` → PRONTO 2× (com o passo 5, reinício do AppServer) |
| T022 spike TIR | TIR 2.14.12 e 2.14.13rc1 não concluem o Setup no WebApp 26 → issue [totvs/tir#2169](https://github.com/totvs/tir/issues/2169) (enviado com autorização do dono); smoke usa Playwright |
| T029 skill testes-protheus | `validate_package.py` → `ok: true`; 66 testes OK |
| T030–T037 `lab setup` | Claude Code e Codex por login de conta: `testado_ok` nos dois; setup idempotente 2×; credenciais 600 no volume `lab-home` |
| T038 ponta a ponta com IA | Claude no lab criou uma suíte TIR da MATA010 com `tir-test-generator` + `testes-protheus`, somente leitura, sem senha |
| Medição de recursos | duas releases + lab ativos: RAM ~4,7 GB; imagens ~28 GB; volumes ~11 GB |
| T045 pesquisa opencode/Gemini | `research.md` R-07.1: versões `latest` no npm (opencode-ai 1.19.5, @google/gemini-cli 0.66.0) e docs oficiais lidas nos repositórios `sst/opencode` @ `1bf08ae46a91` e `google-gemini/gemini-cli` @ `0ac57c029b84` (sites bloqueados na sessão de nuvem). Gemini não documenta login de conta sem navegador → só `api_key` |
| T046 providers opencode e Gemini | `lab/setup/providers/opencode.sh` (conta: `opencode auth login`; chave: `OPENCODE_API_KEY` ou `ANTHROPIC_API_KEY`) e `gemini.sh` (só `api_key`: `GEMINI_API_KEY`); `lab-setup.sh` com `IAS_SUPORTADAS="claude codex opencode gemini"`, versão no `state.json` e `<ia>_modos` opcional (fluxo de Claude/Codex sem mudança de comportamento). `shellcheck` v0.11.0 (binário oficial, sessão sem Docker): 0 achados em `lab/setup/providers/*.sh`, `lab/tests/*.sh` e `lab-setup.sh`. Teste local com **stubs** (npm, CLIs, doctor e smoke falsos; sem rede de IA): chave digitada por pseudo-TTY não aparece na saída, `secrets.env` 600 sem duplicar, wrapper do opencode exporta só a variável escolhida e nenhuma no modo conta, wrapper do Gemini só `GEMINI_API_KEY`, `settings.json` do Gemini preservado; 2 execuções seguidas com as 4 IAs → estado, instruções, skills e wrappers idênticos |
| T039–T044 cenários de leitura (US5) | 03/11/2026, imagem reconstruída: `lab cenarios 2610` 5/5 e `lab cenarios 2510` 5/5 (produtos, fornecedores, clientes, contas a receber, contas a pagar), todas as 10 sessões saíram por Finalizar, sem reiniciar o License Server |
| T051 verificação do zero (03/11/2026) | clone limpo + wrapper bash; `plab down --volumes` e `up`: 2610 em 74 s, 2510 em 293 s (restore); `lab procedures 2610 08` 1 instalado; `plab smoke 2610` PRONTO; cenários 2610 5/5 e 2510 5/5 (2510 com a senha padrão da imagem). `plab smoke 2510` para no passo 3 com código 22: a base recriada volta à senha padrão (com `$`), e o advpls trava com qualquer `$` (testado: `$` cru, `$$`, `\$` travam; `${VAR}` derruba o advpls com 139). Achados no caminho: falsos OK do `plab scan` no Git Bash (corrigidos) e `plab up lab` reaproveita a imagem existente (use `docker compose ... build` após atualizar o repositório) |
| Revisão independente (PR #2) | achados B2, A1, A4, A5, M1, M2, M3 tratados; demais em andamento (abaixo) |

## Achados verificados

- **Senha expirada na 2510**: base publicada com última troca em 12/10/2025 → login exige troca
  obrigatória. `plab up` renova só a data (padrão: só 2510).
- **Compilar na 2510 derruba o `/app-root`**: o AppServer 24.3 reinicia os HTTP e o REST ocupa a
  porta `SD`. Mitigação: RPO próprio para `P2510D`, interface antes da compilação, reinício no passo 5.
- **advpls**: ignora SIGPIPE; includes locais graváveis com nomes em maiúsculas; `$` na senha trava
  (código 22); caminho do RPO em minúsculas no Linux (`rpo-init`).
- **Licenças de desenvolvimento**: sessões encerradas sem "Log Off → Finalizar" não devolvem a
  licença e a 3ª ou 4ª sessão seguida recebe "Erro de servidor de licença: -20 — Excedeu número de
  licenças". Correção: `plab_pw.sair_do_sistema` ao fim de todo teste de interface (sucesso ou
  falha). Verificado: 5 sessões seguidas na 2610 sem erro de licença.
- **Procedures na 2610**: FINA050 exigia o processo 08 na assinatura 013 e a base trazia 012.
  Com autorização do dono (02/11/2026), o processo 08 da empresa 99 foi instalado pelo Gestor de
  Procedures (CFGX051M) a partir do pacote .ZSPS do RPO (19/05/2026): resumo 1 sucesso, 0 falhas;
  `TOP_SP` com as 11 procedures em 013; Contas a Pagar abriu com a grade carregada. Automatizado em
  `lab procedures 2610 08` (reexecução: "Ignorada", código 0). O gestor não fecha por Esc,
  Confirmar nem X da aba; a licença é liberada com `plab restart 2610`.
- **Senha sem vencimento (03/11/2026, pedido do dono)**: testado na 2510 com a data da última troca
  voltada para 12/10/2025 e `lab ui 2510` depois de reiniciar o AppServer. Controle (política 90 dias):
  "Alterar senha". Continuou pedindo a troca com: política `usr_qtdexppsw=0`; política e grupo
  DEFAULT `*` em 0; prazo do próprio Admin em 999 dias. Ou seja, zerar o prazo no banco não tira o
  vencimento nesta base, e o TDN ("Configure a safe password rule") não documenta valor "nunca vence".
  Base devolvida ao estado anterior e `lab ui 2510` OK. A renovação da data no `plab up` continua.
- **`sair_do_sistema` gravava formulário aberto**: o "Finalizar" de uma rotina (Política de senhas do
  SIGACFG) foi clicado como se fosse o do Log Off e gravou tamanho mínimo 8 e máscara `#Aa9X` na
  política da 2510 (revertido para 1 e vazio). Correção: "Finalizar" só depois de clicar em "Log Off".
  Verificado: cenários 2610 5/5 e 2510 5/5, `plab smoke` PRONTO nas duas.
- **Senha em captura de tela**: numa falha de login a captura mostrou a senha digitada no campo de
  usuário (o formulário PO UI redesenhou entre os preenchimentos). Correção: o login confere os dois
  campos antes de clicar e toda captura limpa o formulário de login antes. Capturas de falha da
  etapa de login foram apagadas das evidências locais. Risco restante: capturas do próprio TIR
  (`lab tir`) não passam por essa limpeza, e o `plab scan` não lê imagens.

## Em andamento

- Revisão independente: L1–L9 (issues #6–#14) corrigidos em PR, um commit por issue, aguardando
  validação do dono no lab (`plab up`, `plab smoke` e `lab cenarios` nas duas releases). Situação
  de cada item em `docs/revisao/RESOLUCAO-2026-11-03.md`. Validado sem container: `shellcheck`
  0.11.0, `bash -n`, `docker compose config` e 7 testes locais novos em `lab/tests/` (no CI).
  Fora do PR: o laço "Enter vazio → repetir ou pular" do `segredo_ler` (L6).
- Compilação na 2510 do zero exige trocar a senha do Admin por uma sem `$`.

## Pendências

- **T047 (US6)**: 03/11/2026. Idempotência com as 4 IAs OK. **Gemini `testado_ok` com chave de API** do dono (teste com `gemini-2.5-flash`; o modelo padrão respondeu 503 por demanda). Login de conta Google funciona, mas o Google recusa o plano gratuito de conta pessoal para o Gemini CLI (`UNSUPPORTED_CLIENT`, research R-07.4). **opencode fora desta versão por decisão do dono em 03/11/2026**: o provider continua no código e instala (wrapper e 36 skills), mas fica `nao_testado` e não entra nos critérios de pronto.
- Conferir a versão da LIB pela interface (2610: autor declara 20261016).

## Desvios registrados

- **US6 / opencode**: fora desta versão por decisão do dono em 03/11/2026. Provider mantido no código, sem login testado.
- **FR-005 / T018 (fonte reserva)**: fora desta versão. As reservas exigem outro layout de volumes,
  ini e senhas, e testá-las de ponta a ponta dobra o download (~25 GB). Mitigação: digests fixos das
  imagens principais e documentação das reservas no README. Revisitar se as imagens principais
  sumirem.

## Decisões de governança

- **Renovação da data de troca de senha do Admin** (M2 da revisão): decisão técnica do agente em
  2026-11-02, **mantida pelo dono em 03/11/2026** depois do teste que mostrou que zerar o prazo
  (política, grupo ou usuário) não tira o vencimento. Motivo: a base 2510 da imagem já nasce com a senha vencida pela política, e o login
  automatizado não pode passar pela troca obrigatória. Não altera a senha nem desliga a política;
  só atualiza `usr_dtchgpsw` do usuário 000000. Aplicada só nas releases de
  `PLAB_RENOVAR_SENHA_ADMIN` (padrão 2510). A senha do banco é lida dentro do container.
- **Senha do Admin da 2510 do lab** trocada pelo fluxo "Alterar senha" do Protheus por uma sem `$`
  (autorizado pelo dono), por causa do travamento do `advpls`.
  Refeita em 03/11/2026 (autorizado pelo dono) depois de recriar a base: senha de 16 caracteres
  gerada no container e gravada só no `.env`; `plab smoke 2510` → PRONTO nos 5 passos.

## Cenário pedido-compra (03/11/2026, noite)

- Sugestão de um comentário no LinkedIn (Pedido de Compra com alçada). Menu do módulo Compras
  explorado nas duas releases; a rotina está em Atualizações > Pedidos > Pedidos de Compra.
- `lab cenarios 2610` → 6/6 (`2610/cenarios-20261103-201603`); `lab cenarios 2510` → 6/6
  (`2510/cenarios-20261103-202412`), todas as sessões saindo por "Log Off → Finalizar".
- Alçada não testada: a base de demonstração das duas releases tem 1 pedido (000001, 14 itens)
  já liberado (`C7_CONAPRO = L`), `SCR` vazia, `SAL` inexistente, `SAK` vazia (2610) ou
  inexistente (2510) e `MV_APRPCEC` = F (consulta somente leitura). Proposta na issue #16.
- Correção: `lab/tir/explorar_menu.py` não saía por "Log Off → Finalizar" e prendia licença de
  desenvolvimento a cada exploração. Agora sai pelo `sair_do_sistema` ("saida: ok" nas 4 explorações
  seguintes). As 3 sessões presas antes da correção foram liberadas com `plab restart 2610`.
- O container `lab` em uso recebeu os dois arquivos por `docker cp`; quem atualizar o repositório
  precisa reconstruir a imagem (`docker compose ... build`), como já registrado.

## Validação dos PRs #17–#19, cópia da base e incidente da 2610 (03–04/11/2026)

- PR #17 (L1–L9) validado no lab antes do merge: testes 8/8 no Linux, rede com label, `*-init`
  sem sobrescrever, lab com `cap_drop: ALL`, Postgres sem root, smoke PRONTO e cenários 6/6 nas duas.
- PR #18 (modo desenvolvimento): `PLAB_LAB_DEV=1` monta `lab/`, `cenarios/` e `skills/` somente
  leitura pelo `plab` e pelo `plab.ps1`; desligado, volta ao código da imagem. Validado e desligado.
- PR #19 (`lab menus`): o mapa parava em 2 grupos nas duas releases. Correção: na 2510 o clique pelo
  componente mapeia os 13 grupos de Atualizações do módulo Compras (completo: sim); na 2610 o mapa
  continua parcial (issue #20). Diferenças já vistas: Controle Orçamentário, Dados Adicionais do
  Produto e Características do Produto só na 2610; Cadastros 30 × 28.
- Issue #20 resolvida em 05/11/2026: na 2610 o `lab menus` passou a abrir uma sessão por grupo
  (`lab/tir/mapear_por_grupo.py`); se um grupo falhar e tiver subgrupos, cada subgrupo vira uma
  sessão. `lab menus 2610 2`: 20 sessões, 20 grupos, completo: sim, 39 min. `lab menus-diff 2` em
  Atualizações: 26 itens só na 2610 (Controle Orçamentário com 6 subgrupos, Dados Adicionais e
  Características do Produto), 0 só na 2510, Cadastros 30 × 28.
- **Incidente**: a primeira versão do `plab snapshot/restore` (não publicada) copiava a base com
  `CREATE DATABASE ... TEMPLATE`. Depois do restore a 2610 recusou todo login com "O tipo do ambiente
  encontrado está inválido, é necessária uma redefinição no Configurador". As tabelas eram idênticas;
  a causa provável é o banco ter virado outro objeto para o Postgres. O dono recriou a 2610
  (`plab.ps1 down 2610 -Volumes`, autorizado e executado por ele em 03/11/2026); `plab up 2610` em
  96 s, `lab procedures 2610 08` e smoke PRONTO. A 2510 não foi afetada.
- `plab snapshot/restore` refeito copiando o volume inteiro do Postgres com a release parada.
  2510 (bash): cópia 93 s, restauração 55 s, tabela-marcador desfeita, cenários 6/6 depois do
  restore. 2610 (PowerShell): cópia ~50 s, restauração ~47 s, marcador desfeito, login normal.
- Login da 2610: aviso intermitente "Não foi possível enviar a requisição" na tela de sessão
  (cerca de 1 em 6 sessões, só depois das 21h de 03/11, quando o relógio do lab em UTC já marcava
  04/11; causa não confirmada). Repetir o "Entrar" não resolve; o `lab cenarios` agora refaz o
  cenário desde o login, uma vez, só nesse sintoma, e conta `repeticoes=R` no resumo.
- O "Entrar" não é mais repetido (no lab, 3 de 3 repetições falharam): ao ver o aviso, o login
  desiste na hora e o `lab cenarios` / `lab smoke` refaz desde o login, uma vez, só nesse sintoma.
  Investigação da causa na issue #21.
- Validação final (04/11/2026, 01:36–02:16): `plab smoke 2610` PRONTO; `lab cenarios 2610` 6/6 com
  1 repetição (`2610/cenarios-20261104-014048`); `plab smoke 2510` PRONTO com o passo 5;
  `lab cenarios 2510` 6/6 (`2510/cenarios-20261104-020304`). Testes `lab/tests/` e shellcheck ok.

## Cenários da fase 2 (04/11/2026)

- Os 20 da proposta `docs/propostas/cenarios-fase2.md` viraram 25 entradas novas em
  `cenarios/ui-leitura/cenarios.json` (31 no total), todas somente leitura, rodadas uma a uma nas
  duas releases (`lab cenarios <rel> <nome>`, evidências em `evidencias/<rel>/cenarios-20261104-*`).
- Novos recursos do runner, todos sem gravar dado de negócio: `parametros: "ok"` (confirma a tela
  Pergunte com os valores padrão), `help` (Help esperado no lugar do browse, fechado com "Fechar")
  e `visualizar: true` (abre o 1º registro em Visualizar, captura, fecha com Cancelar/Fechar e
  confere a volta do browse).
- Achados: na 2610 a Atualizar Cotações (MATA150) abre o "Comunicado Ciclo de Vida de Software"
  (rotina descontinuada, manutenção encerrada em 30/06/2025); na 2510 não, e o cenário fica só na
  2510. A Liberar de Documentos dá o Help A097APROV para o Admin nas duas releases. A base não tem
  cotações, inventário nem pedidos liberados (browse vazio ou Help RECNO). O título do inventário
  vem como "Digitaçäo" (com "ä"). O pedido de compra 000001 abre em Visualizar com os 14 itens.
- Bateria completa com o JSON final (04/11/2026, 06:15–08:28): `lab cenarios 2610` total=31
  falhas=0 pulados=1 (cotações) repeticoes=0 (`2610/cenarios-20261104-061533`); `lab cenarios 2510`
  total=31 falhas=0 pulados=0 repeticoes=0 (`2510/cenarios-20261104-071929`).
- Ficaram fora: a conferência de valores contra SQL (saldo, posição de cliente, contagem de itens)
  e as gravações opcionais (C3, E3, F3, V5), feitas depois na seção seguinte.

## Cenários de gravação (04/11/2026)

- Autorização do dono no chat em 04/11/2026: "pode seguir com as gravações usando snapshot".
- Cópia antes de tudo: `plab snapshot <rel> antes_gravacao_20261104` nas duas releases (13:10–13:13).
  Base de partida conferida por SQL (só leitura), igual nas duas: SED 27, SE4 3, SC1 51 (última
  000092), SB7 0, IND.001/01 com `B2_QATU` 197 e `B2_SALPEDI` 0, `MV_SCSLDBL` e `MV_APROVSC` = .F.
- Novo `lab gravacoes <rel> [nome]` (`cenarios/ui-gravacao/gravacao_ui.py` + `gravacoes.json`):
  inclui um registro de teste pela rotina, confere no browse, exclui pela própria rotina e confere
  que sumiu. Recusa sem `PLAB_GRAVACAO_AUTORIZADA=sim` (código 3). Quatro cenários: C3
  solicitacao-compras (MATA110), F3 natureza (FINA010), V5 condicao-pagamento (MATA360) e E3
  inventario (MATA270; o acerto MATA340 nunca roda).
- Bateria final com a base restaurada (15:10–15:32): `lab gravacoes 2610` total=4 falhas=0
  (`2610/gravacoes-20261104-151001`); `lab gravacoes 2510` total=4 falhas=0
  (`2510/gravacoes-20261104-152115`). SQL depois: contagens ativas iguais às de partida, os quatro
  registros de teste com `D_E_L_E_T_ = '*'`, `B2_QATU` 197 e `B2_SALPEDI` 0. Nas rodadas individuais
  a SC somou 1 em `B2_SALPEDI` na inclusão e tirou na exclusão.
- Depois: `plab restore <rel> antes_gravacao_20261104` nas duas; SQL sem nenhuma linha de teste.
  Regressão de leitura: `lab cenarios <rel> naturezas-visualizar` e `solicitacao-compras` ok.
- Achados: campo com espaços até o tamanho faz o foco pular no 1º caractere (é preciso selecionar
  tudo antes de digitar); no "Pesquisar" o Ctrl+A digita "a", o Enter não pesquisa e a busca vazia
  dá Help PESQ01; MATA110 e MATA270 reabrem a inclusão depois de salvar; a FINA010 pergunta
  "Confirma Exclusão?"; a numeração da SC não volta com `plab restore` (000093 → 000096 na 2610).
- Copias `antes_gravacao_20261104` mantidas nas duas releases (apagar com `plab snapshot-rm`).
- Correção no `plab scan` (04/11/2026): o item "docker logs plab-*" nunca tinha rodado. No
  PowerShell 5.1 as aspas do `--format` sumiam, o template falhava (`function "com" not defined`) e
  todos os containers eram pulados, dando 0. Agora lê os rótulos em JSON, mostra quantos containers
  varreu e vira N/VER se não achar nenhum. Rodada nova: zero ocorrências com `containers=13`.
- `lab licencas` (melhoria 5) fora: a porta do monitor abre o assistente de ativação do License
  Server (TOTVS Id e token), não uma lista de licenças, e o log de hoje não registra consumo por
  usuário. Achados de passagem (WARN a cada 10 s causado pelo healthcheck; AppServer reconectando
  com `FAILED TO NOTIFY THREAD RELEASE`) registrados na issue #27, sem correção aplicada.

## Includes da 2510 (04/11/2026, issue #5)

- A imagem AppServer 2510 não tem nenhum `.ch` (a 2610 tem 139). Não há fonte pública oficial: a
  TOTVS distribui pelo Portal do Cliente. O dono indicou os includes do pacote de fontes padrão da
  2510 que ele tem no Drive (167 `.ch`, formato `#zip` como os da imagem 2610).
- Novo `plab includes 2510 <pasta>` (bash e PowerShell): copia a pasta para o volume local
  `plab-lab_includes-2510` (com links de nome em maiúsculas e minúsculas e sentinela), montado
  somente leitura no lab. Nada é versionado. O `compile.sh` usa `PLAB_INCLUDES`, depois os da
  release, depois os da imagem 2610, e escreve na 1ª linha do `compile.log` qual conjunto usou.
- Verificação: `plab.ps1 includes 2510 <pasta do Drive>` → 167 `.ch`, 196 links; `lab compile 2510`
  de um fonte com `#include "protheus.ch"` e `"totvs.ch"` → SUCCESS; com include inexistente →
  `C2090 File not found`. `plab smoke 2510` PRONTO (5 passos, log com "includes da 2510") e
  `plab smoke 2610` PRONTO (log com "includes da imagem 2610"). O fonte de teste LABINC ficou no
  RPO de compilação da 2510 do lab.

## Alçada do Pedido de Compra (05/11/2026, issue #16)

- Pedido do dono: "planeje e execute o que francisco pediu" e "siga até o final". Cópias antes:
  `antes_alcada_20261104` (2510) e `antes_alcada_20261105` (2610); `plab restore` nas duas no fim,
  conferido por SQL (sem aprovadores, 1 usuário, `MV_APRPCEC = F`, nenhum PC novo).
- Configuração pela interface (usuário `labapr1`, perfis, aprovadores, grupos com centro de custo);
  só `MV_APRPCEC = T` foi ligado por SQL. Roteiros em `cenarios/ui-alcada/`, resultado em
  `docs/propostas/alcada-compras.md`.
- Resultado igual nas duas releases: o centro de custo do item escolhe o grupo (AL1/AL2); o
  pedido acima do teto do perfil entra **liberado sem alçada** (AL3); a ausência por "Pendências de
  subordinados" transfere a pendência ao superior e guarda o aprovador original (AL4).
- Diferença entre releases: "Substituição de Aprovadores" é uma tela nova na 2610 e na 2510 exige
  Smart Schedule (Help `A230CONFIG`).
- Base 2610: 25 sequências de RECNO atrasadas fazem a inclusão de usuário cair com chave duplicada
  (issue #30); ajustadas só no banco do lab para o teste.
- `plab_pw.preencher_celula` passa a achar células em grade MVC (`wa-tgrid`).
- Tela nova da 2610 (AL6, mesmo dia, pedido "siga até o final"): cópia `antes_subst_20261105`,
  alçada montada de novo pelos roteiros, transferência **pontual** do PC 000005 do aprovador de
  teste para o Admin pela "Substituição de Aprovadores" ("Os documentos foram transferidos com
  sucesso."; `SCR` com `CR_APRORI`/`CR_USERORI` e `CR_TPTRAN = 3`) e aprovação pelo Admin
  (`C7_CONAPRO = L`). A temporária exige Smart Schedule também na 2610. `plab restore` no fim,
  conferido por SQL (sem `SCR`/`SAK`, sem `labapr1`, `MV_APRPCEC = F`; as 2 linhas apagadas do PC
  000002 na SC7 são da base da imagem, iguais na 2510). Novo roteiro `al_subst.py`.
- A numeração automática não volta com o `plab restore` (usuário veio `000002`, Admin virou
  aprovador `000003`): `al_config.py` lê o código gerado ou recebe `AL_USR`/`AL_APR_*`.

## Divulgação

- 03/11/2026 (autorizado pelo dono: "já pode fazer agora no LinkedIn"), conta Daniel Montagna:
  - artigo: https://www.linkedin.com/pulse/protheus-2610-e-2510-lado-com-testes-de-tela-ia-o-que-montagna-7rt5f/
    (texto conferido por hash contra `divulgacao/TEXTOS-PARA-APROVAR.md`; capa e 6 imagens);
    o LinkedIn gerou o cartão automático do artigo no feed, sem texto;
  - post com o carrossel (PDF, 9 páginas): https://www.linkedin.com/feed/update/urn:li:activity:7523461833916362752/
    (texto idêntico ao aprovado);
  - primeiro comentário com o link do artigo, o e-book e o "Comente LAB" (repositório ainda privado).
- 03/11/2026, depois da abertura do repositório (feita pelo dono; `gh repo view` → PUBLIC e acesso
  anônimo HTTP 200):
  - página https://lp.protheusialab.com.br/lab/ no ar (HTTP 200, capa e 2 prints carregando);
    menu e rodapé da rede com 11 itens nas 9 páginas (`propagate.py` OK); backups `.bak_lab_20261103_1738`;
  - primeiro comentário editado: "Comente LAB" trocado pelos links do repositório e da página
    (conferido após recarregar; ninguém tinha comentado "LAB");
  - resposta ao único comentário do post (sugestão de Pedido de Compra com alçada como cenário),
    autorizada pelo dono;
  - artigo atualizado: o parágrafo "Próximos passos" agora traz os links do repositório e da página
    (conferido na versão pública);
  - bundle de backup do histórico apagado, como combinado.
- 03/11/2026, noite: calendário da Fase 4 aprovado pelo dono ("aprovado, pode publicar o post 1
  amanhã"). Post 1 (repositório aberto) agendado no LinkedIn para qua 04/11 às 08:30, com o print do
  smoke e texto alternativo; texto aprovado com dois ajustes de fato (6 cenários, com Pedido de
  Compra, e issues sem número fixo). Segunda resposta ao comentário do Pedido de Compra com o
  resultado e o link da issue #16.
- 04/11/2026, 08:35: terceira resposta ao comentário do Pedido de Compra (texto aprovado pelo
  dono: "pode publicar assim"), depois do merge do PR #23: 7 cenários de Compras nas duas
  releases, visualização do pedido 000001, Help A097APROV, comunicado da MATA150 na 2610 e link do
  `cenarios/README.md`. Conferida uma vez só, após recarregar a publicação.

## Conferência pré-publicação (03/11/2026)

- Autorização do dono para abrir o repositório e seguir o plano: "Tudo aprovado e siga conforme suas
  sugestões e já siga com a página também" (03/11/2026).
- Revisão independente (PR #2) incorporada: `docs/revisao/` traz o relatório e a situação de cada
  achado (17 resolvidos; 12 de severidade baixa ou desvio registrado viram issues públicas).
- `plab scan`: zero ocorrências em todos os itens (gitleaks, histórico, imagem, container lab,
  docker logs, evidências e arquivos versionados).
- `git ls-files`: sem `.env`, evidências, chaves, RPO, includes ou bundles.
- `plab smoke 2610` → PRONTO (evidências `2610/20261103-173443`); `plab smoke 2510` → PRONTO, com
  o passo 5 de recuperação ok (evidências `2510/20261103-173741`). Cenários de leitura 5/5 nas duas
  releases (12:29 e 12:36 do mesmo dia).
- E-mail dos commits mantido: o dono já o usa em commits de outros repositórios públicos, e os PRs
  #1 e #2 guardam o commit original de qualquer forma. Reescrever o histórico não esconderia nada.

## Bloqueios

Nenhum.

## AGUARDANDO_USUARIO

- Próximos passos de git e divulgação: ver `docs/plano-publicacao.md`.

## Riscos

- R1 login PO UI × TIR: confirmado (totvs/tir#2169); mitigado com Playwright.
- R2 License Server exigir `/dev/mem` no WSL2: não ocorreu; override opcional mantido.
- R3 imagens de comunidade sem licença declarada: digest fixo; reserva não implementada (desvio).
- R4 RAM das duas releases juntas: medida (~4,7 GB).
- R5 licenças de desenvolvimento limitadas: sessões precisam sair pelo "Sair".

## Emendas da constituição

- v1.0.0 adotada em 2026-11-02.
- v1.0.1 (2026-11-02, PATCH): exemplo do Princípio IV trocado por texto genérico, sem nomes de
  stacks locais (achado A4 da revisão independente).
