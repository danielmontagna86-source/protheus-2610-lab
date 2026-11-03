# Cenário ui-smoke (Playwright)

## Objetivo

Provar, somente leitura, que a release responde ao fluxo real de um usuário no WebApp: parâmetros
iniciais → login PO UI → empresa 99 / filial 01 / módulo Faturamento → menu
**Atualizações > Cadastros > Produtos** (MATA010) → browse **"Atualizacao de Produtos"** → sair.

## Por que Playwright

Em 02/11/2026 o TIR 2.14.12 não conclui o `Setup` nestes WebApps (WebApp 26.0.0 e SmartClient HTML
10.0.2): o campo de ambiente autocompleta e embaralha a digitação, e o clique no `wa-button` OK não
leva ao login. O Playwright 1.64.1 (mesmo Chrome 156 da imagem) atravessa o shadow DOM, espera
acionabilidade e encontra o iframe do login PO UI. O TIR continua sendo o gerador oficial das suítes
(skill EngPro `tir-test-generator`); este cenário cobre o que o TIR ainda não alcança.

## Pré-condição

Release de pé (`plab up 2610`/`2510`) e container lab de pé (`plab up lab`).

## Como rodar

```bash
plab smoke 2610            # passo 2 do smoke usa este cenário
# ou, dentro do container lab:
lab ui 2610
```

## Somente leitura

- O diálogo **Moedas** (cotações do dia) é fechado com **Cancelar**; **Confirmar** gravaria cotações.
- Nenhuma inclusão, alteração ou exclusão; nenhuma captura mostra senha (a captura do login é feita
  antes do preenchimento ou depois da entrada).

## Evidência esperada

`01-menu.png`, `02-rotina.png` (ou `falha.png`) e a saída `[ui] OK: aba 'Produtos' aberta com titulo
'Atualizacao de Produtos'`.

## Releases confirmadas

- 2610: confirmada em 02/11/2026 (capturas em `evidencias/diag/pw-2610-p8`)
- 2510: confirmada em 03/11/2026 (`plab smoke 2510` PRONTO, registrado no `STATUS.md`)

author: daniel.montagna
