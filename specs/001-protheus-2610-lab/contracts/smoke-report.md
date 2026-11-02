# Contract: saída do smoke

## Console

```text
[1/4] doctor 2610 ........ OK   (WebApp 200, login página ok)
[2/4] compile LABHELLO ... OK   (SUCCESS=1 WARN=0 ERROR=0 FATAL=0)
[3/4] tir leitura ........ OK   (1 teste, 0 falhas)
[4/4] limpeza ............ OK   (.ini temporário removido)
PRONTO 2610 — evidências: evidencias/2610/20261102-153000/
```

Falha: `FALHOU 2610 no passo <n>/<nome>: <motivo curto>` e código de saída 10 + n.

## `resumo.json`

```json
{
  "release": "2610",
  "inicio": "2026-11-02T15:30:00-03:00",
  "fim": "2026-11-02T15:33:10-03:00",
  "versoes": {"appserver": "…", "dbaccess": "…", "lib": "…", "webapp": "…"},
  "passos": [
    {"n": 1, "nome": "doctor", "status": "ok", "detalhe": "…"},
    {"n": 2, "nome": "compile", "status": "ok", "severidades": {"SUCCESS": 1, "WARN": 0, "ERROR": 0, "FATAL": 0}},
    {"n": 3, "nome": "tir", "status": "ok", "testes": 1, "falhas": 0},
    {"n": 4, "nome": "limpeza", "status": "ok"}
  ],
  "resultado": "PRONTO"
}
```

Proibido no arquivo: senha, token, conteúdo de `secrets.env`, dados pessoais.
