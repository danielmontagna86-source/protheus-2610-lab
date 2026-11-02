# Contract: `lab` (dentro do container)

```text
lab doctor <2610|2510>        # diagnóstico: DNS, portas, WebApp HTTP, login TIR opcional
lab setup [--release R] [--ia claude,codex,...] [--auth conta|api_key] [--with-exemplos]
lab smoke <2610|2510>         # doctor → compile hello → TIR leitura → PRONTO | FALHOU:<passo>
lab compile <release> <arquivo...>
lab tir <release> <suite.py>
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
7. Gera `config.json` do TIR em `~/.config/lab/tir/<release>/` com senha lida de env em runtime.
8. Roda `lab smoke <release>`.
9. Imprime resumo: IA × modo × estado; termina com PRONTO ou o passo que falhou.

## Idempotência

Estado em `~/.config/lab/state.json` (sem segredo). Reexecução: pula o que está `testado_ok`,
pergunta antes de trocar chave existente, nunca duplica linhas em `secrets.env`.
