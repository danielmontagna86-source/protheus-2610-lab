# Cenário hello — `LABHELLO.prw`

## Objetivo

Provar que o lab compila um fonte AdvPL no RPO do ambiente de compilação de cada release e que o
fonte compilado está disponível para execução.

## Pré-condição

- Release alvo de pé (`plab up 2610` ou `plab up 2510`) e container lab de pé (`plab up lab`).
- Nenhuma sessão aberta no ambiente de compilação durante a compilação (erro COMPILEERROR-300 =
  RPO em uso).

## Como rodar

```bash
plab smoke 2610   # ou 2510; dentro do container: lab compile 2610 cenarios/hello/LABHELLO.prw
```

## Evidência esperada

- `compile.log` com `SUCCESS` para `LABHELLO.prw` e zero `ERROR`/`FATAL`.
- `resumo.json` do smoke com o passo `compile` em `ok`.

## Fonte

- Encoding **CP1252** e quebra de linha **CRLF** (conferidos por `lab/tests/test_encoding.sh`).
- Sem `#include`: os includes do Protheus são da TOTVS e não são redistribuídos.
- Símbolos validados no TDN em 02/11/2026:
  [ConOut](https://tdn.totvs.com/display/tec/ConOut),
  [DToS](https://tdn.totvs.com/display/tec/DToS),
  [Date](https://tdn.totvs.com/display/tec/Date),
  [Time](https://tdn.totvs.com/display/tec/Time);
  `User Function` / `Return` conforme o exemplo oficial da página ConOut.

## Releases confirmadas

- 2610: `SUCCESS=1` (registrado no `STATUS.md`, T023–T025)
- 2510: `SUCCESS=1` (registrado no `STATUS.md`, T023–T025)
