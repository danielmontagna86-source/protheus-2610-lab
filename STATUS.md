# STATUS — Protheus 2610 Lab

Última atualização: 2026-11-02

## Fase atual

Gate final da constituição executado em 03/11/2026 (T051–T053): relatório em
`docs/relatorio-final-2026-11-03.md`. US1–US5 verificadas do zero; US6 parcial (login real de
opencode/Gemini). Publicação pública: só com nova autorização do dono.

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
- **Senha em captura de tela**: numa falha de login a captura mostrou a senha digitada no campo de
  usuário (o formulário PO UI redesenhou entre os preenchimentos). Correção: o login confere os dois
  campos antes de clicar e toda captura limpa o formulário de login antes. Capturas de falha da
  etapa de login foram apagadas das evidências locais. Risco restante: capturas do próprio TIR
  (`lab tir`) não passam por essa limpeza, e o `plab scan` não lê imagens.

## Em andamento

- Revisão independente: L1–L12 (baixos).
- T047 (opencode/Gemini real); compilação na 2510 do zero exige trocar a senha do Admin por uma sem `$`.

## Pendências

- **T047 (US6)**: parte automática OK em 03/11/2026 (`test_setup_idempotente.sh 2610 claude,codex,opencode,gemini`: idempotente; opencode 1.19.5 instalado, wrapper e 36 skills, `nao_testado`; Gemini: login de conta Google verificado até o pedido do código em 03/11/2026 (R-07.2), modo `conta` passa a ser o padrão; Claude/Codex seguem `testado_ok`). Falta login real de opencode/Gemini com conta/chave do dono.
- US6: login real de opencode/Gemini.
- Conferir a versão da LIB pela interface (2610: autor declara 20261016).

## Desvios registrados

- **FR-005 / T018 (fonte reserva)**: fora desta versão. As reservas exigem outro layout de volumes,
  ini e senhas, e testá-las de ponta a ponta dobra o download (~25 GB). Mitigação: digests fixos das
  imagens principais e documentação das reservas no README. Revisitar se as imagens principais
  sumirem.

## Decisões de governança

- **Renovação da data de troca de senha do Admin** (M2 da revisão): decisão técnica do agente em
  2026-11-02, registrada aqui para revisão do dono (ver AGUARDANDO_USUARIO). Motivo: a base 2510 da imagem já nasce com a senha vencida pela política, e o login
  automatizado não pode passar pela troca obrigatória. Não altera a senha nem desliga a política;
  só atualiza `usr_dtchgpsw` do usuário 000000. Aplicada só nas releases de
  `PLAB_RENOVAR_SENHA_ADMIN` (padrão 2510). A senha do banco é lida dentro do container.
- **Senha do Admin da 2510 do lab** trocada pelo fluxo "Alterar senha" do Protheus por uma sem `$`
  (autorizado pelo dono), por causa do travamento do `advpls`.
  Refeita em 03/11/2026 (autorizado pelo dono) depois de recriar a base: senha de 16 caracteres
  gerada no container e gravada só no `.env`; `plab smoke 2510` → PRONTO nos 5 passos.

## Bloqueios

Nenhum.

## AGUARDANDO_USUARIO

- Publicação pública do repositório: exige nova autorização.
- Confirmar a renovação automática da data de troca de senha do Admin na 2510 (ou desligar com
  `PLAB_RENOVAR_SENHA_ADMIN=` vazio e trocar a senha manualmente a cada vencimento).
- **US6**: testar opencode e Gemini com sua conta/chave (`lab setup --ia opencode` e `lab setup --ia gemini --auth api_key`)? Sem isso ficam "não testado".

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
