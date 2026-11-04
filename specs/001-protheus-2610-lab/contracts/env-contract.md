# Contract: `.env.example`

Versionado, **sem nenhum valor secreto**. O usuário copia para `.env` (ignorado pelo git).

| Grupo | Variáveis (exemplos) |
|---|---|
| Imagens 2610 | `PLAB_2610_IMG_DB`, `PLAB_2610_IMG_LICENSE`, `PLAB_2610_IMG_DBACCESS`, `PLAB_2610_IMG_APPSERVER` = `repo:tag@sha256:<64hex>` |
| Imagens 2510 | `PLAB_2510_IMG_*` idem |
| Portas 2610 | `PLAB_2610_PORT_TCP=26234`, `_WEBAPP=26321`, `_REST=26181`, `_DB=26432`, `_LICMON=26020` |
| Portas 2510 | `PLAB_2510_PORT_*` = 25234, 25321, 25181, 25432, 25020 |
| Ambientes | `PLAB_2610_ENV=P2610`, `PLAB_2610_ENV_COMPILA=…`, `PLAB_2510_ENV=P2510`, `PLAB_2510_ENV_COMPILA=…` |
| Senhas (só nomes) | `PLAB_2610_ADMIN_PASSWORD=` e `PLAB_2510_ADMIN_PASSWORD=` vazios no exemplo; README explica onde obter a senha padrão pública |
| Containers | `PLAB_RESTART=unless-stopped` (ou `no`), `PLAB_MEM_*` |
| Lab | `PLAB_UBUNTU=24.04`, `PLAB_NODE=22`, `PLAB_TIR=2.14.12`, `PLAB_CHROME=156.0.8078.80`, `PLAB_TDS_LS=2.2.7` |
| IAs | `PLAB_CLAUDE_CODE=2.1.316`, `PLAB_CODEX=0.166.0`, `PLAB_OPENCODE=1.19.5`, `PLAB_GEMINI_CLI=0.66.0` |
| Terceiros | `PLAB_ENGPRO_COMMIT=<sha>`, `PLAB_EXEMPLOS_COMMIT=<sha>` |

Regra de verificação: `plab scan` falha se `.env.example` tiver valor em qualquer variável
terminada em `_PASSWORD`, `_TOKEN`, `_KEY` ou `_SECRET`.
