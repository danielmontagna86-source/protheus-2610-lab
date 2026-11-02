# Research: Protheus 2610 Lab

Pesquisa feita em 2026-11-02 (Docker Hub API, GitHub API, npm, PyPI, Chrome for Testing).
"Verificado" = consultado na fonte nesta data. "Hipótese" = a confirmar no spike (Fase 0).

## R-01 Fonte das imagens da 12.1.2610

- **Decision**: `emebatista/{postgres,license-server,protheus-dbaccess,protheus}-2610:1.0.0`.
- **Rationale** (verificado): é o único conjunto 2610 com **base padrão já restaurada** dentro
  da imagem (`postgres-2610`: PostgreSQL 15.14, WIN1252). Versões declaradas: AppServer 26.3.0.0,
  Lib 20261016, WebApp 26.0.0, DBAccess 26.1.0.0, License 3.7.2. Publicado em 17/10/2026.
  Ambientes declarados: P2610, P2610_COMPILA, P2610_DEBUG. Usuário `Admin`, senha documentada
  publicamente no README do autor (não será gravada no repo).
- **Digests (verificados)**: postgres-2610 `sha256:fca7d2bea756…`, license-server-2610
  `sha256:a5d35ee1847d…`, protheus-dbaccess-2610 `sha256:efa60f455746…`, protheus-2610
  `sha256:b8ab6047dbc3…` (digests completos vão para o `.env.example` na Fase 0).
- **Alternatives considered**:
  - Oficial TOTVS `totvsengpro/*`: **não existe tag 2610** (última atualização 09/10/2025, só até
    2510). Rejeitado para 2610.
  - `feliperaposo/protheus:p12.1.2610` (22/10/2026, GPL-3.0 no compose): sem `privileged`, mas
    banco nasce vazio + systemload (exige criar base). Fica como **reserva**.
  - `JobwiseTec/protheus-2610`: fork do emebatista (mesmo conteúdo). Descartado por duplicidade.

## R-02 Fonte das imagens da 12.1.2510

- **Decision**: `emebatista/*-2510:1.0.0` (mesma família da 2610).
- **Rationale** (verificado): mesma topologia, nomes e convenções da 2610 → um único modelo de
  compose e um único caminho de diagnóstico; base restaurada na primeira subida (~5 min segundo o
  autor); ambiente P2510 e P2510D (sem multiprotocolo, indicado para compilar).
- **Alternatives considered**: oficial `totvsengpro/postgres-dev:12.1.2510_bra` +
  `appserver-dev:24.3.1.1` + `dbaccess-postgres-dev:24.1.1.0` + `license-dev:3.7.0` (verificado:
  existem, com digest). É oficial, mas exige outro modelo de configuração; vira **reserva** e
  será testada se a principal falhar. `feliperaposo/protheus:p12.1.2510`: reserva secundária.

## R-03 Componentes excluídos

- **Decision**: não usar `deskflow-2610` (produto licenciado, monta `docker.sock` e usa
  `pid: host`), `smartview-*` e `protheus-*-exclusivo`.
- **Rationale**: Constituição IV (mínimo privilégio) e escopo da spec.

## R-04 Privilégios do License Server e AppServer

- **Decision**: escada testada no spike: (a) nenhum privilégio extra → (b)
  `security_opt: [systempaths=unconfined, apparmor=unconfined]` (abordagem do feliperaposo) →
  (c) `devices: /dev/mem` + `cap_add: SYS_RAWIO` → (d) `privileged: true`. Usar o primeiro degrau
  que funcionar e registrar evidência dos degraus que falharam.
- **Rationale**: o compose original do emebatista usa (c)+(d); o feliperaposo resolveu o mesmo
  dmidecode só com (b). Hipótese: (b) basta no Docker Desktop/WSL2.

## R-05 Isolamento entre releases e com stacks existentes

- **Decision**: três projetos compose (`plab-2610`, `plab-2510`, `plab-lab`), sem
  `container_name`, volumes nomeados por projeto, rede externa `plab` com aliases
  `appserver-2610`, `appserver-2510`, `dbaccess-2610`… Portas host em 127.0.0.1:
  2610 → 26234 (TCP 1234), 26321 (WebApp 4321), 26181 (REST 8181), 26432 (Postgres), 26020
  (monitor licença); 2510 → 25234, 25321, 25181, 25432, 25020. Verificado em 2026-11-02:
  todas livres; `protheus-teste` usa 1234/18080/18081/57890/55434.
- **Alternatives considered**: um compose com profiles (rejeitado: `down -v` do projeto apagaria
  volumes das duas releases); `host.docker.internal` (rejeitado: portas em 127.0.0.1 não são
  alcançáveis por esse caminho em Linux).

## R-06 Imagem lab

- **Decision**: Ubuntu 24.04, multi-stage; Python 3.12 (do sistema) + venv; `tir_framework==2.14.12`
  (verificado: exige Python 3.12 exato; dependências fixadas incluem selenium 4.19.0); Chrome for
  Testing **156.0.8078.80** + chromedriver mesma versão (verificado: stable em 2026-11-02);
  Node 22 LTS; `@totvs/tds-ls@2.2.7` (verificado: Apache-2.0, ~75 MB, contém advpls); git;
  usuário não-root `lab` (UID 1000).
- **Rationale**: TIR exige 3.12; Chrome for Testing dá par navegador/driver casado e fixável.
- **Alternatives considered**: imagem oficial `totvsengpro/tir:2.14.12` (~1 GB, verificada) como
  base — rejeitada para manter uma única imagem enxuta com advpls e CLIs; pode servir de
  comparação se o TIR falhar.

## R-07 CLIs de IA

- **Decision** (versões verificadas no npm): `@anthropic-ai/claude-code@2.1.316`,
  `@openai/codex@0.166.0`, `opencode-ai@1.19.5`, `@google/gemini-cli@0.66.0`, instaladas pelo
  `lab setup` em prefixo npm dentro de `lab-home` (não na imagem) para não engordar a imagem e
  permitir atualizar sem rebuild.
- **Hipóteses a confirmar na documentação oficial de cada CLI durante a Fase 4**: fluxo de login
  sem navegador (device-code/URL), variável de API key, diretório de skills
  (`~/.claude/skills`, `~/.codex/skills` ou `~/.agents/skills`, equivalentes de Gemini/opencode).

## R-08 Skills de terceiros

- **Decision**: `totvs/engpro-advpl-tlpp-skills` (verificado: **MIT**) clonado no setup por commit
  fixado; `dan-atilio/AdvPL` (verificado: **GPL-3.0**) só com `lab setup --with-exemplos`,
  clonado no volume do usuário, nunca vendorizado. TIR (`totvs/tir`, MIT) via pip.

## R-09 Compilação

- **Decision**: advpls CLI com `.ini` temporário em `/tmp` (modo 600, apagado por `trap`), senha
  só por variável de ambiente; ambiente de compilação P2610_COMPILA (2610) e P2510D (2510)
  conforme README do autor — **hipótese** a confirmar no `appserver.ini` da imagem no spike.
  Erro COMPILEERROR-300 (RPO em uso) → fechar sessão TIR antes de compilar.

## Achados do spike 2610 (2026-11-02, verificados)

- Topologia exigida pelos `.ini` das imagens: hosts `postgresql-2610`, `license-server-2610`,
  `dbaccess-2610` (resolvidos por alias de rede). DBAccess usa a senha padrão de desenvolvimento
  da imagem, só na rede interna.
- AppServer `appserver.ini`: ambientes `P2610` (web), `P2610_COMPILA` (RPO próprio em
  `/protheus12/P2610_COMPILA/APO0002`) e `P2610_DEBUG`; TCP 1234 com `MultiProtocolPort=1`;
  WebApp 4321; REST 8181 `/rest`.
- **WebApp correto = porta multiprotocolo** (`http://127.0.0.1:26234/webapp/`). Pela 4321 a
  tela de parâmetros abre, mas `/app-root/preindex_env_p2610/index.html` dá 404 e o WebApp
  mostra `json_context.cpp:963, 404 - Unknown status`. O `/app-root` só é servido na 1234.
- Login é **PO UI** ("Linha Protheus"); home após login é o **menu clássico** → TIR:
  `POUILogin: true`, `POUI: false`, `NewHome: false`.
- Escada de privilégio: degrau (a) **basta**. Login, seleção de empresa 99/filial 01 e menu
  carregaram sem `/dev/mem`. Degrau (b) não expõe DMI no WSL2; (c) faz o dmidecode funcionar
  mas não é necessário — mantido só como override opcional `stacks/override/devmem.yaml`.
  O log `Can't read memory from /dev/mem` é ruído.
- Versões medidas: AppServer 26.3.0.0 build 7.00.260324P (15/10/2026); WebApp 26.0.0;
  DBAccess build 20240224 (07/10/2026), dbapi 26.1.0.0; License (appserver) 24.3.0.11;
  PostgreSQL 15.19. LIB 20261016 declarada pelo autor, não conferida na interface.
- Recursos: subida com imagens em cache 32 s; RAM em repouso ≈ 1,0 GB (appserver 701 MB,
  db 182 MB, license 123 MB, dbaccess 34 MB); disco: imagens 15,9 GB + volumes 2,9 GB.
- Log `Fail to Start Hub (-113)` aparece na subida e não impediu login/menu (não investigado).

## R-10 Risco de login TIR

- **Fato**: no ambiente local `Protheus-Teste` (imagem feliperaposo antiga, WebApp 10.1.5) o smoke
  TIR não concluiu por causa do fluxo de login PO UI (relatório VALIDACAO-8GB-20260910.md).
- **Decision**: provar login TIR no início da Fase 3 em cada release, antes de escrever cenários;
  se falhar, registrar bloqueio com captura e avaliar adaptador versionado de login.
