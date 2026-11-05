# Situação dos achados da revisão independente (03/11/2026)

A revisão (`REVISAO-INDEPENDENTE-2026-11.md`, PR #2) analisou o commit `62b49c3`. A tabela abaixo
mostra o estado de cada achado no `main` de 03/11/2026, conferido no código e no `STATUS.md`.
"Issue" quer dizer que o item fica aberto no GitHub depois da publicação, por decisão do dono:
os itens de severidade baixa não bloqueiam a abertura.

Atualização de 03/11/2026 (tarde): L1–L9 (issues #6–#14) corrigidos em um PR, um commit por
issue, validados por análise estática (`shellcheck` 0.11.0, `bash -n`, `docker compose config`) e
por testes locais sem container em `lab/tests/`. Os itens marcados "falta validar no lab" mexem
em compose ou rede e precisam de `plab up`, `plab smoke` e `lab cenarios` na máquina do dono.

| Achado | Situação | Como foi conferido |
|---|---|---|
| B1 gate final e STATUS | resolvido | `STATUS.md`: T051–T053, smoke PRONTO nas duas releases, cenários 5/5 |
| B2 aviso de marca | resolvido | `README.md`: topo e seção "Marcas e afiliação" |
| A1 bit executável | resolvido | `git ls-files -s`: 100755; passo de CI que confere o modo |
| A2 3 a 5 cenários | resolvido | `cenarios/ui-leitura/cenarios.json`: 5 rotinas de leitura; 5/5 nas duas releases no `STATUS.md` |
| A3 fonte reserva | desvio registrado, issue | fora desta versão; desvio no `STATUS.md` (FR-005/T018), reservas citadas no README |
| A4 dados do ambiente local | resolvido | `git grep` sem nomes de stacks locais; relatório final generalizado |
| A5 README × STATUS | resolvido | `README.md` cobre `plab setup`, `plab scan` e o status atual |
| M1 senha em argumento | resolvido | `plab`/`plab.ps1` leem `POSTGRES_PASSWORD` dentro do container; registrado no `plan.md` |
| M2 renovação da senha do Admin | resolvido | decisão do dono registrada no `STATUS.md` (03/11/2026) e no `plan.md` |
| M3 códigos de saída | resolvido | `plab down foo` e `plab logs foo` → rc 2 (reproduzido) |
| M4 cobertura do `plab scan` | resolvido | `plab-scan` verifica segredos do container lab e marca `N/VER` quando não consegue verificar |
| M5 contratos × código | resolvido | contrato do smoke: interface (Playwright) antes da compilação, códigos 11–14 |
| M6 doctor sem License/DBAccess | resolvido | `doctor.sh` testa TCP de License Server (5555) e DBAccess (7890), códigos 36–37 |
| M7 downloads sem checksum | resolvido (05/11/2026) | Node e Chrome/chromedriver com `sha256sum -c`; pip pelo `lab/deps/requirements.lock` (`--require-hashes`) e `tds-ls` por `npm ci` com `package-lock.json` (issue #4) |
| M8 bind mounts no Linux | resolvido | `plab` cria `workspace/` e `evidencias/` antes de subir |
| M9 logs do TIR | resolvido | `tir.sh` procura o segredo antes de copiar e usa `evidencias/` por padrão |
| M10 includes da 2610 na 2510 | issue | volume de includes único |
| L1 sentinela dos `*-init` | corrigido no PR das L1–L9, falta validar no lab | `stacks/semear-volume.sh` (sentinela `.plab-seeded` só no fim; volume antigo é completado sem sobrescrever o RPO); `lab/tests/test_semear_volume.sh` |
| L2 rede `plab` sem label | corrigido no PR das L1–L9, falta validar no lab | `plab`/`plab.ps1` criam com `com.plab.owner=plab` e recusam rede sem label (código 3), exceto a de versão anterior só com containers `plab-*`; bash testado com `docker` falso |
| L3 `.env` executado como shell | corrigido no PR das L1–L9 | parser `KEY=VALUE` no bash, sem exportar e sem ler senhas; `read … \|\| conf=""`; `plab.ps1` trata comentário inline; `lab/tests/test_plab_env.sh` |
| L4 falsos positivos do passo 4 | corrigido no PR das L1–L9 | senha lida sem `\r\n`, secret vazio reprova, `/tmp/plab-ui-*` incluído; `lab/tests/test_smoke_limpeza.sh` |
| L5 `compile.sh` com entradas atípicas | corrigido no PR das L1–L9 | rc do `iconv` (código 23), nome com vírgula ou espaço e duplicados (código 2); `lab/tests/test_compile_entradas.sh` |
| L6 `lab setup` e estados | corrigido no PR das L1–L9 (parcial: laço do Enter vazio fica de fora) | código 1 com `falhou(...)`; `state.json` só com a categoria, estados antigos saneados; desvio do Codex no `plan.md`; `lab/tests/test_setup_estados.sh` |
| L7 temporários em `/tmp` | corrigido no PR das L1–L9 | `mktemp` no próprio `~/.config/lab`, `chmod 700` em `segredos_preparar`, temporário apagado em falha; `lab/tests/test_segredos_tmp.sh` |
| L8 marcadores BEGIN/END | corrigido no PR das L1–L9 | só substitui com um BEGIN e um END em ordem; nos outros casos avisa e não grava; `lab/tests/test_templates_marcadores.sh` |
| L9 endurecimento dos containers | corrigido no PR das L1–L9, falta validar no lab | lab com `cap_drop: [ALL]` e `no-new-privileges`; `user: root` do `db` removido (era o padrão da imagem; o entrypoint do Postgres passa para `postgres`); `PLAB_RESTART` (padrão `unless-stopped`) |
| L10 CI | resolvido | referência ao plano corrigida; `persist-credentials: false` nos dois `checkout` |
| L11 documentação desatualizada | resolvido | READMEs de `hello` e `ui-smoke` atualizados |
| L12 terceiros e autoria | resolvido | `THIRD_PARTY_NOTICES.md` (Spec Kit, MIT). E-mail dos commits mantido: o dono já o usa em outros repositórios públicos e os PRs guardariam o commit original de qualquer forma |
