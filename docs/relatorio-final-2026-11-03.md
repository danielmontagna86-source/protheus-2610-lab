# Relatório final — Protheus 2610 Lab (03/11/2026)

Relatório do gate final da constituição (T051–T053). Plataforma verificada: Windows 11 + Docker
Desktop (WSL2). Repositório privado; publicação pública depende de nova autorização do dono.

## Resultado por história

| História | Resultado | Evidência |
|---|---|---|
| US1 stack 2610 | ok | `plab up 2610` do zero em 74 s; doctor 8/8 |
| US2 stack 2510 | ok | `plab up 2510` do zero em 293 s (restore); duas releases juntas; isolamento 55/55 |
| US3 smoke | 2610 PRONTO; 2510 PRONTO com senha sem `$` | na base recém-criada a 2510 para na compilação (código 22) |
| US4 assistente de IA | ok | Claude Code e Codex `testado_ok` por login de conta; setup idempotente |
| US5 cenários de leitura | 10/10 | 5 cenários × 2 releases, todos saindo por "Log Off → Finalizar" |
| US6 opencode e Gemini | ok (Gemini) | Gemini `testado_ok` com chave de API; opencode fora desta versão por decisão do dono |

## Verificação do zero (T051)

Clone limpo, wrapper bash, `plab down --volumes` e `up` das duas releases; volume `lab-home`
preservado para manter o login das CLIs.

- `lab procedures 2610 08` → 1 instalado, 0 falhas; `plab restart 2610`.
- `plab smoke 2610` → PRONTO (doctor, interface, compilação `SUCCESS=1`, limpeza).
- `lab cenarios 2610` → 5/5; `lab cenarios 2510` → 5/5 (senha padrão da imagem).
- `plab smoke 2510` → para no passo 3 (código 22), comportamento documentado.
- `plab scan` no clone do GitHub → zero ocorrências, todos os itens verificados.

## Baseline (T052)

As 11 stacks que já existiam na máquina continuam saudáveis. O contêiner `protheus_ia_lab-api-1`
foi recriado às 04:00 de 03/11 (reinícios 0, sem OOM) por um `compose up` externo ao lab. Nenhum
comando do lab age sobre esse projeto.

## Achados que viraram correção

1. O TIR 2.14.12/2.14.13rc1 não conclui o Setup no WebApp 26 (totvs/tir#2169) → Playwright.
2. Senha do Admin da 2510 vencida pela política → renovação da data no `plab up` (só 2510).
3. Compilar na 2510 derruba o `/app-root` → interface antes da compilação e reinício no passo 5.
4. `advpls` trava com qualquer `$` na senha, mesmo escapado → falha cedo com código 22.
5. Licenças de desenvolvimento presas por sessões sem "Finalizar" → saída obrigatória.
6. Senha visível em captura de falha de login → conferência dos campos e limpeza antes da captura.
7. FINA050 na 2610 incompatível com a procedure da base → `lab procedures` (pacote do RPO).
8. Falsos OK do `plab scan` no Git Bash → item sem resposta vira "não verificado".

## Pendências

- opencode: fora desta versão (decisão do dono); provider fica no código sem login testado.
- Fonte reserva das imagens (FR-005): desvio registrado.
- Achados baixos da revisão independente (L1–L12).
- Publicação pública, divulgação no LinkedIn e marca no nome do projeto: decisão do dono.

author: daniel.montagna
