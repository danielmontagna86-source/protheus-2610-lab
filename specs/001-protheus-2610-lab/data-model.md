# Data Model: Protheus 2610 Lab

O lab não tem banco próprio; as "entidades" são configuração versionada (`.env.example`,
manifests) e estado de runtime (containers, `lab-home`). Este documento fixa campos e regras.

## Release

| Campo | Tipo | Regra |
|---|---|---|
| id | `2610` \| `2510` | único; nomeia diretório `stacks/<id>` e project `plab-<id>` |
| fonte_ativa | `principal` \| `reserva-oficial` \| `reserva-felipe` | default `principal` |
| imagens | mapa serviço → `repo:tag@sha256:…` | digest obrigatório (Princípio I) |
| portas | mapa serviço → porta host | faixa 26xxx/25xxx, sobrescrevível, única na máquina |
| ambiente_web | ex.: `P2610` | confirmado no spike |
| ambiente_compila | ex.: `P2610_COMPILA` / `P2510D` | confirmado no spike |
| usuario_admin | `Admin` | senha via `PLAB_<id>_ADMIN_PASSWORD` (nunca versionada) |
| versoes_medidas | AppServer, DBAccess, LIB, WebApp, License | preenchido com evidência do spike |
| consumo_medido | RAM (MiB), disco (GB) | medido no spike |

## Stack (runtime)

Estados por serviço: `ausente → criando → starting → healthy | unhealthy`.
Stack `pronta` ⇔ db, license, dbaccess, appserver = `healthy` e WebApp responde HTTP 200.

## FonteImagem

| Campo | Regra |
|---|---|
| repo, tag, digest | digest de 64 hex |
| verificado_em | data ISO |
| licenca | declarada ou "não declarada" |

## ProvedorIA

| Campo | Regra |
|---|---|
| id | `claude` \| `codex` \| `opencode` \| `gemini` |
| pacote_npm, versao | fixados no `.env.example` |
| modos_auth | subconjunto de {`conta`, `api_key`} confirmado na doc oficial |
| dir_skills | caminho confirmado na doc oficial |
| estado | `nao_configurado → configurado → testado_ok` \| `nao_testado(motivo)` \| `falhou(passo)` |

Regras: API key nunca vazia; gravada só em `~/.config/lab/secrets.env` (600); estado persistido
em `~/.config/lab/state.json` (sem segredo) para idempotência.

## SkillEmbarcada

| Campo | Regra |
|---|---|
| nome | `testes-protheus`, `compilar-advpls-lab`, `engpro`, `advpl-exemplos` |
| origem | `repo` (vendorizada) \| `git@<commit>` (clonada no setup) |
| licenca | MIT/Apache/GPL verificada antes de clonar |
| destinos | um por provedor configurado |

## Cenario

| Campo | Regra |
|---|---|
| id | `hello`, `tir-<rotina>` |
| rotina | rotina padrão confirmada no menu da release |
| releases_confirmadas | ⊆ {2610, 2510}, só com evidência |
| somente_leitura | sempre `true` (exceto compilação do hello no RPO) |

## Evidencia

Diretório `evidencias/<release>/<AAAAMMDD-HHMMSS>/` com `resumo.json` (passos, status, tempos,
versões), `compile.log`, `tir.log`, `*.png`. Sem senhas, tokens ou dados pessoais.
