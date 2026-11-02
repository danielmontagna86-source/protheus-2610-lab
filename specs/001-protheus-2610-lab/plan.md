# Implementation Plan: Protheus 2610 Lab (releases 12.1.2610 e 12.1.2510)

**Branch**: `001-protheus-2610-lab` | **Date**: 2026-11-02 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-protheus-2610-lab/spec.md`

## Summary

Entregar, nesta máquina e executado pelo agente, um lab funcional com duas stacks Protheus
padrão (12.1.2610 e 12.1.2510) que coexistem, cada uma com base restaurada, mais um container de
ferramentas (`lab`) com TIR, Chrome headless, advpls e CLIs de IA, um assistente `lab setup`
idempotente e um smoke (compilação + TIR leitura) que termina em PRONTO. A abordagem é
"spike primeiro": provar as duas stacks com as imagens de comunidade `emebatista/*` (fixadas por
digest, sem DeskFlow/SmartView, com privilégios mínimos testados em escada) antes de construir o
resto. Decisões e alternativas em [research.md](research.md).

## Technical Context

**Language/Version**: Bash 5 (assistente e scripts no container), PowerShell 5.1 + Bash (wrapper
`plab` no host), Python 3.12 (TIR, utilitários), AdvPL/TLPP (cenário hello, CP1252 + CRLF)

**Primary Dependencies**: Docker Engine + Compose v2; imagens `emebatista/*-2610:1.0.0` e
`emebatista/*-2510:1.0.0`; `tir_framework==2.14.12`; Chrome for Testing 156.0.8078.80 +
chromedriver idem; Node 22 LTS; `@totvs/tds-ls@2.2.7` (advpls); CLIs IA fixadas
(`@anthropic-ai/claude-code@2.1.316`, `@openai/codex@0.166.0`, `opencode-ai@1.19.5`,
`@google/gemini-cli@0.66.0`)

**Storage**: PostgreSQL das imagens (base padrão restaurada, WIN1252) em volumes nomeados por
release; volume `lab-home` (config/tokens das IAs); bind `./workspace` (fontes do usuário)

**Testing**: smoke `plab smoke <release>` (advpls + TIR); `python -B -m unittest` da skill
`testes-protheus`; `bats`-free shell tests via `lab/tests/*.sh` (asserções simples em bash);
`shellcheck` nos scripts; varredura de segredo `plab scan`

**Target Platform**: Windows 11 + Docker Desktop (WSL2), imagens `linux/amd64`; Linux nativo
"não testado" até evidência

**Project Type**: ambiente de desenvolvimento conteinerizado + CLI (wrapper host e assistente)

**Performance Goals**: stack pronta (todos healthy) em ≤ 10 min com imagens em cache (SC-001);
smoke completo ≤ 5 min por release

**Constraints**: bind 127.0.0.1; portas 26xxx (2610) e 25xxx (2510); zero conflito com
outras stacks já existentes na máquina; RAM das duas releases + lab dentro da memória alocada ao Docker
(medir); sem `docker.sock`/`pid: host`; segredos só em `secrets.env` (600)

**Scale/Scope**: 2 releases, 1 imagem construída, 4 IAs (2 no MVP), 2 skills próprias + 2 de
terceiros clonadas, 1 hello + 3–5 cenários TIR

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio | Como o plano cumpre | Status |
|---|---|---|
| I. Padrão TOTVS, sem redistribuição | Só referências a imagens externas por digest; advpls/TIR/CLIs baixados no build/setup; nenhum fonte/RPO no repo; cenários só em rotinas padrão | PASS |
| II. Segredos fora de tudo | Senhas por env (`PLAB_*_PASSWORD` no `.env` local não versionado); API keys via `read -s` → `~/.config/lab/secrets.env` 600; `.ini` do advpls em `/tmp` apagado por `trap`; `plab scan` antes de concluir | PASS |
| III. Evidência antes de afirmação | `STATUS.md` por tarefa; smoke grava evidências; "não testado" explícito no relatório de IAs | PASS |
| IV. Isolamento e mínimo privilégio | 3 projetos compose, volumes próprios, rede `plab` própria, portas novas verificadas livres; escada de privilégio testada (R3) | PASS condicionado ao spike (ver Complexity Tracking) |
| V. AdvPL/TLPP disciplinado | LABHELLO validado no TDN; checagem de bytes CP1252/CRLF em `lab/tests`; parser de severidade na skill de compilação | PASS |
| VI. Reprodutibilidade e retomada | Versões no `.env.example`; commit por tarefa; sem push | PASS |

**Re-check pós-design (Phase 1)**: mantido PASS. Único ponto condicionado: se o License Server
ou o AppServer exigirem `/dev/mem` + `sys_rawio` ou `privileged`, o desvio é registrado abaixo e
no README com a evidência do teste.

## Project Structure

### Documentation (this feature)

```text
specs/001-protheus-2610-lab/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── plab-cli.md          # wrapper do host
│   ├── lab-setup-cli.md     # assistente dentro do container
│   ├── env-contract.md      # variáveis do .env.example
│   └── smoke-report.md      # formato de saída e evidências do smoke
├── checklists/requirements.md
└── tasks.md                 # /speckit-tasks
```

### Source Code (repository root)

```text
.env.example                 # versões, digests, portas, nomes de variáveis de senha (sem valor)
plab.ps1 / plab              # wrapper host: net, up, down, status, logs, smoke, setup, scan
stacks/
├── 2610/compose.yaml        # project plab-2610: db, license, dbaccess, appserver
├── 2510/compose.yaml        # project plab-2510: idem
└── reserva/                 # compose das fontes reserva (totvsengpro-2510, feliperaposo-2610)
lab/
├── compose.yaml             # project plab-lab: serviço lab, volumes lab-home e workspace
├── Dockerfile               # multi-stage Ubuntu 24.04, usuário lab
├── bin/lab                  # entrypoint de comandos: setup, doctor, smoke, compile, tir
├── setup/lab-setup.sh
├── setup/providers/{claude,codex,opencode,gemini}.sh
├── setup/lib/*.sh           # diagnóstico, segredos, skills, templates
└── tests/*.sh               # testes de shell (idempotência, permissões, CP1252)
skills/
├── testes-protheus/         # cópia dos insumos do kit
└── compilar-advpls-lab/     # skill nova
templates/
└── agent-rules.md.tmpl      # gera AGENTS.md / CLAUDE.md / GEMINI.md
cenarios/
├── hello/LABHELLO.prw + README.md
└── tir-<rotina>/            # 3–5 suítes somente leitura + README
evidencias/                  # saída do smoke (ignorado no git, exceto .gitkeep)
README.md  LICENSE (MIT)  STATUS.md
```

**Structure Decision**: repositório único, sem `src/`: a "aplicação" é infraestrutura (compose)
+ uma imagem + scripts. Cada release é um diretório de stack autocontido para permitir
`down -v` isolado (SC-002).

## Fases de execução (ordem obrigatória)

| Fase | Entrega | Gate de saída (evidência) |
|---|---|---|
| 0 Spike | stacks/2610 e stacks/2510 de pé com emebatista, privilégio mínimo descoberto, login WebApp nas duas, versões e RAM/disco medidos | `docker compose ps` healthy nas duas ao mesmo tempo; tela pós-login; stacks pré-existentes da máquina ainda healthy |
| 1 Spec | (esta) spec/plan/tasks | commit |
| 2 Imagem lab | Dockerfile + compose lab | `import tir` ok; Chrome headless abre WebApp 2610 e 2510; `advpls --version` |
| 3 Compilação + smoke | skill compilar-advpls-lab, LABHELLO, smoke TIR leitura | `plab smoke 2610` e `plab smoke 2510` → PRONTO |
| 4 Assistente IA (MVP) | lab-setup + providers claude/codex + skills + templates | testes de idempotência; teste trivial por IA ou "não testado" com motivo |
| 5 Cenários | 3–5 suítes TIR leitura | cada suíte aprovada em ≥ 1 release |
| 6 opencode/Gemini | providers extras | idem fase 4 |
| 7 Docs + verificação final | README, STATUS final | subida do zero, scan zero, SC-001..009 avaliados |

## Riscos principais

| ID | Risco | Mitigação |
|---|---|---|
| R1 | Login PO UI do WebApp 26.x incompatível com TIR (já falhou numa stack local mais antiga, com WebApp 10.1.5) | TIR 2.14.12 (mais novo); spike de login TIR logo no início da fase 3; reserva: adaptador de login via Selenium documentado na skill `testes-protheus` (`ui_adapter.py`) |
| R2 | License Server/AppServer exigindo `/dev/mem` no WSL2 | escada de privilégio no spike, com evidência por degrau |
| R3 | Imagens de comunidade sem licença declarada e sem garantia de permanência | fixar digest; reservas documentadas; README avisa |
| R4 | RAM das duas releases + lab | medir no spike; README traz números e recomenda subir uma por vez em máquinas menores |
| R5 | Ambiente de compilação (P2610_COMPILA / P2510D) e senha de compilação desconhecidos | descobrir no spike lendo `appserver.ini` da imagem (sem copiar para o repo) |
| R6 | Login por conta das CLIs depende do dono | item fica AGUARDANDO_USUARIO; API key não testada vira "não testado" |

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Possível `devices: /dev/mem` + `cap_add: sys_rawio` (ou `privileged`) no License Server/AppServer — só se o spike provar | O License Server identifica hardware via dmidecode; sem isso pode não subir | `security_opt: systempaths=unconfined` é tentado antes; se bastar, nenhum desvio é registrado |
| Rede externa `plab` criada pelo wrapper | o container lab precisa alcançar as duas releases por nome | `host.docker.internal` não alcança portas publicadas só em 127.0.0.1 em Linux; rede compartilhada é portátil |
| `plab up` atualiza `sys_usr.usr_dtchgpsw` do Admin (só releases em `PLAB_RENOVAR_SENHA_ADMIN`, padrão 2510) | a base 2510 da imagem nasce com a senha vencida pela política; o login automatizado não passa pela troca obrigatória | trocar a senha a cada vencimento é manual e quebra o smoke sem aviso; a senha e a política não são alteradas |
| Senha do superusuário do Postgres lida de `POSTGRES_PASSWORD` dentro do container `db` para a renovação | o `psql` exige senha mesmo pelo socket local | passar a senha em `-e PGPASSWORD=...` a expõe na lista de processos do host (Princípio II); a variável já existe na imagem e não sai do container |
| Fonte reserva (FR-005 / T018) não implementada | — (desvio, não exceção) | registrado em STATUS.md "Desvios registrados" |
