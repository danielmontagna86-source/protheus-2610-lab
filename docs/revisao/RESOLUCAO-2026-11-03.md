# Situação dos achados da revisão independente (03/11/2026)

A revisão (`REVISAO-INDEPENDENTE-2026-11.md`, PR #2) analisou o commit `62b49c3`. A tabela abaixo
mostra o estado de cada achado no `main` de 03/11/2026, conferido no código e no `STATUS.md`.
"Issue" quer dizer que o item fica aberto no GitHub depois da publicação, por decisão do dono:
os itens de severidade baixa não bloqueiam a abertura.

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
| M7 downloads sem checksum | parcial, issue | Node e Chrome/chromedriver com `sha256sum -c`; pip e npm ainda sem lock |
| M8 bind mounts no Linux | resolvido | `plab` cria `workspace/` e `evidencias/` antes de subir |
| M9 logs do TIR | resolvido | `tir.sh` procura o segredo antes de copiar e usa `evidencias/` por padrão |
| M10 includes da 2610 na 2510 | issue | volume de includes único |
| L1 sentinela dos `*-init` | issue | — |
| L2 rede `plab` sem label | issue | — |
| L3 `.env` executado como shell | issue | — |
| L4 falsos positivos do passo 4 | issue | — |
| L5 `compile.sh` com entradas atípicas | issue | rc do `iconv` ainda não é conferido |
| L6 `lab setup` e estados | issue | o código de saída ainda depende só do smoke |
| L7 temporários em `/tmp` | issue | — |
| L8 marcadores BEGIN/END | issue | `templates.sh` confere só o BEGIN |
| L9 endurecimento dos containers | issue | — |
| L10 CI | resolvido | referência ao plano corrigida; `persist-credentials: false` nos dois `checkout` |
| L11 documentação desatualizada | resolvido | READMEs de `hello` e `ui-smoke` atualizados |
| L12 terceiros e autoria | resolvido | `THIRD_PARTY_NOTICES.md` (Spec Kit, MIT). E-mail dos commits mantido: o dono já o usa em outros repositórios públicos e os PRs guardariam o commit original de qualquer forma |
