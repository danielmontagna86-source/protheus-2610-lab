# Quickstart / roteiro de validação

Roteiro que prova a feature de ponta a ponta. Comandos detalhados nos contratos
([plab-cli](contracts/plab-cli.md), [lab-setup-cli](contracts/lab-setup-cli.md)).

## Pré-requisitos

- Docker Desktop (WSL2) rodando, ≥ 16 GB alocados ao Docker para as duas releases juntas
  (valor final medido no spike vai para o README), ~25 GB de disco livres.
- Git. PowerShell 5.1+ ou bash.

## Cenários de validação

| # | Passo | Resultado esperado | Cobre |
|---|---|---|---|
| V0 | Registrar estado de `protheus-teste` e `protheus_ia_lab` (`docker ps`) | baseline salvo | SC-008 |
| V1 | `copy .env.example .env`, preencher senhas admin, `plab up 2610` | 4 serviços healthy; `http://127.0.0.1:26321` responde | US1, SC-001 |
| V2 | Login no WebApp 2610 como Admin | menu abre; versões anotadas | US1 |
| V3 | `plab up 2510` com 2610 rodando | as duas healthy; `http://127.0.0.1:25321` abre 2510 | US2, SC-002 |
| V4 | `plab down 2510 --volumes`, `plab up 2510` | 2610 segue healthy durante todo o tempo | US2, SC-002 |
| V5 | `plab up lab`, `plab smoke 2610`, `plab smoke 2510` | PRONTO nas duas; evidências gravadas | US3, SC-003 |
| V6 | `plab setup` (Claude + Codex), depois de novo | mesmo estado final; IAs `testado_ok` ou `nao_testado(motivo)` | US4, SC-004, SC-007 |
| V7 | Pedir à IA "crie um teste TIR que abra MATA010 e confira o título" | usa skills embarcadas | US4 |
| V8 | Rodar cada cenário de `cenarios/tir-*` | ≥ 3 aprovados em ≥ 1 release | US5, SC-006 |
| V9 | `plab scan` | zero ocorrências | SC-005 |
| V10 | `docker ps` de novo | stacks pré-existentes inalteradas e healthy | SC-008 |
| V11 | Clone limpo + `down -v` + V1..V5 | repete resultado | gate final |
