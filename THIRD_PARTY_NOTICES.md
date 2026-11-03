# Avisos de terceiros

A licença MIT do arquivo `LICENSE` cobre o código do Protheus 2610 Lab. Os itens abaixo vêm de
terceiros e mantêm as próprias licenças.

## GitHub Spec Kit

- Arquivos: `.specify/**` e `.claude/skills/speckit-*/**` (modelos, scripts e skills do fluxo
  spec → plano → tarefas).
- Origem: https://github.com/github/spec-kit
- Licença: MIT. Copyright GitHub, Inc.
  Texto completo: https://github.com/github/spec-kit/blob/main/LICENSE

## Referenciados, não incluídos

O repositório não inclui nenhum dos itens abaixo. Eles são baixados por quem usa o lab:

- Imagens Docker da comunidade (`emebatista/*`) e as imagens reserva. Contêm software da TOTVS.
  Baixá-las é decisão e responsabilidade de quem usa o lab.
- TIR (`totvs/tir`), compilador `advpls` (`@totvs/tds-ls`), Chrome for Testing, Playwright e as
  CLIs de IA. Cada um é instalado na versão fixada no `.env.example`, sob a licença do respectivo
  autor.
- Skills da Engenharia Protheus (`totvs/engpro-advpl-tlpp-skills`), clonadas por commit durante o
  `lab setup`.
