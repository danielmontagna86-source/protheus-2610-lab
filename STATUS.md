# STATUS — Protheus 2610 Lab

Última atualização: 2026-11-02

## Fase atual

Fase 0 (spike das imagens), tarefas T001–T018 de `specs/001-protheus-2610-lab/tasks.md`.

## Decisões vigentes

- Releases: 12.1.2610 e 12.1.2510, lado a lado (pedido do dono em 2026-11-02).
- Fonte principal das duas: imagens de comunidade `emebatista/*:1.0.0` (base restaurada).
  Reservas: oficial TOTVS `totvsengpro/*` (só 2510) e `feliperaposo/protheus:p12.1.2610`.
  Motivo: não existe tag 2610 oficial (Docker Hub verificado em 2026-11-02); dono autorizou fonte
  não oficial.
- Fora: DeskFlow, SmartView, container exclusivo, `docker.sock`, `pid: host`.
- Portas: 2610 → 26234/26321/26181/26432/26020; 2510 → 25234/25321/25181/25432/25020 (todas livres
  em 2026-11-02).
- Skill TIR: `testes-protheus` 1.2.0 (cópia do kit + integração EngPro `tir-test-generator` 5.1.0,
  commit `41504805e419b72232885f7575d54dfd573fea1b`); EngPro clonada no setup, não vendorizada.

## Concluído (com evidência)

| Tarefa | Evidência |
|---|---|
| Spec Kit (constituição, spec, plan, tasks) | commits `b2bf57b`..`932a442` |
| T001 baseline | `evidencias/baseline/antes.txt`: 11 containers pré-existentes, todos healthy |
| T002 estrutura + LICENSE | árvore criada |
| T029 (antecipada) skill testes-protheus 1.2.0 | `validate_package.py` → `ok: true`; `unittest` → `Ran 66 tests … OK` |
| T003 `.env.example` | 8 digests `emebatista/*:1.0.0` verificados; senhas vazias; `.env` local ignorado (`git check-ignore` ok) |
| T004/T005 wrapper `plab.ps1` + `plab` | `net`, `ports`, `up`, `down`, `status`, `logs` |
| T006 | `plab net` 2× → "criada" / "ja existe", 1 rede `plab`; `plab ports` → 10 portas livres |
| T007/T008 imagens e inspeção 2610 | achados em `research.md` "Achados do spike 2610" |
| T009 compose 2610 | `docker compose config --quiet` → 0 |
| T010 escada de privilégio | (a) basta: login+menu sem `/dev/mem`; (b) não expõe DMI no WSL2; (c) funciona mas desnecessário → override opcional `stacks/override/devmem.yaml` |
| T011 login 2610 | `http://127.0.0.1:26234/webapp/` → login PO UI Admin → empresa 99/filial 01 → menu "TOTVS Linha Protheus POSTGRES P2610"; capturas em `evidencias/2610/spike/` (ignoradas pelo git) |
| T012 recursos 2610 | subida 32 s; RAM ≈ 1,0 GB em repouso; imagens 15,9 GB + volumes 2,9 GB; 11 containers pré-existentes seguem healthy |

| T013/T014 imagens e inspeção 2510 | digests no `.env.example`; `P2510`/`P2510D` compartilham `/protheus12/apo`; SmartClient HTML 10.0.2 |
| T015/T016 stack 2510 | primeira subida 283 s (restore da base); login PO UI Admin → 99/01 → menu "TOTVS Construção e Projetos POSTGRES P2510"; versões AppServer 24.3.1.1 (7.00.240223P), DBAccess 20240224 / API 24.1.1.0, License 24.3.0.11 |
| Achado 2510: senha do Admin expirada | base publicada com última troca em 12/10/2025 → login exige "Alterar senha" e Cancelar = "Usuário não autorizado!". Correção: `stacks/sql/renova-senha-admin.sql` (atualiza só a data da última troca, não a senha), aplicado automaticamente pelo `plab up` nas duas releases. Verificado: login entra sem troca |
| T017 isolamento | `down --volumes` + `up` da 2510 do zero (277 s) com a 2610 monitorada a cada 5 s: **55/55 ok, 0 falhas**; volumes da 2610 intactos (`evidencias/2510/spike/t017-isolamento.txt`) |
| T019–T021 imagem lab | `plab-lab:local` 2,94 GB; `lab versions`: Python 3.12.3, TIR 2.14.12, Selenium 4.19.0, Chrome/chromedriver 156.0.8078.80, Node 22.23.4, advpls TDS-LS 2.1; usuário `lab` uid 1000; senhas como secrets em `/run/secrets` (nada em `docker inspect`); `lab doctor 2610` → 6/6 OK |
| T023/T024 hello | símbolos `ConOut`, `DToS`, `Date`, `Time`, `User Function` conferidos no TDN (navegador); `LABHELLO.prw` 541 bytes, 15 CRLF, CP1252 (0xE7 0xE3 0xE1) |
| T025 compilação 2610 | `lab compile 2610 LABHELLO.prw` → `SUCCESS=1 WARN=0 ERROR=0 FATAL=0` (`evidencias/2610/compile-teste/compile.log`) |

Correções descobertas na compilação (todas verificadas):

- RPO de `P2610_COMPILA`: o AppServer Linux usa o caminho em minúsculas (`/protheus12/p2610_compila/apo0002`) e a imagem o tem em maiúsculas → "Open APO failed". Serviço `rpo-init` semeia o volume no caminho certo.
- advpls tenta conexão segura primeiro e morre por SIGPIPE (rc 141, sem log) → `lab compile` ignora SIGPIPE.
- Includes: o pré-compilador roda **no lab**, exige `PRTOPDEF.CH` (maiúsculas) e **escrita** no diretório → serviço `includes-init` (lab) copia os 158 includes da imagem AppServer 2610 do usuário + links maiúsculos; `lab compile` usa cópia temporária.
- `$` no `psw` trava o advpls (loop em `std::string::find`, sem saída) → `lab compile` falha cedo (código 22).

| T022 spike TIR | **TIR 2.14.12 não conclui o Setup** no WebApp 26.0.0 nem no SmartClient HTML 10.0.2: (1) `#selectEnv` autocompleta e a digitação vira `P261P2610` (reproduzido com Selenium) → corrigido pela extensão `lab/tir/plab_tir_compat.py` (log "[plab_tir_compat] Ambiente P2610 selecionado"); (2) depois disso o clique no `wa-button` OK não leva ao login (Selenium) → **bloqueio do TIR registrado** |
| Playwright (pedido do dono) | plugin oficial "playwright" (MCP Microsoft) oferecido para instalação no Claude; na imagem lab: `playwright==1.64.1` usando o Chrome 156 (sem download de navegador) |
| Smoke de interface (Playwright) | `lab ui 2610` e `lab ui 2510` → **OK**: parâmetros → login PO UI (iframe `/login`) → 99/01/módulo 5 Faturamento → Atualizações > Cadastros > Produtos → Moedas **Cancelar** (nada gravado) → aba "Produtos" (2510: "Produtos [02.9.0005]") e título "Atualizacao de Produtos" |
| Skill testes-protheus 1.3.0 | seção "Complemento Playwright"; validador `ok: true`, 66 testes OK |

| T026–T028 smoke completo | `plab smoke 2610` → **PRONTO** em 211 s (doctor, compile SUCCESS=1, interface OK, limpeza sem temporários e sem senha nas evidências; `evidencias/2610/20261102-172055/resumo.json`). `plab smoke 2510` → **FALHOU no passo 2** de forma controlada (código 22: senha com `$`), em 6 s |

| 2510 compilação | senha do Admin da 2510 do lab trocada pelo fluxo "Alterar senha" do Protheus (sem `$`, autorizado pelo dono); `lab compile 2510` → SUCCESS |
| 2510 /app-root após compilar | AppServer 24.3.1.1 para todos os HTTP ao compilar e o REST toma a porta do servidor `SD` → `/app-root` 404. Mitigação verificada: RPO próprio para `P2510D` (`rpo-init` + `entrypoint-lab.sh`), smoke com interface antes da compilação e `plab smoke` reiniciando o appserver (passo 5) + `plab restart` |
| Bateria de validação | `plab smoke 2510` 2× **PRONTO** (com recuperação), `plab smoke 2610` **PRONTO**, scan sem segredos (só falha a trava de histórico) |
| T030–T037 lab setup (Claude + Codex) | conta: `claude auth login` e `codex login --device-auth` (fontes oficiais em research.md); setup idempotente 2× (estado, AGENTS/CLAUDE/GEMINI.md e 36 skills idênticos; secrets.env 600); **login real do dono: claude testado_ok, codex testado_ok**, credenciais 600 no volume lab-home; smoke PRONTO |
| T038 ponta a ponta com IA | Claude no lab criou suíte TIR da MATA010 usando `tir-test-generator` + `testes-protheus` (POUILogin, somente leitura, sem senha, não declarou pronto). Ressalvas viraram regra no template (config via `PLAB_TIR_CONFIG`; título real sem acento) |
| TIR 2.14.13rc1 | testado: mesmo travamento no `#selectEnv` → issue redigido em `docs/upstream/tir-issue-selectenv.md` (envio autorizado; falta `gh auth login`) |
| Shellcheck / CI | 20 scripts sem achados; `.github/workflows/ci.yml` com gates estáticos (actions por SHA) |
| T045 pesquisa opencode/Gemini | `research.md` R-07.1: versões `latest` no npm (opencode-ai 1.19.5, @google/gemini-cli 0.66.0) e docs oficiais lidas nos repositórios `sst/opencode` @ `1bf08ae46a91` e `google-gemini/gemini-cli` @ `0ac57c029b84` (sites bloqueados na sessão de nuvem). Gemini não documenta login de conta sem navegador → só `api_key` |
| T046 providers opencode e Gemini | `lab/setup/providers/opencode.sh` (conta: `opencode auth login`; chave: `OPENCODE_API_KEY` ou `ANTHROPIC_API_KEY`) e `gemini.sh` (só `api_key`: `GEMINI_API_KEY`); `lab-setup.sh` com `IAS_SUPORTADAS="claude codex opencode gemini"`, versão no `state.json` e `<ia>_modos` opcional (fluxo de Claude/Codex sem mudança de comportamento). `shellcheck` v0.11.0 (binário oficial, sessão sem Docker): 0 achados em `lab/setup/providers/*.sh`, `lab/tests/*.sh` e `lab-setup.sh`. Teste local com **stubs** (npm, CLIs, doctor e smoke falsos; sem rede de IA): chave digitada por pseudo-TTY não aparece na saída, `secrets.env` 600 sem duplicar, wrapper do opencode exporta só a variável escolhida e nenhuma no modo conta, wrapper do Gemini só `GEMINI_API_KEY`, `settings.json` do Gemini preservado; 2 execuções seguidas com as 4 IAs → estado, instruções, skills e wrappers idênticos |

## Em andamento

- Nada rodando. Próximas: decisão da senha da 2510 (AGUARDANDO_USUARIO), US4 (assistente IA), US5 cenários, verificação final.

## Pendências

- T026–T028 smoke completo; T018 reservas; US4–US6; Polish.
- **T047 (US6) não testado**: precisa da imagem `lab` com as stacks Protheus e credenciais do dono.
  No PC do dono, dentro do container lab:
  1. `bash /opt/plab/lab/tests/test_setup_idempotente.sh 2610 claude,codex,opencode,gemini`
     (esperado: opencode `nao_testado`, gemini `nao_suportado(modo conta...)`, idempotente OK);
  2. `lab setup --ia opencode` (conta, ex.: GitHub Copilot por código de dispositivo, ou `api_key`)
     e `lab setup --ia gemini --auth api_key` → esperado `testado_ok`;
  3. varredura de segredo (`plab scan`) depois do login.
  Estado atual por IA × modo: opencode conta = não testado; opencode api_key = não testado;
  gemini api_key = não testado; gemini conta = não suportado (documentação oficial).
- Conferir versão da LIB pela interface (2610: autor declara 20261016).
- Antes de publicar: reescrever o histórico local para remover `evidencias/` do commit `1b6fc29`
  (capturas com hostname do autor da imagem e baseline com nomes de containers locais).

## Bloqueios

Nenhum.

## AGUARDANDO_USUARIO

- **Compilar na 2510**: a senha padrão do Admin da 2510 contém `$`, que trava o `advpls cli`.
  Opção recomendada: trocar a senha do Admin **da 2510 do lab** por uma sem `$` pelo fluxo normal do
  Protheus (WebApp → trocar senha) e atualizar `PLAB_2510_ADMIN_PASSWORD` no `.env`. Autoriza?
- **US6 (T047)**: rodar os passos de T047 acima com sua conta/chave de opencode e Gemini? Sem isso
  os dois ficam "não testado".
- **Reportar ao TIR** (github.com/totvs/tir) o defeito do `#selectEnv` com autocompletar? É publicação
  externa; só com autorização.

- (achado, não bloqueia) Cópias locais da skill TIR estão desatualizadas: `~/.claude/skills/advpl-tlpp/tir-test-generator` e
  `~/.codex/skills/advpl-tlpp/tir-test-generator` em 5.0.0 (EngPro atual 5.1.0); `~/.codex/skills/tir-test-generator`
  é uma variante antiga que descreve TIR como JavaScript (incorreto). Atualizar as cópias pessoais?

## Riscos

- R1 login PO UI × TIR: mitigação direta pela EngPro 5.1.0 (`POUILogin: true`, `POUI: false`, `NewHome` conforme home).
- R2 License Server exigir `/dev/mem` no WSL2: escada de privilégio no spike.
- R3 imagens de comunidade sem licença declarada: digest fixo + reservas.
- R4 RAM das duas releases juntas: medir no spike.

## Emendas da constituição

- v1.0.0 adotada em 2026-11-02.
