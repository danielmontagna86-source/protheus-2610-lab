# Revisão independente — Protheus 2610 Lab (novembro/2026)

## Resumo

1. Nenhum segredo real foi encontrado no histórico git: há um único commit e `evidencias/` contém só `.gitkeep`. O desenho de segredos (`/run/secrets`, `read -s`, `secrets.env` 600, arquivos temporários 0700/0600 com `trap`) está correto.
2. **Bloqueiam a publicação:** o gate final da constituição (clone limpo + `down -v` + smoke + scan) não tem evidência e o `STATUS.md` contradiz o próprio estado; falta aviso de marca e de não afiliação à TOTVS.
3. **Alto:** os scripts estão versionados sem bit executável, então `./plab` e `plab scan` falham em Linux/macOS/WSL (reproduzido). FR-020 (3–5 cenários) e a fonte reserva (FR-005, US2-AS3) não foram implementados. Specs e STATUS trazem dados do ambiente local do dono. O README contradiz o STATUS e não documenta `lab setup`.
4. **Médio:** `PGPASSWORD` vai em argumento de linha de comando. `plab up`/`down` sem alvo saem com 0 (reproduzido). O `plab scan` não cobre `lab-home` nem os logs de setup. Os contratos divergem do código e o `doctor` não diagnostica License Server/DBAccess. Há downloads sem checksum no Dockerfile.
5. O que foi executado aqui passou: shellcheck 0.11.0, validador e 66 testes da skill, `test_encoding.sh`, `docker compose config` das 3 stacks e testes isolados de `segredos.sh` e `templates.sh`. Tudo que depende das stacks Protheus está marcado como **não verificável aqui**.

---

## Escopo, método e limites

- **Revisado:** commit `62b49c3` (único do repositório; `main` e `claude/funny-hawking-8byuzs` iguais), 119 arquivos versionados.
- **Lido integralmente:** `plab`, `plab.ps1`, `lab/bin/**`, `lab/setup/**`, `lab/tir/*.py`, `lab/tests/*`, `lab/Dockerfile`, `lab/compose.yaml`, `stacks/**`, `.github/workflows/ci.yml`, `.env.example`, `.gitignore`, `.dockerignore`, `.gitattributes`, `README.md`, `STATUS.md`, READMEs e código dos cenários, `skills/compilar-advpls-lab`, constituição, spec, contratos, `plan.md` (conformidade e complexidade), `tasks.md` e `quickstart.md`.
- **Executado neste ambiente (Linux, sem daemon Docker, sem stacks Protheus):**
  - `shellcheck 0.11.0 -x -s bash` nos mesmos arquivos do CI: **0 achados**.
  - `skills/testes-protheus`: `validate_package.py .` → `"ok": true`; `unittest` → `Ran 66 tests … OK`.
  - `bash lab/tests/test_encoding.sh` → `fontes: 1 falhas: 0` (LABHELLO.prw CP1252 + CRLF, conferido também com `od -c`).
  - `docker compose config --quiet` (Compose v5.6.1) nas stacks 2610, 2510 e no lab, com `.env` copiado do exemplo: **ok**.
  - `plab` (bash) com um `docker` falso no `PATH`: códigos de saída de `up`, `down`, `logs`, `smoke`, `status`, `scan`, checagem de porta ocupada e falha do `restart` dentro do `smoke`.
  - `lab/setup/lib/segredos.sh` e `templates.sh` com `HOME` temporário: troca de chave sem duplicar, recusa de valor vazio, modo 600, ida e volta de valor com `'"$\`` e idempotência byte a byte dos AGENTS/CLAUDE/GEMINI.md.
  - Busca no histórico (`git log --all -p`) por padrões de chave (`sk-`, `sk-ant-`, `ghp_`, `AKIA`, `PRIVATE KEY`, `xox?-`, `PASSWORD=<valor>`): só aparece `PGPASSWORD=protheus` (ver M1).
  - SHAs das actions: `actions/checkout@3d3c42e…` corresponde ao commit "prep v7.0.1 release". O commit `actions/setup-python@6d4fd22…` existe no repositório oficial, mas não deu para confirmar aqui que ele é a tag v7.1.0.
- **Não verificável aqui:** subida das stacks, login, compilação, smoke, `lab setup` real, `docker inspect`/`docker history` da imagem `plab-lab`, gitleaks (sem daemon), comportamento das imagens `emebatista/*`. Nesses pontos o relatório cita a evidência que o `STATUS.md` declara, sem confirmá-la.

Legenda de severidade:
- **Bloqueante:** impede publicar ou declarar o kit pronto.
- **Alto:** requisito MUST não atendido ou defeito que quebra o uso documentado.
- **Médio:** desvio de princípio ou contrato, ou risco relevante.
- **Baixo:** robustez, higiene ou documentação.

---

## Achados

### Bloqueante

**B1. O gate final da constituição não tem evidência, e o STATUS se contradiz**
- **Onde:**
  - `.specify/memory/constitution.md:91-92` (gate final).
  - `specs/001-protheus-2610-lab/tasks.md:151-153` (T051–T053 abertas).
  - `STATUS.md:7` ("Fase 0"), `STATUS.md:71`, `STATUS.md:75`, `STATUS.md:86-88`.
- **Fatos:**
  - O STATUS ainda declara "Fase 0", lista "T026–T028 smoke completo" como pendência e mantém em AGUARDANDO_USUARIO a senha da 2510, que a linha 61 dá como resolvida.
  - Nenhuma linha registra subida do zero (clone limpo + `down -v` + `.env.example`), nem `plab scan` final com zero ocorrências, nem `docker ps` final comparado ao baseline (SC-008).
  - A linha 63 diz "scan sem segredos (só falha a trava de histórico)", ou seja, o último scan registrado **não** deu zero.
- **Impacto:** pelo Princípio III e pelo gate final, o kit não pode ser declarado pronto nem publicado. Quem retomar o trabalho (Princípio VI) lê um estado falso.
- **Correção sugerida:**
  - Executar T051–T053 e registrar comando + saída resumida no STATUS.
  - Reescrever as seções "Fase atual", "Em andamento", "Pendências" e "AGUARDANDO_USUARIO".
  - Marcar as tarefas concluídas em `tasks.md`.

**B2. Falta aviso de marca e de não afiliação à TOTVS**
- **Onde:** `README.md:1-9`, `README.md:121-128`, `LICENSE:3`; o nome do projeto é "Protheus 2610 Lab".
- **Fatos:** o README diz que Protheus, AppServer etc. "pertencem à TOTVS", mas não diz que "TOTVS" e "Protheus" são marcas da TOTVS S.A., que o projeto não é afiliado, endossado nem suportado pela TOTVS, nem que a licença MIT cobre só o código do lab.
- **Impacto:** risco jurídico e de reputação ao publicar com a marca no nome.
- **Correção sugerida:**
  - Adicionar no topo do README e no rodapé uma seção "Marcas e afiliação" com esse texto.
  - Avaliar um nome sem a marca (ex.: "lab-2610 para Protheus") ou obter orientação jurídica antes de publicar.

### Alto

**A1. Scripts versionados como `100644`: `./plab` e `plab scan` não funcionam em Linux, macOS ou WSL**
- **Onde:** índice git (`git ls-files -s`). Afeta `plab`, `lab/bin/plab-scan`, `lab/bin/lab`, `lab/bin/lib/*.sh`, `lab/setup/lab-setup.sh`, `lab/tests/*.sh` e `stacks/2510/entrypoint-lab.sh`, todos `100644`.
- **Reproduzido:**
  - `./plab up` → `Permission denied` (rc 126).
  - `bash plab scan` → rc 126, porque `plab:199` faz `exec "$RAIZ/lab/bin/plab-scan"`.
- **Impacto:**
  - O README (`README.md:35`) e o contrato `plab-cli.md` mandam usar `./plab`.
  - O gate de segredos (Princípio II) fica inacessível pelo wrapper bash.
  - Dentro da imagem não há problema, porque o `Dockerfile:103` aplica `chmod 0755`. O entrypoint da 2510 é chamado via `/bin/bash`.
- **Correção sugerida:**
  - `git update-index --chmod=+x` nesses arquivos.
  - Em `plab:199`, usar `exec bash "$RAIZ/lab/bin/plab-scan"`.
  - Adicionar ao CI uma checagem de modo (`git ls-files -s | awk '$1!="100755"' …` para a lista de executáveis).

**A2. FR-020 / SC-006 não atendidos: há 1 cenário de interface, não 3 a 5**
- **Onde:** `cenarios/` só tem `hello`, `ui-smoke` (MATA010) e `tir-smoke` (a mesma MATA010, bloqueada). Tarefas `tasks.md:129-134` (T039–T044) abertas.
- **Fatos:** não há cenários de fornecedores, clientes nem financeiro. Os READMEs existentes marcam releases como "pendente" (`cenarios/hello/README.md:38-39`, `cenarios/ui-smoke/README.md:43`).
- **Impacto:** a User Story 5 e o SC-006 ficam não atendidos.
- **Correção sugerida:**
  - Parametrizar `smoke_ui.py`, que já aceita `PLAB_UI_MENU`, `PLAB_UI_ABA` e `PLAB_UI_TITULO`, para MATA020, MATA030/CRMA980 e FINA040/050.
  - Criar um README por cenário com as releases confirmadas.
  - Ou reduzir formalmente o escopo na spec, com registro no STATUS.

**A3. FR-005 parcial e US2-AS3 não atendido: a fonte reserva não existe como configuração**
- **Onde:**
  - `README.md:72-75`: reservas citadas sem tag nem digest.
  - `tasks.md:75`: T018 aberta.
  - `stacks/reserva/` inexistente, embora o `plan.md` e a T002 o prevejam.
  - `.github/workflows/ci.yml:46`: o passo chama-se "compose config (… reservas)", mas não valida reserva alguma.
- **Impacto:** se as imagens `emebatista/*` sumirem (o risco R3 do próprio STATUS), não há caminho "pelo mesmo comando". O FR-005 exige digest também para a reserva.
- **Correção sugerida:**
  - Implementar `stacks/reserva/2510-oficial` e `2610-feliperaposo` com digests e uma variável de seleção (ex.: `PLAB_2610_FONTE=reserva`).
  - Documentar as diferenças no README.
  - Ou registrar o desvio na spec e corrigir o nome do passo no CI.

**A4. Specs e STATUS trazem dados do ambiente local do dono**
- **Onde:**
  - `.specify/memory/constitution.md:43` e `specs/001-protheus-2610-lab/plan.md:44`: nomes de stacks locais `protheus-teste` e `protheus_ia_lab`.
  - `specs/001-protheus-2610-lab/quickstart.md:16` e `tasks.md:29,58`: os mesmos nomes.
  - `specs/001-protheus-2610-lab/research.md:57`: portas da stack local (`1234/18080/18081/57890/55434`).
  - `plan.md:44`: "31 GB do Docker".
  - `tasks.md:108` e `plan.md:104`: caminho `../insumos/`.
  - `STATUS.md:92-94`: caminhos pessoais `~/.claude/skills/...` e `~/.codex/skills/...` e o estado das cópias locais do dono.
  - `STATUS.md:27`: "11 containers pré-existentes".
- **Impacto:** expõe o inventário da máquina do autor e não serve a terceiros. Contraria o espírito do Princípio I, que proíbe dados de terceiros e de ambiente.
- **Correção sugerida:**
  - Trocar por exemplos genéricos ("outra stack Protheus local, ex.: porta 1234").
  - Mover o baseline e as notas pessoais para fora do repositório.
  - Revisar `STATUS.md` antes de publicar.

**A5. README contradiz o STATUS e não documenta o assistente de IA**
- **Onde:**
  - `README.md:18`: compilação da 2510 "bloqueada". O `STATUS.md:61-63` diz que ela passa e que `plab smoke 2510` deu PRONTO duas vezes.
  - `README.md:58-68`: a tabela de comandos não traz `plab setup`, `plab scan`, `plab ports`, `plab net`, `plab restart` nem `lab setup`.
  - O README não tem nenhuma seção sobre IA (Claude/Codex, conta × chave, `secrets.env`, skills publicadas).
  - `README.md:28`: RAM "~1,0 GB por release … Reserve 8 GB", enquanto os `mem_limit` somam 10 GB por release mais 4 GB do lab (`.env.example:56-60`). Não há medição das duas releases juntas.
- **Impacto:**
  - FR-021 e SC-009 ficam parciais.
  - SC-001 ("seguindo apenas o README") não se sustenta para a User Story 4.
  - Quem lê o README recebe um status falso (Princípio III).
- **Correção sugerida:**
  - Atualizar a tabela de status a partir do STATUS (com data).
  - Adicionar a seção "Assistente de IA (`plab setup`)".
  - Completar a tabela de comandos.
  - Medir e publicar RAM e disco das duas releases juntas e explicar a relação com os `mem_limit`.

### Médio

**M1. Senha do banco em argumento de linha de comando (Princípio II, NON-NEGOTIABLE)**
- **Onde:** `plab:84` e `plab.ps1:132` (`docker compose exec -T -e PGPASSWORD=protheus db psql …`); portas `127.0.0.1:26432` e `127.0.0.1:25432` publicadas (`stacks/2610/compose.yaml:23`, `stacks/2510/compose.yaml:23`).
- **Impacto:**
  - A senha aparece na lista de processos do host e fica versionada.
  - É a senha padrão pública da imagem, mas o princípio não abre exceção.
  - Com o Postgres publicado em localhost, qualquer processo local entra na base com essa credencial conhecida.
- **Correção sugerida:**
  - Rodar o `psql` pelo socket local como usuário do container (ex.: `exec -T -u postgres db psql -d protheus -f …`, se o `pg_hba` permitir; não verificável aqui) ou com `PGPASSFILE` já existente na imagem.
  - Registrar a exceção na seção Complexity Tracking do `plan.md`.
  - Avaliar não publicar a porta do banco por padrão (porta opcional via override).

**M2. `renova-senha-admin.sql` altera a política de senha da base sem registro de governança**
- **Onde:** `stacks/sql/renova-senha-admin.sql:6-10`, aplicado em todo `up` (`plab:97`, `plab.ps1:145`) nas **duas** releases.
- **Fatos:**
  - A cada subida, o script atualiza `sys_usr.usr_dtchgpsw` para evitar a troca obrigatória de senha.
  - A falha só gera aviso (`plab:87`), e o `compose cp` silencia erros (`plab:83`).
  - O arquivo `/tmp/plab-renova-senha.sql` fica no container `db`.
- **Impacto:**
  - A constituição proíbe "contornar autenticação". Isto não pula a senha, mas pula um controle de autenticação, e não há registro de autorização do dono nem justificativa no Complexity Tracking.
  - Na 2610 a medida não é necessária, segundo o próprio STATUS.
- **Correção sugerida:**
  - Registrar a decisão (o quê, por quê, autorização) no STATUS e no `plan.md`.
  - Aplicar só onde for necessário (variável por release).
  - Remover o arquivo temporário.
  - Tratar a falha do `cp`.

**M3. Códigos de saída do `plab` divergem do contrato (reproduzido)**
- **Onde:** `plab:33-39` (`alvos` chama `sair` dentro de `$(…)`, e o `exit` só encerra o subshell), `plab:93`, `plab:105`, `plab:195`, `plab:152-168` e `plab.ps1:212-234`.
- **Reproduzido:**

  | Comando | Resultado | Esperado (contrato) |
  |---|---|---|
  | `plab up` | rc **0**: cria a rede e lista o status de todas | rc 2 |
  | `plab down` / `plab down foo` | rc **0** | rc 2 |
  | `plab logs foo` | chama `docker compose -f "" logs` | rc 2 |
  | `plab smoke 2510` com falha no `restart` | rc **5**, sem a linha `FALHOU … passo 5/recuperacao` | rc 15 (`plab:167`, inalcançável porque `cmd_restart` chama `sair 5`) |

  O mesmo erro do passo 5 existe no `plab.ps1:222` (`Sair 5` dentro de `Cmd-Restart`). O PowerShell trata `up` sem alvo corretamente (rc 2), então os dois wrappers divergem.
- **Correção sugerida:**
  - Validar o alvo antes do laço (`alvos "$1" >/dev/null || exit 2`, ou validar fora de `$(…)`).
  - Fazer `cmd_restart` retornar o código em vez de sair quando chamado pelo smoke.

**M4. `plab scan` não cobre o que a constituição exige**
- **Onde:** `lab/bin/plab-scan:24-36` e `lab/bin/plab-scan.ps1:25-48`; `.specify/memory/constitution.md:23-24`; FR-023.
- **Fatos:**
  - Procura apenas os valores `*_PASSWORD/_TOKEN/_KEY/_SECRET` do `.env` com 6 caracteres ou mais (`plab-scan:27`).
  - Não procura as chaves de API (`~/.config/lab/secrets.env`, `~/.codex/auth.json`, `~/.claude/.credentials.json` no volume `lab-home`).
  - Não varre `docker logs` dos serviços, os logs do `lab setup`, `/workspace` nem os AGENTS/CLAUDE/GEMINI.md.
  - Se a imagem `plab-lab:local` não existir, o item sai como **OK** (`plab-scan:32`, saída vazia → 0) em vez de "não verificado".
- **Impacto:** o SC-005 ("logs do setup") não é demonstrável, e um "OK" pode ser falso.
- **Correção sugerida:**
  - Ler, de dentro do container lab, os valores de `secrets.env` e das credenciais das CLIs (sem imprimir) e procurá-los em `docker logs`, `evidencias/`, `workspace/`, imagem e histórico.
  - Tratar "imagem ausente" ou "container parado" como `NAO_VERIFICADO`, com rc diferente de 0 no modo gate.

**M5. Contratos e spec divergem da implementação (US3, smoke-report, lab-setup-cli, plab-cli)**
- **Onde e fatos:**
  - `contracts/smoke-report.md:6-13,17-30` × `lab/bin/lib/smoke.sh:15-74`:
    - A ordem real é doctor → **interface (Playwright)** → compile → limpeza. O contrato diz doctor → compile → **tir** → limpeza.
    - Falha de compilação sai com 13, não 12.
    - O `resumo.json` não tem `versoes`, `severidades`, `testes` nem `falhas`.
  - A spec (US3, FR-015) pede suíte TIR. O TIR virou passo informativo (`smoke.sh:54,60`) por causa de um bloqueio upstream documentado (`README.md:99-103`). Isso não está na spec nem no Complexity Tracking.
  - `contracts/lab-setup-cli.md:13`: "se duas [healthy], pergunta". O código escolhe a primeira (`lab-setup.sh:47`).
  - `contracts/lab-setup-cli.md:23`: o `config.json` deveria ficar em `~/.config/lab/tir/<release>/`. O código gera config temporária por execução (`tir.sh:15-50`), o que é mais seguro, mas o contrato não mudou.
  - `contracts/plab-cli.md:21`: "listando porta e dono". O bash não mostra o dono (`plab:73`).
  - `contracts/plab-cli.md`: não cita `restart` nem o passo 5 / código 15.
  - O contrato não define os códigos do `doctor` (11–16), que se sobrepõem aos do smoke (11–14) com outro significado (`doctor.sh:30-53`).
- **Correção sugerida:** emendar spec e contratos (registrar a data no STATUS), completar o `resumo.json` e adotar uma faixa própria para os códigos do `doctor` (ex.: 30+).

**M6. `doctor` não cobre o diagnóstico previsto em FR-008 e nos edge cases**
- **Onde:** `lab/bin/lib/doctor.sh:28-53`.
- **Fatos:** checa DNS, TCP 1234, `/webapp/`, `/app-root/`, `/rest/` e o secret. Não checa License Server, DBAccess nem banco, e não verifica memória. A spec pede que o diagnóstico "identifica o License Server como causa" e "mostra o consumo e recomenda parar uma das releases".
- **Correção sugerida:**
  - Adicionar testes TCP a `license-server-<rel>:5555` e `dbaccess-<rel>:7890`. Isso exige que o lab alcance esses aliases, que hoje estão só na rede `default` da stack.
  - Ou fazer `plab status` no host interpretar a saúde por serviço e o `docker stats`.

**M7. Supply chain da imagem `lab`: downloads sem checksum e dependências sem lock (Princípios I e VI)**
- **Onde:**
  - `lab/Dockerfile:23-27`: Chrome for Testing e chromedriver baixados sem `sha256sum -c`. O Node é conferido (`:19-21`).
  - `lab/Dockerfile:28`: `npm install @totvs/tds-ls@X` sem lockfile, com dependências transitivas soltas.
  - `lab/Dockerfile:81-83`: `pip install tir_framework==X playwright==Y` sem `--require-hashes`, com dependências transitivas soltas (Selenium etc.).
  - `lab/Dockerfile:51-61`: pacotes apt sem versão.
  - `lab/setup/providers/*.sh`: `npm install -g` das CLIs de IA, também sem lock.
- **Impacto:** builds em datas diferentes produzem imagens diferentes, e um pacote transitivo comprometido entra sem aviso.
- **Correção sugerida:**
  - Fixar o SHA-256 dos zips do Chrome no `.env.example`.
  - Usar `requirements.lock` com hashes (`pip install --require-hashes`).
  - Versionar um `package-lock.json` para `tds-ls`.
  - Registrar no README que o apt segue o snapshot do digest do Ubuntu.

**M8. Bind mounts `../workspace` e `../evidencias` em Docker Engine Linux (não verificável aqui)**
- **Onde:** `lab/compose.yaml:68-69`; `Dockerfile:91-93` (usuário `lab`, UID 1000).
- **Fatos:**
  - `workspace/` não existe no clone (está ignorado). O Docker Engine cria a origem inexistente de um bind como `root:root`, e aí o usuário `lab` não grava `/workspace`: `gerar_instrucoes` falha e a IA não consegue salvar fontes.
  - `evidencias/` pertence ao UID de quem clonou. Se esse UID não for 1000, o smoke não grava evidências.
  - No Docker Desktop (plataforma de referência) o comportamento é diferente, o que explica o sucesso relatado.
- **Correção sugerida:**
  - Fazer `plab up lab` criar `workspace/` e `evidencias/` antes de subir.
  - Documentar o UID 1000 ou permitir `user: "${UID}:${GID}"`.
  - Marcar no README "Linux nativo: não testado".

**M9. `lab tir` copia logs do TIR sem saneamento e perde a evidência sem `PLAB_EVID_DIR`**
- **Onde:** `lab/bin/lib/tir.sh:58-60` e `tir.sh:18`.
- **Fatos:**
  - Só `tir.out` passa pelo `sed` do `"Password"`. O conteúdo de `LogFolder` (logs do próprio TIR) é copiado sem filtro. Se o TIR registra parâmetros de login ou a config no log, a senha chega às evidências (não verificável aqui).
  - O passo 4 do smoke só confere isso quando `PLAB_SMOKE_TIR=1`.
  - Sem `PLAB_EVID_DIR`, as evidências ficam em `$tmp/evid`, que o `trap` apaga, e a mensagem final aponta para um caminho que já não existe.
- **Correção sugerida:**
  - Antes de copiar, procurar o valor do secret em todo o conteúdo (como o passo 4 do smoke) e falhar se encontrar.
  - Usar por padrão `/opt/plab/evidencias/<rel>/tir-<carimbo>`.

**M10. `includes-init` usa os includes da 2610 também para compilar na 2510 (não verificável aqui)**
- **Onde:** `lab/compose.yaml:12-29`, `src=/protheus12/bin/appserver_deskflow/includes` da imagem `PLAB_2610_IMG_APPSERVER`.
- **Impacto:**
  - Includes de outra release podem divergir (defines, `PRTOPDEF.CH`).
  - Quem quer só a 2510 precisa baixar a imagem AppServer da 2610 (cerca de 16 GB, segundo o README).
  - A pasta de origem pertence ao DeskFlow, que está fora do escopo e pode sumir em outra versão da imagem.
- **Correção sugerida:** volume de includes por release (`includes-2610` e `includes-2510`), com `compile.sh` escolhendo pelo `rel`. Documentar a origem.

### Baixo

**L1. Idempotência frágil dos serviços `*-init`**
- **Onde:** `stacks/2610/compose.yaml:91`, `stacks/2510/compose.yaml:87`, `lab/compose.yaml:21`.
- **Fatos:** a semeadura testa só a existência de um arquivo (`tttm120.rpo` ou `prtopdef.ch`). Se um `cp -a` for interrompido depois de copiar esse arquivo, o volume fica parcial e nunca é ressemeado.
- **Correção sugerida:** copiar para `/dst/.tmp` e renomear no fim, ou gravar um sentinela (`.plab-seeded`) só depois do `cp` completo.

**L2. A rede `plab` pré-existente é reutilizada sem conferir a origem**
- **Onde:** `plab:41-44` e `plab.ps1:67-76`.
- **Fatos:** se a máquina já tiver uma rede chamada `plab` de outro projeto, o lab se conecta a ela. Isso contraria o Princípio IV ("MUST NOT reutilizar").
- **Correção sugerida:** criar com `--label com.plab.owner=plab` e recusar uma rede sem o label.

**L3. Detalhes de robustez do `plab`**
- `plab:108`: `read` com stdin fechado aborta com rc 1 por causa do `set -e` (reproduzido).
- `plab:16`: o `.env` é executado como shell (`. .env`). Valores com espaço ou `$` são interpretados de forma diferente do Docker Compose, e o arquivo vira código executável.
- `plab.ps1:30-33`: o parser simplificado não trata comentário inline.
- **Correção sugerida:** um parser `KEY=VALUE` próprio no bash (como no PowerShell) e `read … || conf=""`.

**L4. Verificação de limpeza do smoke (passo 4) com falsos positivos e negativos**
- **Onde:** `lab/bin/lib/smoke.sh:73-74`.
- **Fatos:**
  - Se o secret estiver ausente, `grep -f` recebe padrões vazios e o passo passa.
  - Um secret com `\r` não casa.
  - Uma linha vazia no arquivo casa com tudo.
  - Não verifica `/tmp/plab-ui-*` (padrão do `ui.sh:7`).
- **Correção sugerida:** ler o secret como `senha_admin` faz (sem `\r\n`), exigir valor não vazio e incluir os diretórios de UI.

**L5. `compile.sh`: entradas atípicas**
- `compile.sh:57`: falha do `iconv` (senha com caractere fora do CP1252) não é tratada e gera script truncado.
- `compile.sh:44`: nomes com vírgula ou espaço quebram `program=`.
- Fontes com o mesmo `basename` em pastas diferentes se sobrescrevem (falha segura, mas a mensagem confunde).
- **Correção sugerida:** checar o rc do `iconv`, recusar nomes com `,` e detectar duplicados.

**L6. `lab setup`: estados e mensagens**
- `lab-setup.sh:120`: sai com 0 mesmo quando todas as IAs falharam (só o smoke conta).
- O edge case "Enter vazio → oferece repetir ou pular" virou "cancelado" (`segredos.sh:19`).
- `lab-setup.sh:89`: guarda em `state.json`, que por contrato não tem segredo, até 160 caracteres da saída da CLI. Algumas CLIs ecoam parte mascarada da chave.
- Codex:
  - A chave também fica em `~/.codex/auth.json`, gravado pela própria CLI. É um desvio inevitável do "gravadas apenas em `secrets.env`" que precisa ser registrado.
  - `OPENAI_API_KEY` fica em `secrets.env` sem nenhum consumidor, porque `codex` é um symlink e não um wrapper (`codex.sh:21`).
- `test_setup_idempotente.sh` cobre só o modo `conta` não interativo.
- **Correção sugerida:** código de saída diferente de 0 quando houver `falhou(...)`, laço de repetição no `segredo_ler`, gravar no `state.json` só a categoria do erro e registrar o desvio do Codex no `plan.md`.

**L7. Arquivos temporários de segredo/estado em `/tmp` com `mv` entre sistemas de arquivos**
- **Onde:** `lab/setup/lib/segredos.sh:23` e `estado.sh:13`.
- **Fatos:**
  - O `mktemp` cria em `/tmp` (camada do container) e o `mv` leva para o volume `lab-home`, o que equivale a cópia + remoção, não atômica.
  - Se a operação falhar, fica em `/tmp` uma cópia de **todos** os segredos (modo 600).
  - O diretório só vira 700 porque `estado_iniciar` roda antes (`estado.sh:7`); `segredos_preparar` sozinho deixa 755 (reproduzido).
- **Correção sugerida:** `mktemp "$LAB_CFG/.secrets.XXXXXX"` e `chmod 700` dentro de `segredos_preparar`.

**L8. `gerar_instrucoes` trunca o arquivo do usuário se houver `BEGIN` sem `END`**
- **Onde:** `lab/setup/lib/templates.sh:18-20`.
- **Correção sugerida:** só substituir se houver os dois marcadores; caso contrário, avisar e não gravar.

**L9. Endurecimento dos containers**
- **Onde:** `lab/compose.yaml:34-76`, `stacks/2610/compose.yaml:20`, `lab/Dockerfile:69-72`.
- **Fatos:**
  - O lab não tem `cap_drop: [ALL]` nem `security_opt: [no-new-privileges:true]`.
  - O Chrome roda com `--no-sandbox` (documentado).
  - O `db` da 2610 roda como `user: root` sem justificativa no README.
  - `restart: unless-stopped` em tudo faz as stacks voltarem sozinhas com o Docker Desktop, consumindo RAM em máquinas que têm outros ambientes (Princípio IV).
- **Correção sugerida:** adicionar `cap_drop`/`no-new-privileges` ao lab, justificar o `root` ou removê-lo, e considerar `restart: "no"`.

**L10. CI: referências quebradas e pequenos endurecimentos**
- `.github/workflows/ci.yml:3` cita `docs/PUBLICACAO.md`, que não existe.
- `ci.yml:46` cita "reservas" (ver A3).
- `actions/checkout` sem `persist-credentials: false` (`ci.yml:19,70`).
- `plab.ps1` e `plab-scan.ps1` sem lint (PSScriptAnalyzer).
- Não há checagem de bit executável (A1).
- Não foi possível confirmar aqui que o SHA do `setup-python` corresponde à tag v7.1.0.
- **Pontos positivos:** actions por SHA, `permissions: contents: read`, imagens auxiliares (shellcheck, gitleaks) por digest, nenhum `pull_request_target` e nenhum segredo usado.

**L11. Documentação desatualizada em pontos menores**
- `cenarios/hello/README.md:38-39`: "pendente" nas duas releases. O STATUS registra SUCCESS em ambas.
- `cenarios/ui-smoke/README.md:24`: "passo 3 do smoke". Na verdade é o passo 2.
- `cenarios/ui-smoke/README.md:37`: as capturas reais se chamam `01-menu.png` e `02-rotina.png`.
- `cenarios/ui-smoke/README.md:43`: 2510 "pendente", mas a 2510 já passou.
- `skills/compilar-advpls-lab/SKILL.md:18`: diz que P2510D "compartilha o RPO de P2510". Hoje há RPO próprio (`stacks/2510/entrypoint-lab.sh`).
- `skills/compilar-advpls-lab/SKILL.md:39-40`: manda informar `PLAB_INCLUDES`, mas os includes vêm do volume (linhas 51-53 da mesma skill).
- `lab/Dockerfile:41`: `LABEL licenses="MIT"` numa imagem que contém `advpls` (TOTVS) e o Chrome. Sugestão: `"MIT AND LicenseRef-terceiros"`.
- `STATUS.md:26`: cita os commits `b2bf57b..932a442`, que não existem no histórico atual (squash).
- `STATUS.md:77`: a pendência de reescrever o histórico já foi feita (só `.gitkeep` em `evidencias/`).
- `.env.example:85`: `PLAB_EXEMPLOS_COMMIT` vazio faz `--with-exemplos` não fazer nada, sem aviso (`skills.sh:46`). Isso deixa o FR-019 parcial.

**L12. Terceiros e autoria (decisão do dono antes de publicar)**
- `.claude/skills/speckit-*` e `.specify/**` vêm do GitHub Spec Kit (`author: "github-spec-kit"`) e foram copiados sem o aviso de licença MIT do projeto de origem. Sugestão: incluir `THIRD_PARTY_NOTICES.md` ou retirar do repositório público (o `.dockerignore` já os exclui da imagem).
- O commit está assinado com e-mail pessoal (`git log --format='%ae'`), que se torna público junto com o histórico. Sugestão: usar o e-mail `noreply` do GitHub, se for o desejo do dono.
- O `author: daniel.montagna` nos arquivos é coerente com o `LICENSE`. Ponto informativo.
- `docs/upstream/tir-issue-selectenv.md:3` já diz "autorizado". Antes de enviar, confirmar que a issue não traz caminho ou host locais (não encontrei nenhum).

---

## Conformidade com a constituição (Princípios I–VI)

| Princípio | Situação | Evidência | O que falta |
|---|---|---|---|
| I. Padrão TOTVS, sem redistribuição | **Parcial** | Nenhum `.rpo`, `.ch`, `appserver.ini` ou binário versionado (`git ls-files`; scan item 4 em `plab-scan:39`). Imagens principais por tag + digest (`.env.example:11-22`). Ubuntu por digest (`Dockerfile:6`). Includes semeados da imagem do usuário (`lab/compose.yaml:12-29`) | Reserva sem digest (A3). Chrome sem checksum (M7). Dados do ambiente local nos specs (A4). Aviso de marca (B2) |
| II. Segredos fora de tudo | **Parcial** | Senha do Admin como secret de arquivo (`lab/compose.yaml:72-82`, `lab/bin/lib/comum.sh:27-32`). `read -s` + 600 (`lab/setup/lib/segredos.sh:15-28`). Temporários 0700/0600 com `trap` (`compile.sh:30-33,47`; `tir.sh:15-22`). Saneamento do `psw` (`compile.sh:74`). Wrapper Claude carrega só a sua chave (`claude.sh:22-29`). Histórico sem segredo (verificado aqui) | `PGPASSWORD` em argumento (M1). Scan sem cobertura de setup/`lab-home` (M4). Logs do TIR sem filtro (M9). Codex grava a chave fora do `secrets.env` (L6) |
| III. Evidência antes de afirmação | **Parcial** | O STATUS separa evidência de achados; o README diz "não testado"/"bloqueado" onde cabe | STATUS e README contraditórios (B1, A5). Evidências citadas estão em `evidencias/` (fora do git), sem resumo no STATUS para alguns itens (T026–T038) |
| IV. Isolamento e mínimo privilégio | **Atendido com ressalvas** | `name: plab-*`, sem `container_name`, volumes e redes próprios, binds em `127.0.0.1` (`stacks/*/compose.yaml`). Sem `docker.sock`, `pid: host` ou `privileged`. `devmem.yaml` opcional e justificado (`README.md:84-86`). Teste T017 55/55 (STATUS, não verificável aqui) | Rede `plab` reutilizável (L2). `restart: unless-stopped` (L9). `db` como root (L9) |
| V. AdvPL/TLPP disciplinado | **Atendido** | `LABHELLO.prw` CP1252/CRLF (verificado aqui). `.gitattributes:15-19` com `-text`. Símbolos com links do TDN (`cenarios/hello/README.md:29-34`). Severidades e FATAL/ERROR invalidam o lote (`compile.sh:76-96`). CI de encoding (`ci.yml:43-44`) | `test_encoding.sh` não cobre `.aph` (citado nas preferências do dono, não na constituição) |
| VI. Reprodutibilidade e retomada | **Parcial** | Versões no `.env.example:69-85`. Imagens por digest. Actions por SHA | Dependências transitivas sem lock (M7). STATUS desatualizado (B1). Histórico em um único commit: "um commit por tarefa" não é verificável no histórico publicado. Autorização para criar o remoto privado não está registrada no STATUS (FR-024) |

## Conformidade com a spec (FR-001..FR-024)

| FR | Status | Evidência (arquivo:linha) | O que falta |
|---|---|---|---|
| FR-001 | Atendido (runtime não verificável aqui) | `stacks/2610/compose.yaml:16-134`, `stacks/2510/compose.yaml:16-134`; STATUS T011/T016 | — |
| FR-002 | Atendido | `plab:91-100` (`up --wait`), `plab:102-114`; base já restaurada (`stacks/2610/compose.yaml:25-27`) | Na 2510, compilar exigiu troca manual da senha do Admin (STATUS:61). Documentar no README (A5) |
| FR-003 | Atendido | `name: plab-2610/2510`, portas `127.0.0.1:` (`stacks/*/compose.yaml:23,45,111-113`); STATUS:42 (T017) | Evidência só no STATUS (não verificável aqui) |
| FR-004 | Atendido com ressalva | Portas via `.env` (`.env.example:27-37`); `checar_portas` (`plab:68-76`, rc 4 reproduzido) | Reuso da rede `plab` (L2). Bash não mostra o dono da porta (M5) |
| FR-005 | **Parcial** | Principal por digest (`.env.example:11-22`) | Reserva sem digest nem compose (A3) |
| FR-006 | Atendido | Sem `docker.sock`/`pid`/`privileged`; `stacks/override/devmem.yaml` opcional com justificativa (`README.md:84-86`, `plan.md:147`) | — |
| FR-007 | Atendido | `lab/Dockerfile` (TIR `:81`, Chrome `:23-27`, advpls `:28,76`, git `:53`, `USER lab` `:114`) | Lock de dependências (M7) |
| FR-008 | **Parcial** | `lab/bin/lib/doctor.sh:28-53` | License Server, DBAccess e memória (M6) |
| FR-009 | Atendido | `lab-setup.sh:53-74`; `claude.sh:33-49`; `codex.sh:24-44` | — |
| FR-010 | **Parcial** | `lab/setup/lib/segredos.sh:15-28`; wrapper `claude.sh:22-29`; `codex.sh:37` (stdin) | Codex sem wrapper e chave em `auth.json` (L6) |
| FR-011 | Atendido | Versão fixada (`claude.sh:13-19`, `codex.sh:13-19`); teste "OK" (`claude.sh:51-55`, `codex.sh:46-50`); `nao_testado` (`lab-setup.sh:82-83`) | O teste aceita qualquer saída com "OK" (fraco, baixo) |
| FR-012 | Atendido (local das skills conforme doc oficial: não verificável aqui) | `lab/setup/lib/skills.sh:29-50`; `templates.sh`; `templates/agent-rules.md.tmpl` | — |
| FR-013 | Atendido (runtime pelo STATUS:64) | `estado.sh`; `segredos.sh:24-25` sem duplicar (reproduzido); `templates.sh` idempotente (reproduzido); `lab/tests/test_setup_idempotente.sh` | Teste só cobre `conta` não interativo (L6) |
| FR-014 | Atendido (desvio favorável) | `tir.sh:15-50`: config temporária 0600, senha do secret | A spec diz "variável de ambiente" e o contrato diz config persistente: atualizar (M5) |
| FR-015 | **Parcial** | `compile.sh` (CP1252, severidades, limpeza); `smoke.sh:73-78` | Suíte de interface é Playwright, TIR só informativo, desvio não registrado na spec (M5) |
| FR-016 | **Parcial** | `smoke.sh:22-41,80-81`; evidências `compile.log`, `ui/`, `resumo.json` | Campos do `resumo.json` do contrato (M5) |
| FR-017 | Atendido | `skills/testes-protheus`; validador `ok` + 66 testes (executados aqui) | — |
| FR-018 | Atendido | `skills/compilar-advpls-lab/SKILL.md`; `compile.sh` (exit 21 para RPO em uso) | Documentação da skill desatualizada (L11) |
| FR-019 | **Parcial** | EngPro por commit (`.env.example:84`, `lab/setup/lib/skills.sh:38-45`), MIT, não vendorizada | `PLAB_EXEMPLOS_COMMIT` vazio: `--with-exemplos` não faz nada (L11) |
| FR-020 | **Não atendido** | Só hello + 1 cenário UI | A2 |
| FR-021 | **Parcial** | `README.md:24-29,97-132` | Setup de IA, comandos, RAM das duas juntas e status correto (A5); aviso de marca (B2) |
| FR-022 | **Parcial** | `STATUS.md` existe | Desatualizado (B1) |
| FR-023 | **Parcial** | Sem binários TOTVS no git; histórico sem segredo (verificado aqui); `plab scan` | Scan não cobre logs de setup nem `lab-home` (M4); último scan registrado não deu zero (STATUS:63) |
| FR-024 | Atendido (presumido) | Repositório privado | Registrar no STATUS a autorização para criar o remoto e para a futura publicação |

## Critérios de sucesso (SC-001..SC-009)

| SC | Status | Observação |
|---|---|---|
| SC-001 | Não verificado | Tempo de 10 minutos "seguindo só o README" não foi medido. O README não cobre todo o fluxo (A5) |
| SC-002 | Atendido segundo STATUS:42 | Não verificável aqui |
| SC-003 | Atendido segundo STATUS:59-63 | A 2510 só fica PRONTO com o passo 5 do `plab` (reinício). Não verificável aqui |
| SC-004 | Atendido segundo STATUS:64 | Cobertura do teste limitada (L6) |
| SC-005 | **Parcial** | Cobertura do scan (M4); scan final com zero não registrado (B1) |
| SC-006 | **Não atendido** | A2 |
| SC-007 | **Parcial** | STATUS registra só `conta` para Claude e Codex. As combinações `api_key` e opencode/Gemini (US6) não têm status "ok" nem "não testado (motivo)" |
| SC-008 | **Parcial** | Baseline "antes" registrado (STATUS:27); comparação final (T052) ausente |
| SC-009 | **Parcial** | RAM por release em repouso; falta a medição das duas juntas (A5) |

---

## Prontidão para publicação (checklist)

| Item | Situação |
|---|---|
| Segredos no histórico | Limpo (busca aqui + STATUS). Rodar gitleaks no gate final |
| `evidencias/` no histórico | Limpo (só `.gitkeep`) |
| Binários/fontes TOTVS | Nenhum versionado |
| Imagens de comunidade sem licença | O README avisa (`README.md:77-78,127`). Sugestão: destacar que as imagens contêm software TOTVS e que baixá-las é decisão e responsabilidade do usuário |
| Marcas TOTVS/Protheus | **Falta aviso** (B2) |
| Dados do ambiente local | **Remover** (A4) |
| Terceiros vendorizados (Spec Kit) | Falta aviso de licença (L12) |
| Workflow CI | Actions por SHA, permissões mínimas, sem segredos. Corrigir referências (L10) |
| `STATUS.md` | Reescrever antes de publicar (B1, A4) |
| E-mail do autor no commit | Decisão do dono (L12) |

Lembrete da constituição: esta revisão **não autoriza publicação**. A decisão é do dono.

---

## Ordem sugerida de correção

1. A1 (bit executável), M3 (códigos de saída) e B2 (aviso de marca): mudanças pequenas e sem risco.
2. A4 e B1 (limpar e atualizar specs e STATUS) e A5 (README).
3. M1, M2 e M4 (segredos e governança) e M5 (emendar contratos e spec).
4. A2 e A3 (cenários e reservas) ou redução formal de escopo.
5. Gate final: clone limpo, `down -v`, smoke nas duas releases, `plab scan` com zero ocorrências e `docker ps` comparado ao baseline, tudo registrado no STATUS.
