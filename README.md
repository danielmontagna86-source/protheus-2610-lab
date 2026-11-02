# Protheus 2610 Lab

Ambiente local de desenvolvimento sobre o **padrão TOTVS**, com duas releases lado a lado:
**Protheus 12.1.2610** e **12.1.2510**. Cada uma tem PostgreSQL com a base padrão já restaurada,
License Server, DBAccess e AppServer (WebApp + REST). Um container de ferramentas (`lab`) traz TIR,
Playwright, Chrome headless, `advpls` (compilação AdvPL/TLPP) e as CLIs de IA.

> O lab **não substitui homologação** e **não deve ser apontado para produção nem para dados reais**.
> Ele valida rotinas padrão, compilação e testes de interface somente leitura.

## Status verificado (02/11/2026)

| Item | 2610 | 2510 |
|---|---|---|
| Stack sobe e fica healthy | ok (32 s com imagens em cache) | ok (283 s na 1ª subida: restore da base) |
| Login WebApp (Admin) → menu | ok | ok (com renovação automática da senha, ver abaixo) |
| Duas releases ao mesmo tempo / recriar uma sem afetar a outra | ok (55/55 checagens da 2610 durante `down -v` + `up` da 2510) | ok |
| Compilação `LABHELLO.prw` | ok (`SUCCESS=1`) | **bloqueada**: senha padrão com `$` trava o `advpls cli` (ver Problemas conhecidos) |
| Smoke de interface (Playwright): login → Faturamento → MATA010 → título | ok | ok |
| Suíte TIR 2.14.12 | **bloqueada** (ver Problemas conhecidos) | **bloqueada** |

Detalhes e evidências: [`STATUS.md`](STATUS.md).

## Pré-requisitos

- Docker Desktop (WSL2) ou Docker Engine com Compose v2, imagens `linux/amd64`.
- Disco: ~16 GB de imagens da 2610, ~6 GB da 2510, ~3 GB da imagem `lab`, mais volumes (~3 GB por release).
- RAM medida em repouso: ~1,0 GB por release (AppServer ~700 MB). Reserve 8 GB para as duas releases + lab.
- PowerShell 5.1+ (Windows) ou bash (Linux/WSL/macOS).

## Passo a passo

```powershell
copy .env.example .env      # preencha PLAB_2610_ADMIN_PASSWORD e PLAB_2510_ADMIN_PASSWORD
.\plab.ps1 up 2610           # ou: ./plab up 2610
.\plab.ps1 up 2510
.\plab.ps1 up lab
.\plab.ps1 smoke 2610
```

As senhas padrão do usuário `Admin` são as documentadas publicamente pela fonte das imagens
(README de `emebatista/docker-protheus-2610` e `-2510`). Elas ficam **só** no seu `.env`. Atenção:
cada `$` da senha deve ser escrito como `$$` no `.env` (regra do Docker Compose).

### Endereços (somente 127.0.0.1)

| | 2610 | 2510 |
|---|---|---|
| WebApp | http://127.0.0.1:26234/webapp/ | http://127.0.0.1:25234/webapp/ |
| TCP / TDS / SmartClient | 127.0.0.1:26234 | 127.0.0.1:25234 |
| REST | http://127.0.0.1:26181/rest/ | http://127.0.0.1:25181/rest/ |
| PostgreSQL | 127.0.0.1:26432 | 127.0.0.1:25432 |
| Monitor de licenças | http://127.0.0.1:26020/ | http://127.0.0.1:25020/ |

Use o WebApp pela **porta multiprotocolo** (`.../webapp/`): no WebApp 26 a tela de login nova
(`/app-root`) só é servida nela. Todas as portas são configuráveis no `.env`.

### Comandos

| Host | Dentro do container lab | O que faz |
|---|---|---|
| `plab up/down/status/logs <alvo>` | — | gerencia `2610`, `2510`, `lab` ou `all` |
| `plab smoke <rel>` | `lab smoke <rel>` | doctor → compila LABHELLO → interface somente leitura → PRONTO |
| — | `lab doctor <rel>` | DNS, porta, WebApp, `/app-root`, REST, senha |
| — | `lab compile <rel> <fontes>` | compila no ambiente de compilação (P2610_COMPILA / P2510D) |
| — | `lab ui <rel>` | smoke de interface com Playwright |
| — | `lab tir <rel> <suite.py>` | executa suíte TIR com config temporária |
| — | `lab versions` | versões instaladas |
| — | `lab setup [--ia ...] [--auth conta\|api_key]` | configura CLIs de IA, publica skills e gera AGENTS/CLAUDE/GEMINI.md |

### IAs do `lab setup`

Versões fixadas no `.env.example`. Chaves de API são lidas sem eco e ficam só em
`~/.config/lab/secrets.env` (600, volume `lab-home`); o wrapper de cada CLI carrega apenas a sua.
Fontes oficiais e datas em `specs/001-protheus-2610-lab/research.md` (R-07).

| IA | Pacote npm | Login de conta (`conta`) | Chave (`api_key`) | Skills | Status |
|---|---|---|---|---|---|
| Claude Code | `@anthropic-ai/claude-code` | `claude auth login` (URL + código colado) | `ANTHROPIC_API_KEY` | `~/.claude/skills` | conta testada (login real do dono) |
| Codex | `@openai/codex` | `codex login --device-auth` | `OPENAI_API_KEY` via stdin do `codex login --with-api-key` | `~/.codex/skills` | conta testada (login real do dono) |
| opencode | `opencode-ai` | `opencode auth login` (escolha o provedor; no container prefira código de dispositivo, ex.: GitHub Copilot) | `OPENCODE_API_KEY` ou `ANTHROPIC_API_KEY` | `~/.config/opencode/skills` | não testado |
| Gemini CLI | `@google/gemini-cli` | **não suportado** (a doc só descreve login com navegador local) | `GEMINI_API_KEY` | `~/.gemini/skills` | não testado |

## Fontes das imagens

| Release | Principal (usada) | Reserva |
|---|---|---|
| 12.1.2610 | `emebatista/*-2610:1.0.0` (digest no `.env.example`) | `feliperaposo/protheus:p12.1.2610` |
| 12.1.2510 | `emebatista/*-2510:1.0.0` | oficial TOTVS `totvsengpro/*` (postgres-dev 12.1.2510_bra) |

Não existe imagem oficial TOTVS da 2610 (Docker Hub verificado em 02/11/2026). As imagens de
comunidade não declaram licença; o lab só as referencia por digest e não as redistribui.
Componentes das imagens originais **não usados**: DeskFlow (monta `docker.sock`, `pid: host`),
SmartView e container exclusivo. Nenhum serviço do lab usa `privileged`.

## Decisões técnicas verificadas

- **Sem privilégios extras.** Login e menu funcionam sem `/dev/mem`; o log `Can't read memory
  from /dev/mem` é só ruído. Se o License Server recusar licenças, há o override opcional
  `stacks/override/devmem.yaml`.
- **Senha do Admin da 2510.** A base foi publicada com a última troca em 12/10/2025. Passado o
  prazo da política, o login exige troca obrigatória. O `plab up` aplica
  `stacks/sql/renova-senha-admin.sql`, que atualiza só a **data** da última troca, nunca a senha,
  nas duas releases.
- **RPO de compilação da 2610.** O AppServer Linux usa caminhos em minúsculas, e a imagem traz
  `P2610_COMPILA/APO0002`. O serviço `rpo-init` semeia o volume em `p2610_compila/apo0002`.
- **Includes.** Os `.ch` da TOTVS não vêm no repositório. O serviço `includes-init` copia os 158
  includes da imagem AppServer 2610 que você baixou, com nomes também em maiúsculas.
- **Playwright complementa o TIR.** Ele usa o mesmo Chrome 156 da imagem, sem baixar outro navegador.

## Problemas conhecidos

1. **TIR 2.14.12 x WebApp 26.0.0 / SmartClient HTML 10.0.2.**
   - O campo de ambiente autocompleta e a digitação do TIR vira `P261P2610`. A extensão local
     `lab/tir/plab_tir_compat.py` corrige esse ponto.
   - Depois disso, o clique no OK não leva ao login. Até o TIR corrigir, o smoke usa Playwright
     (`cenarios/ui-smoke`). A suíte TIR continua em `cenarios/tir-smoke` e roda com `PLAB_SMOKE_TIR=1`.
2. **`advpls cli` trava com `$` na senha** (TDS-LS 2.2.7). O `lab compile` falha cedo, com código 22.
   Para compilar na 2510, troque a senha do Admin **do lab** por uma sem `$`, pelo WebApp, e
   atualize o `.env`.
3. **Diálogo "Moedas".** No primeiro acesso do dia a cadastros, "Confirmar" grava cotações. Os
   testes de leitura usam "Cancelar".

## Solução de problemas

| Sintoma | Causa provável | O que fazer |
|---|---|---|
| `plab up` sai com código 4 | porta ocupada | `plab ports`; troque a porta no `.env` |
| WebApp mostra `json_context.cpp:963, 404` | acesso pela porta 4321 | use `http://127.0.0.1:<PORT_TCP>/webapp/` |
| Login pede "Alterar senha" | prazo da política vencido | `plab up <rel>` renova a data |
| `lab compile` código 21 | RPO em uso (COMPILEERROR-300) | feche as sessões do ambiente de compilação |
| `lab compile` código 22 | senha com `$` | ver Problemas conhecidos, item 2 |
| `lab compile` com `C2090 File not found PRTOPDEF.CH` | volume de includes vazio | `plab up lab` (o `includes-init` semeia) |

## Licenças e responsabilidades

- Código do lab: MIT ([LICENSE](LICENSE)).
- Protheus, AppServer, DBAccess, License Server, RPO, includes, TIR e advpls pertencem à TOTVS.
  Licenças e direito de uso são de quem instala. O License Server de desenvolvimento das imagens
  não comprova direito de uso.
- Imagens de comunidade: responsabilidade de seus autores.
- CLIs de IA: credenciais, planos e termos são de quem configura.

## O que o lab não cobre

Oracle, SQL Server, dados reais, produção, homologação, SmartView, carga/performance.
