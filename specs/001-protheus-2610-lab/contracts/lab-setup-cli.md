# Contract: `lab` (dentro do container)

Emenda de 2026-11-02 (achado M5): ordem do smoke, `lab ui`, `lab cenarios` e config do TIR
alinhados à implementação.

```text
lab doctor <2610|2510>        # DNS, TCP, WebApp, /app-root, REST, License Server, DBAccess, secret (31–38)
lab setup [--release R] [--ia claude,codex,...] [--auth conta|api_key] [--with-exemplos]
          [--nao-interativo] [--sem-smoke]
lab smoke <2610|2510>         # doctor → interface (Playwright) → compile hello → limpeza → PRONTO | FALHOU
lab compile <release> <arquivo...>
lab ui <2610|2510>            # smoke de interface somente leitura (Playwright)
lab cenarios <2610|2510> [nome]  # cenários de leitura de cenarios/ui-leitura/cenarios.json
lab tir <release> <suite.py>  # suíte TIR com config temporária
lab versions
```

## `lab setup` — fluxo

1. `doctor` da release (default: a única release healthy; se duas, pergunta).
2. Menu de IAs (seleção múltipla). Para cada IA: modo `conta` (fluxo device-code/URL da CLI) ou
   `api_key` (`read -s`, não vazia, grava em `~/.config/lab/secrets.env` 600). O provider pode
   declarar `<ia>_modos` com os modos que a CLI documenta; modo fora da lista vira
   `nao_suportado(...)` (Gemini: só `api_key`).
3. Instala a CLI na versão fixada (prefixo npm em `lab-home`), cria wrapper em
   `~/.local/bin/<cli>` que carrega `secrets.env` só para aquele processo.
4. Teste trivial ("responda OK"); sem credencial → estado `nao_testado(motivo)`.
5. Publica skills no diretório de cada CLI (confirmado na doc oficial).
6. Gera `AGENTS.md`, `CLAUDE.md`, `GEMINI.md` em `/workspace` a partir de
   `templates/agent-rules.md.tmpl` (só cria/atualiza bloco delimitado
   `<!-- BEGIN plab -->…<!-- END plab -->`, preservando texto do usuário).
7. Não grava `config.json` do TIR: o `lab tir` gera uma config temporária por execução (diretório
   0700, arquivo 0600, apagado no fim) com a senha lida do secret, e entrega o caminho em
   `PLAB_TIR_CONFIG`. Mais seguro que um arquivo persistente.
8. Roda `lab smoke <release>`.
9. Imprime resumo: IA × modo × estado; termina com PRONTO ou o passo que falhou.

## Código de saída do `lab setup`

Emenda de 03/11/2026 (L6 da revisão independente): `0` quando nenhuma IA ficou em `falhou(...)` e o
smoke deu PRONTO (ou foi pulado com `--sem-smoke`); `1` quando o smoke falhou ou alguma IA ficou em
`falhou(...)`; `2` uso incorreto; `3` nenhuma release respondendo ou doctor falhou. `nao_testado(...)`
e `nao_suportado(...)` não reprovam. No `state.json` vai só a categoria (`falhou(instalacao)`,
`falhou(autenticacao)`, `falhou(teste)`); a saída da CLI no teste aparece só no terminal.

## Idempotência

Estado em `~/.config/lab/state.json` (sem segredo). Reexecução: pula o que está `testado_ok`,
pergunta antes de trocar chave existente, nunca duplica linhas em `secrets.env`.
