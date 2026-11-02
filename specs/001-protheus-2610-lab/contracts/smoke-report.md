# Contract: saída do smoke

Emenda de 2026-11-02 (achado M5 da revisão independente): ordem e campos alinhados à
implementação em `lab/bin/lib/smoke.sh`. Motivos registrados em STATUS.md.

## Console

```text
[1/4] doctor             OK   (WebApp, /app-root, REST, License Server, DBAccess e secret ok)
[2/4] interface          OK   (OK: aba 'Produtos' aberta com titulo 'Atualizacao de Produtos')
[3/4] compile            OK   (SUCCESS=1 WARN=0 ERROR=0 FATAL=0)
[4/4] limpeza            OK   (sem temporarios; nenhuma senha nas evidencias)
PRONTO 2610 — evidencias: /opt/plab/evidencias/2610/20261102-153000
```

- A interface (Playwright, somente leitura) roda **antes** da compilação: na 2510 compilar derruba
  o `/app-root` até o AppServer reiniciar.
- A suíte TIR (`cenarios/tir-smoke`) só roda com `PLAB_SMOKE_TIR=1`, como passo **informativo**
  que não bloqueia o PRONTO, enquanto o TIR 2.14.x não concluir o Setup no WebApp 26
  (totvs/tir#2169). Desvio da US3/FR-015 registrado em STATUS.md.
- Falha: `FALHOU <rel> no passo <n>/<nome>: <motivo curto>` e código de saída 10 + n
  (11 doctor, 12 interface, 13 compile, 14 limpeza).
- No host, `plab smoke <rel>` acrescenta o passo `[5/5] recuperacao` (reinício do AppServer) nas
  releases de `PLAB_REINICIAR_APOS_COMPILAR`; falha nele sai com código 15.

## `resumo.json`

```json
{
  "release": "2610",
  "inicio": "2026-11-02T15:30:00-03:00",
  "fim": "2026-11-02T15:33:10-03:00",
  "passos": [
    {"n": 1, "nome": "doctor", "status": "ok", "detalhe": "…"},
    {"n": 2, "nome": "interface", "status": "ok", "detalhe": "…"},
    {"n": 3, "nome": "compile", "status": "ok", "detalhe": "SUCCESS=1 WARN=0 ERROR=0 FATAL=0"},
    {"n": 4, "nome": "limpeza", "status": "ok", "detalhe": "…"}
  ],
  "resultado": "PRONTO"
}
```

Versões ficam em `lab versions`, não no resumo. Proibido no arquivo: senha, token, conteúdo de
`secrets.env`, dados pessoais.
