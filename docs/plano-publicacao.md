# Plano de git e publicação — Protheus 2610 Lab

Atualizado em 03/11/2026. Cada passo marcado com **[dono]** precisa de autorização explícita do dono
antes de ser executado. Os demais o agente pode fazer quando o passo anterior estiver concluído.

## Estado em 03/11/2026

- Repositório `danielmontagna86-source/protheus-2610-lab`: **privado**. Branch local `publicacao`
  acompanha `origin/main`. Histórico limpo (varredura `plab scan`: zero ocorrências).
- Backup do histórico antigo, fora do repositório:
  `protheus-2610-lab-kit/backup-historico-main-local-2026-11-03.bundle`.
- PR #2 (revisão independente, branch `claude/funny-hawking-8byuzs`) aberto.
- Renovação da data de troca de senha do Admin na 2510: mantida (decisão do dono, 03/11/2026).
- LinkedIn: artigo, post com carrossel e primeiro comentário publicados em 03/11/2026 (links no
  `STATUS.md`, seção Divulgação). O CTA atual é "Comente LAB", porque o repositório ainda é privado.

## Andamento (03/11/2026, fim da tarde)

- Fase 1 concluída: revisão incorporada (`docs/revisao/`), PR #2 fechado, `plab scan` zero, smoke
  PRONTO nas duas releases, tag `v1.0.0` no remoto.
- Fase 2 preparada: descrição, tópicos, homepage, issues habilitadas, release `v1.0.0` e 12 issues
  (#3–#14). **Falta só tornar o repositório público**: o comando foi bloqueado pela política de
  segurança do agente, então o dono executa (Settings → Danger Zone → Change visibility, ou o
  comando do passo 5).
- Página `lp.protheusialab.com.br/lab/` montada no padrão do portal (tokens, `_shared/_nav.html`,
  `_shared/_footer.html` e `propagate.py`, agora com 11 itens) e validada em cópia do site
  (desktop 1440 px e celular 375 px, sem rolagem horizontal, imagens carregadas). Publicação no site
  fica para logo depois da abertura do repositório, porque os botões apontam para o GitHub.
- Fase 2 e 3 concluídas (03/11/2026, noite): repositório público pelo dono; página no ar; primeiro
  comentário e artigo do LinkedIn atualizados com os links; bundle de backup apagado. Detalhes no
  `STATUS.md`, seção Divulgação. Falta: métricas de 24 h e calendário da Fase 4.

## Fase 1 — Fechar o repositório privado (agente)

1. Commitar `STATUS.md` e este plano e enviar para `origin/main` (privado, já autorizado).
2. PR #2: incorporar os itens da revisão que ainda valem e fechar o PR com um resumo. **[dono]**
   decide se os itens de baixa severidade L1–L12 entram antes da abertura ou ficam como issues.
3. Conferência pré-publicação, com saída registrada no `STATUS.md`:
   - `plab scan` (histórico do git, imagem do lab, evidências e logs) com zero ocorrências;
   - `git ls-files` sem `.env`, `evidencias/<release>/`, chaves, bancos ou binários TOTVS;
   - `plab up 2610`, `plab up 2510`, `plab smoke` nas duas → PRONTO; `cenarios` 10/10;
   - README: requisitos, aviso de não vínculo com a TOTVS, imagens de comunidade só referenciadas,
     licença (`LICENSE`), link do issue totvs/tir#2169.
4. Criar a tag `v1.0.0` no commit conferido (local e no remoto privado).

## Fase 2 — Abrir o repositório **[dono]**

5. Autorização explícita do dono para tornar público. Só então:
   `gh repo edit danielmontagna86-source/protheus-2610-lab --visibility public --accept-visibility-change-consequences`.
6. Descrição, tópicos (`protheus`, `advpl`, `totvs`, `docker`, `tir`, `playwright`) e issues
   habilitadas. Conferir a página pública sem login.
7. Release `v1.0.0` com notas curtas (o que sobe, o que testa, limites).
8. Apagar o bundle de backup do histórico só depois de confirmar o repositório público. **[dono]**

## Fase 3 — LinkedIn depois da abertura

9. Editar o primeiro comentário do post: trocar "Comente LAB" pelo link do repositório. **[dono]**
   aprova o texto.
10. Responder a quem comentou "LAB" com o link (mensagens a terceiros: **[dono]** aprova o texto).
11. Editar o fim do artigo ("Próximos passos") com o link do repositório.

## Fase 4 — Calendário de conteúdo (cada peça passa por aprovação antes)

| Quando | Peça | Tese |
|---|---|---|
| 24 h após o post | registro de impressões e comentários | medir, sem inventar métricas |
| +3 a 4 dias | post curto | o issue do TIR no WebApp 26: sintoma, reprodução, contorno |
| +1 semana | post | stored procedure embarcada no RPO (FINA050, processo 08) |
| após abrir o repo | post de lançamento do repositório | como subir o lab em 3 comandos |
| +2 semanas | post | senha vencida e `$` no advpls: o que checar numa base nova |

## Ideia em avaliação: página do lab no lp.protheusialab.com.br

Página própria do lab (por exemplo `lp.protheusialab.com.br/lab`) linkada no perfil. Vantagens: um
link fixo para o CTA enquanto o repositório está privado (lista de espera) e, depois, a página de
entrada com o link do GitHub, o artigo e o e-book. Pendências antes de construir: saber onde o
`lp.protheusialab.com.br` é hospedado e como se publica nele, e se a página coleta e-mail (exige
política de privacidade e consentimento). **[dono]** decide escopo e publicação.
