---

description: "Task list for Protheus 2610 Lab (releases 2610 e 2510)"
---

# Tasks: Protheus 2610 Lab (releases 12.1.2610 e 12.1.2510)

**Input**: Design documents from `specs/001-protheus-2610-lab/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: a spec exige verificação com evidência (Princípio III) e idempotência (FR-013), então
cada história termina com tarefas de verificação. Cada tarefa concluída = atualizar `STATUS.md` +
commit local em português (Princípio VI).

**Organization**: tarefas agrupadas por história de usuário.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: pode rodar em paralelo (arquivos diferentes, sem dependência pendente)
- **[Story]**: história da spec (US1..US6)

---

## Phase 1: Setup

**Purpose**: esqueleto do repositório e baseline da máquina

- [x] T001 Registrar baseline das stacks existentes (`docker ps`, `docker stats --no-stream` das stacks pré-existentes) em `evidencias/baseline/antes.txt` e criar `STATUS.md` com fase 0, decisões da research e AGUARDANDO_USUARIO vazio
- [x] T002 [P] Criar estrutura de diretórios do plan (`stacks/2610`, `stacks/2510`, `stacks/reserva`, `lab/{bin,setup/providers,setup/lib,tests}`, `skills`, `templates`, `cenarios/hello`, `evidencias/.gitkeep`) e `LICENSE` MIT
- [x] T003 [P] Criar `.env.example` conforme `contracts/env-contract.md`: grupos imagens, portas (2610 → 26234/26321/26181/26432/26020; 2510 → 25234/25321/25181/25432/25020), ambientes, nomes de senha **vazios**, versões do lab e das IAs; ajustar `.gitignore` para `.env` e `evidencias/**` exceto `.gitkeep`

---

## Phase 2: Foundational (bloqueia todas as histórias)

**Purpose**: wrapper do host e rede compartilhada

- [x] T004 Implementar `plab.ps1` (Windows PowerShell 5.1) com `net`, `ports`, `up`, `down`, `status`, `logs` conforme `contracts/plab-cli.md`: lê `.env`, recusa porta ocupada (saída 4), `down --volumes` exige digitar o id da release, nunca aceita senha por argumento
- [x] T005 [P] Implementar `plab` (bash) com o mesmo contrato de T004
- [x] T006 Verificar `plab net` idempotente (2 execuções, 1 rede `plab`) e `plab ports` listando as 10 portas livres; registrar evidência em `STATUS.md`

**Checkpoint**: wrapper pronto; histórias podem começar

---

## Phase 3: User Story 1 - Subir 12.1.2610 e entrar no WebApp (Priority: P1) 🎯 MVP

**Goal**: stack 2610 (emebatista, digest fixo, sem DeskFlow/SmartView) saudável, login no WebApp

**Independent Test**: `plab up 2610` → 4 serviços healthy → `http://127.0.0.1:26321` → login Admin → versões anotadas

- [x] T007 [US1] Fazer `docker pull` das 4 imagens `emebatista/*-2610:1.0.0`, anotar digest completo e tamanho; gravar digests em `.env.example` (`PLAB_2610_IMG_*` = `repo:tag@sha256:<64hex>`)
- [x] T008 [US1] Inspecionar sem copiar para o repo: `docker image inspect` (entrypoint, env, portas, healthcheck) e `appserver.ini`/`dbaccess.ini` de dentro da imagem `protheus-2610` (ambientes P2610/P2610_COMPILA, portas 1234/4321/8181, alias de dbaccess e license); registrar achados em `specs/001-protheus-2610-lab/research.md` seção "Achados do spike 2610"
- [x] T009 [US1] Escrever `stacks/2610/compose.yaml` (project `name: plab-2610`, sem `container_name`, volumes nomeados, redes `default` + externa `plab` com aliases `*-2610`, portas `127.0.0.1:${PLAB_2610_PORT_*}`, healthchecks em todos os serviços, `mem_limit` por serviço, degrau (a) sem privilégios)
- [x] T010 [US1] Subir a 2610 aplicando a escada de privilégio (a → b `security_opt systempaths/apparmor unconfined` → c `/dev/mem`+`SYS_RAWIO` → d `privileged`), parando no primeiro degrau que deixa license e appserver healthy; registrar resultado de cada degrau em `STATUS.md` e, se ≥ c, preencher Complexity Tracking do `plan.md`
- [x] T011 [US1] Validar login no WebApp 2610 em `http://127.0.0.1:26321` com Admin (senha só via `.env` local), capturar tela pós-login em `evidencias/2610/spike/`, anotar versões AppServer/DBAccess/LIB/WebApp/License
- [x] T012 [US1] Medir RAM (`docker stats --no-stream`) e disco (`docker system df -v` do project) da 2610 e conferir as stacks pré-existentes ainda healthy; registrar em `STATUS.md`

**Checkpoint**: US1 funcional e verificada (commit "feat(2610): stack 2610 de pé")

---

## Phase 4: User Story 2 - 12.1.2510 lado a lado (Priority: P1)

**Goal**: stack 2510 coexistindo com a 2610, com reserva oficial documentada

**Independent Test**: 2610 e 2510 healthy juntas; `down --volumes` só da 2510 não afeta a 2610

- [x] T013 [US2] Pull + digests das imagens `emebatista/*-2510:1.0.0` e gravar `PLAB_2510_IMG_*` em `.env.example`
- [x] T014 [US2] Inspecionar `appserver.ini`/`dbaccess.ini` da `protheus-2510` (P2510/P2510D, portas) e registrar em `research.md` seção "Achados do spike 2510"
- [x] T015 [US2] Escrever `stacks/2510/compose.yaml` espelhando o de 2610 (project `plab-2510`, portas 25xxx, aliases `*-2510`, mesmo degrau de privilégio vencedor ou novo teste em escada)
- [x] T016 [US2] Subir 2510 com 2610 rodando; validar login em `http://127.0.0.1:25321` (aguardar restore inicial), captura em `evidencias/2510/spike/`, versões anotadas
- [x] T017 [US2] Teste de isolamento: monitorar 2610 (`curl` WebApp a cada 10 s) enquanto roda `plab down 2510 --volumes` + `plab up 2510`; 0 falhas na 2610; medir RAM das duas juntas
- [ ] T018 [P] [US2] Escrever `stacks/reserva/2510-oficial/compose.yaml` (totvsengpro postgres-dev 12.1.2510_bra, appserver-dev 24.3.1.1, dbaccess-postgres-dev 24.1.1.0, license-dev 3.7.0, digests verificados) e `stacks/reserva/2610-felipe/compose.yaml` (feliperaposo p12.1.2610) marcados "não testado" no README da pasta, a menos que testados

**Checkpoint**: US1+US2 = fase 0 do kit concluída (commit "feat(2510): stack 2510 em paralelo")

---

## Phase 5: User Story 3 - Smoke: compilar e testar pela interface (Priority: P2)

**Goal**: container `lab` + `plab smoke <release>` → PRONTO nas duas releases

**Independent Test**: `plab smoke 2610` e `plab smoke 2510` imprimem PRONTO e gravam evidências

- [x] T019 [US3] Escrever `lab/Dockerfile` multi-stage: Ubuntu 24.04, Python 3.12 + venv `/opt/lab/venv` com `tir_framework==${PLAB_TIR}`, Chrome for Testing + chromedriver `${PLAB_CHROME}`, Node 22, `@totvs/tds-ls@${PLAB_TDS_LS}`, git, jq, usuário `lab` UID 1000, sem segredo em `ARG/ENV`
- [x] T020 [US3] Escrever `lab/compose.yaml` (project `plab-lab`, rede externa `plab`, volumes `lab-home` e bind `./workspace`, `extra_hosts` não usado, sem `docker.sock`)
- [x] T021 [US3] Build e verificação da imagem: `python -c "import tir"`, `google-chrome --headless` acessa `http://appserver-2610:4321` e `http://appserver-2510:4321` pela rede `plab`, `advpls` responde versão; registrar em `STATUS.md`
- [x] T022 [US3] Spike de login TIR (risco R1): script mínimo em `cenarios/tir-login/LOGINTESTSUITE.py` que faz login e logout em cada release com senha via env; se falhar, captura + bloqueio em `STATUS.md` antes de seguir
- [x] T023 [P] [US3] Validar no TDN os símbolos usados no hello (ex.: `User Function`, `MsgInfo`/`ConOut`, `Return`) e registrar links em `cenarios/hello/README.md`
- [x] T024 [US3] Escrever `cenarios/hello/LABHELLO.prw` em CP1252 + CRLF e `lab/tests/test_encoding.sh` que confere bytes (sem `0x0A` isolado, sem sequência UTF-8 multibyte)
- [x] T025 [US3] Criar skill `skills/compilar-advpls-lab/SKILL.md` + `lab/bin/lab-compile` (advpls cli, `.ini` temporário em `/tmp` modo 600 removido por `trap`, senha só em env, parser SUCCESS/WARN/ERROR/FATAL, FATAL invalida lote, COMPILEERROR-300 → orientar fechar sessão TIR)
- [x] T026 [US3] Implementar `lab/bin/lab` com `doctor`, `compile`, `tir`, `smoke` conforme `contracts/lab-setup-cli.md` e `contracts/smoke-report.md` (console por passo, `resumo.json`, código 10+n, evidências em `evidencias/<release>/<timestamp>/`)
- [x] T027 [US3] Adicionar `smoke` ao `plab.ps1` e `plab` (executa `lab smoke` no container)
- [ ] T028 [US3] Rodar `plab smoke 2610` e `plab smoke 2510` até PRONTO; testar falha controlada com a 2510 parada (deve falhar no passo 1 nomeando o serviço); registrar evidências

**Checkpoint**: lab funcional sem IA (commit "feat(lab): smoke PRONTO nas duas releases")

---

## Phase 6: User Story 4 - `lab setup` com Claude Code e Codex (Priority: P3)

**Goal**: assistente idempotente, segredos protegidos, skills publicadas, templates gerados

**Independent Test**: rodar `plab setup` 2× → mesmo estado; IAs `testado_ok` ou `nao_testado(motivo)`

- [x] T029 [P] [US4] Copiar a skill `testes-protheus` do kit de insumos para `skills/testes-protheus/` (sem alterar o original) e rodar `python -B scripts/validate_package.py .` e `python -B -m unittest discover -s tests` dentro do container; registrar resultado
- [ ] T030 [P] [US4] Confirmar na documentação oficial de Claude Code e Codex: login sem navegador (device-code/URL), variável de API key, diretório de skills; registrar fontes em `research.md` R-07
- [ ] T031 [US4] Escrever `templates/agent-rules.md.tmpl` (regras genéricas: CP1252, padrão TOTVS, validar símbolo no TDN, WebApp, nunca produção, usar skills embarcadas) e `lab/setup/lib/templates.sh` que gera `AGENTS.md`/`CLAUDE.md`/`GEMINI.md` em `/workspace` só dentro do bloco `<!-- BEGIN plab -->…<!-- END plab -->`
- [ ] T032 [US4] Escrever `lab/setup/lib/secrets.sh` (`read -s`, recusa vazio, grava `~/.config/lab/secrets.env` 600 sem duplicar chave, nunca ecoa) e `lab/setup/lib/state.sh` (`~/.config/lab/state.json` sem segredo)
- [ ] T033 [US4] Escrever `lab/setup/providers/claude.sh` e `lab/setup/providers/codex.sh` (instala versão fixada em prefixo npm do `lab-home`, wrapper em `~/.local/bin` que carrega só a variável da própria CLI, modo conta/api_key, teste "responda OK", publica skills no diretório confirmado)
- [ ] T034 [US4] Escrever `lab/setup/lib/skills.sh` (publica `testes-protheus` e `compilar-advpls-lab`; clona `totvs/engpro-advpl-tlpp-skills` por `PLAB_ENGPRO_COMMIT`; `--with-exemplos` clona `dan-atilio/AdvPL` por commit) e gerar `config.json` do TIR em `~/.config/lab/tir/<release>/` sem senha
- [ ] T035 [US4] Escrever `lab/setup/lab-setup.sh` orquestrando o fluxo de 9 passos do contrato e `plab setup` no host
- [ ] T036 [US4] Escrever `lab/tests/test_setup_idempotente.sh` (2 execuções não interativas com flags; compara `state.json`, contagem de linhas de `secrets.env`, hashes dos `*.md` gerados) e `lab/tests/test_secrets_perm.sh` (modo 600, nada em `docker history`/logs)
- [ ] T037 [US4] Executar setup real com Claude e Codex; login por conta exige o dono → registrar em AGUARDANDO_USUARIO; o que não puder ser testado fica `nao_testado(motivo)`
- [ ] T038 [US4] Teste ponta a ponta: com uma IA configurada, pedir "crie um teste TIR que abra MATA010 e confira o título" e verificar uso das skills embarcadas (ou "não testado" com motivo)

**Checkpoint**: MVP do kit (Claude + Codex) fechado

---

## Phase 7: User Story 5 - Cenários TIR de leitura (Priority: P4)

**Goal**: 3–5 suítes somente leitura em rotinas padrão confirmadas

**Independent Test**: cada suíte passa em ≥ 1 release com evidência

- [x] T039 [US5] Confirmar no menu de cada release quais rotinas existem e seus caminhos/títulos (MATA010, MATA020, MATA030/CRMA980, FINA040, FINA050) — `lab/tir/explorar_menu.py`; caminhos em `cenarios/ui-leitura/cenarios.json`
- [x] T040 [P] [US5] Cenário produtos (MATA010) — Playwright em `cenarios/ui-leitura` (desvio: TIR bloqueado, totvs/tir#2169)
- [x] T041 [P] [US5] Cenário fornecedores (MATA020) — Playwright em `cenarios/ui-leitura`
- [x] T042 [P] [US5] Cenário clientes (MATA030/CRMA980) — Playwright em `cenarios/ui-leitura`
- [x] T043 [P] [US5] Cenários contas-receber (FINA040) e contas-pagar (FINA050) — Playwright; FINA050 na 2610 exige `lab procedures 2610 08`
- [x] T044 [US5] Rodar todas nas duas releases — 03/11/2026: 2610 5/5 e 2510 5/5, 10 saídas por Finalizar; `cenarios/README.md` com releases confirmadas

---

## Phase 8: User Story 6 - opencode e Gemini CLI (Priority: P5)

- [x] T045 [P] [US6] Confirmar na documentação oficial de opencode e Gemini CLI auth sem navegador, variável de API key e diretório de skills/instruções; registrar em `research.md`
- [x] T046 [US6] Escrever `lab/setup/providers/opencode.sh` e `lab/setup/providers/gemini.sh` com o mesmo contrato de T033
- [ ] T047 [US6] Rodar setup e testes de idempotência com as quatro IAs; status final por IA × modo

---

## Phase 9: Polish & verificação final

- [ ] T048 [P] Implementar `plab scan` (ps1 e bash): `git grep` por padrões de chave/senha/token, `.env.example` sem valores em `*_PASSWORD|_TOKEN|_KEY|_SECRET`, `docker history --no-trunc` e `docker inspect` da imagem lab, logs do setup
- [ ] T049 [P] Rodar `shellcheck` em `lab/**/*.sh`, `plab` e corrigir avisos relevantes
- [ ] T050 Escrever `README.md`: pré-requisitos com RAM/disco medidos (cada release e as duas juntas), passo a passo, portas, troubleshooting (porta ocupada, licença, login TIR, RPO em uso), fontes de imagem principal/reserva, avisos de licença (TOTVS, imagens de comunidade, IAs), o que o lab não cobre
- [x] T051 Verificação do zero: `plab down all --volumes`, clone limpo em pasta temporária, `.env` a partir do `.env.example`, `plab up 2610`, `plab up 2510`, `plab up lab`, `plab smoke` nas duas; registrar tempos (SC-001)
- [x] T052 `plab scan` com zero ocorrências; `docker ps` final comparado ao baseline T001 (SC-008)
- [x] T053 Relatório final em `STATUS.md`: funciona (com evidência), pendente, riscos (fonte de comunidade, License dev, TIR 1 worker, RAM), AGUARDANDO_USUARIO, status de SC-001..SC-009; fase marcada AGUARDANDO_REVISAO

---

## Dependencies & Execution Order

- Setup (T001–T003) → Foundational (T004–T006) → US1 → US2 → US3 → US4 → US5/US6 → Polish.
- US2 depende de US1 (reaproveita compose e degrau de privilégio).
- US3 depende de US1 **ou** US2 (smoke de uma release basta para começar; PRONTO nas duas para fechar).
- US4 depende de US3 (setup termina rodando o smoke).
- US5 depende de T022 (login TIR provado). US6 depende de US4.

## Parallel Opportunities

- T002 ∥ T003; T004 ∥ T005.
- T018 (reservas) em paralelo a T016–T017.
- T023 ∥ T019–T021; T029 ∥ T030.
- T040–T043 entre si; T048 ∥ T049.
- Observação: o kit pede "não use subagentes"; paralelismo aqui é só de ordem lógica, executado
  pelo agente em sequência.

## Implementation Strategy

1. **MVP técnico** = US1 + US2 (as duas releases de pé, coexistindo, com evidência).
2. **MVP de desenvolvimento** = + US3 (smoke PRONTO nas duas).
3. **MVP do kit** = + US4 (Claude + Codex).
4. Incrementos: US5 → US6 → Polish/verificação do zero.
5. Parar em cada checkpoint, atualizar `STATUS.md`, commitar.
