# Protheus 2610 Lab Constitution

## Core Principles

### I. Padrão TOTVS Genérico, Sem Redistribuição

- O lab MUST trabalhar exclusivamente sobre o padrão TOTVS das releases 12.1.2610 e 12.1.2510.
- Skills, regras, exemplos, cenários e templates MUST NOT conter nada de empresa ou cliente:
  hosts, usuários, senhas, tabelas Z*, parâmetros customizados ou rotinas U_ de empresa.
- O repositório MUST NOT redistribuir binários ou fontes TOTVS (RPO, AppServer, advpls,
  includes, fontes padrão). Imagens externas MUST ser referenciadas por tag **e** digest.

Rationale: o repositório é público para a comunidade; licenças TOTVS e dados de terceiros
não podem vazar nem ser reempacotados.

### II. Segredos Fora de Tudo (NON-NEGOTIABLE)

- Segredos MUST NOT aparecer em argumento de linha de comando, log, camada de imagem,
  `.env` versionado ou commit.
- Chaves de API MUST ser lidas com `read -s` e gravadas apenas em
  `~/.config/lab/secrets.env` (modo 600) dentro do volume `lab-home`, carregadas só pelo
  wrapper da CLI que as usa.
- Antes de declarar qualquer fase concluída, MUST rodar varredura de segredo (`git grep`,
  `docker history`, `docker inspect`, logs de setup) com zero ocorrências.

Rationale: o lab será clonado por terceiros e roda CLIs de IA com credenciais pessoais.

### III. Evidência Antes de Afirmação

- Nada é "pronto", "ok" ou "funciona" sem verificação executada; a evidência (comando +
  saída resumida) MUST ser registrada em `STATUS.md`.
- Relatórios MUST separar fato verificado de hipótese.
- Onde faltar credencial ou recurso para testar, o status MUST ser "não testado", nunca "ok".

Rationale: validação estática, build, subida de container e smoke funcional provam coisas
diferentes; confundir os níveis gera falsa confiança.

### IV. Isolamento, Coexistência e Mínimo Privilégio

- As stacks 2610 e 2510 MUST ter project name, rede, volumes e portas próprios, com bind
  em `127.0.0.1`, e MUST poder rodar ao mesmo tempo.
- O lab MUST NOT alterar, parar ou reutilizar stacks já existentes na máquina do
  desenvolvedor (ex.: outra stack Protheus local), nem usar portas já ocupadas.
- Containers MUST NOT montar `docker.sock` nem usar `pid: host`. `privileged`, `cap_add` e
  `devices` só são permitidos com teste comprovando a necessidade, documentado no README.

Rationale: o lab entra em máquinas que já têm outros ambientes; ele não pode quebrá-los nem
ampliar a superfície de ataque sem motivo.

### V. AdvPL/TLPP Disciplinado

- Fontes `.prw`, `.prx`, `.tlpp`, `.ch` MUST estar em CP1252 com CRLF, conferidos por bytes
  após cada gravação.
- Todo símbolo AdvPL/TLPP (função, classe, método) MUST ser validado no TDN ou nas skills
  EngPro antes do uso; símbolo não encontrado não é usado e a lacuna é registrada.
- O resultado de compilação MUST ser lido por SUCCESS/WARN/ERROR/FATAL; um FATAL invalida o
  lote inteiro.

Rationale: encoding errado corrompe fontes silenciosamente e API inventada compila errado
ou falha só em runtime.

### VI. Reprodutibilidade e Retomada

- Todas as versões (imagens, pacotes npm/pip, TIR, Chrome/chromedriver, CLIs de IA) MUST
  estar fixadas no `.env.example`, sem segredo.
- `STATUS.md` MUST ser atualizado ao fim de cada tarefa (fase, concluído, evidências,
  pendências, bloqueios, AGUARDANDO_USUARIO) e lido primeiro ao retomar.
- Cada tarefa concluída MUST gerar um commit local com mensagem em português.
- Criar remoto, push, publicação em registry ou rede social MUST NOT ocorrer sem autorização
  explícita do dono do projeto.

Rationale: o trabalho dura dias e atravessa sessões; outra sessão precisa retomar do ponto
exato sem adivinhar.

## Restrições Técnicas

- Banco: PostgreSQL com base padrão restaurada. Oracle e SQL Server ficam fora do escopo.
- Plataforma de referência: Windows 11 + Docker Desktop (WSL2); imagens `linux/amd64`.
- A única imagem construída pelo projeto é a `lab` (Ubuntu 24.04, usuário não-root `lab`).
- O lab valida rotinas padrão, compilação e smoke TIR; ele não substitui homologação e
  MUST NOT ser apontado para produção ou dados reais.

## Fluxo de Trabalho e Gates

- Ordem de trabalho: spec → plan → tasks → implementação por tarefa → verificação.
- Bloqueio que dependa do dono (login em portal, licença, credencial, decisão de escopo)
  MUST ir para `STATUS.md` > AGUARDANDO_USUARIO com pergunta objetiva; o trabalho segue na
  próxima tarefa independente. Contornar autenticação é proibido.
- Script baixado da internet MUST ser lido antes de executado e ficar em pasta própria,
  separada dos scripts do projeto.
- Gate final: subida do zero (`down -v`, clone limpo, `.env.example`), smoke verde nas duas
  releases e varredura de segredo limpa.

## Governance

- Esta constituição prevalece sobre outras práticas do repositório.
- Emendas MUST ser registradas em `STATUS.md` (o quê, por quê, data) e aplicar bump
  semântico: MAJOR para remoção/redefinição de princípio, MINOR para princípio ou seção nova,
  PATCH para redação.
- Toda spec, plan e revisão MUST conferir conformidade com os princípios I–VI; desvio exige
  justificativa escrita na seção de complexidade do plano.
- Revisão independente, quando houver, não autoriza publicação.

**Version**: 1.0.1 | **Ratified**: 2026-11-02 | **Last Amended**: 2026-11-02
