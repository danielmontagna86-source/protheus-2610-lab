# Feature Specification: Protheus 2610 Lab (releases 12.1.2610 e 12.1.2510)

**Feature Branch**: `001-protheus-2610-lab`

**Created**: 2026-11-02

**Status**: Draft

**Input**: User description: "Protheus 2610 Lab: ambiente local reproduzível de desenvolvimento
Protheus sobre o PADRÃO TOTVS, com DUAS releases lado a lado — 12.1.2610 e 12.1.2510 — cada uma
com Postgres com base padrão já restaurada, License Server, DBAccess e AppServer (WebApp + REST),
subindo com docker compose e podendo rodar simultaneamente sem conflitar entre si nem com stacks
já existentes na máquina. Junto, uma imagem 'lab' (...) com um assistente `lab setup` que
diagnostica a stack escolhida, configura uma ou mais IAs (Claude Code e Codex no MVP; opencode e
Gemini depois) por login de conta ou API key, publica skills embarcadas e gera
AGENTS.md/CLAUDE.md/GEMINI.md de template único; gera config do TIR e roda um smoke (compila
LABHELLO.prw e executa suíte TIR somente leitura), terminando com PRONTO ou o passo que falhou.
Cenários: hello + 3 a 5 suítes TIR somente leitura em rotinas padrão. Fontes de imagem:
principal = comunidade emebatista/* para ambas as releases, sem DeskFlow e sem SmartView;
reservas = oficial TOTVS totvsengpro/* para 2510 e feliperaposo/protheus:p12.1.2610 para 2610.
Não precisa ser oficial. Público: comunidade Protheus. O agente executa tudo nesta máquina;
entregável FUNCIONAL e comprovado com evidência." (texto integral na sessão de 2026-11-02)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Subir o Protheus 12.1.2610 padrão e entrar no WebApp (Priority: P1)

Um desenvolvedor Protheus clona o repositório, copia o arquivo de exemplo de configuração, sobe a
stack da release 2610 com um único comando e, poucos minutos depois, abre o WebApp no navegador,
faz login com o usuário administrador do ambiente padrão e chega ao menu do Protheus. Não há
restore manual de banco nem assistente de criação de empresa: a base padrão já vem pronta.

**Why this priority**: sem um Protheus 2610 de pé e acessível, nada mais do lab tem valor. É a
fatia mínima que já serve à comunidade (ambiente de estudo/validação da release nova).

**Independent Test**: em uma máquina com só Docker, executar o comando de subida da stack 2610,
aguardar todos os serviços ficarem saudáveis, abrir o endereço do WebApp, autenticar e registrar
versões (AppServer, DBAccess, LIB, release) exibidas pelo sistema.

**Acceptance Scenarios**:

1. **Given** a máquina com Docker e nenhuma stack do lab, **When** o usuário sobe a stack 2610,
   **Then** banco, License Server, DBAccess e AppServer ficam saudáveis e o WebApp responde no
   endereço local documentado.
2. **Given** a stack 2610 saudável, **When** o usuário faz login com o administrador padrão,
   **Then** o menu do Protheus abre e as versões exibidas correspondem às registradas no README.
3. **Given** a máquina já tem outro ambiente Protheus rodando em portas comuns (ex.: 1234),
   **When** o usuário sobe a stack 2610, **Then** a subida não conflita nem altera o ambiente
   existente.

---

### User Story 2 - Ter a 12.1.2510 lado a lado com a 2610 (Priority: P1)

O mesmo desenvolvedor sobe também a stack da release 2510, em paralelo à 2610, para comparar
comportamento entre releases. Cada release tem endereço próprio, dados próprios e pode ser
ligada, desligada ou recriada sem afetar a outra.

**Why this priority**: o dono do projeto pediu explicitamente as duas releases; comparar 2510 vs.
2610 é o caso de uso que diferencia o lab de stacks existentes que sobem uma por vez.

**Independent Test**: com a 2610 rodando, subir a 2510, fazer login nas duas ao mesmo tempo,
derrubar e recriar só a 2510 e confirmar que a 2610 seguiu disponível e com seus dados.

**Acceptance Scenarios**:

1. **Given** a stack 2610 rodando, **When** o usuário sobe a 2510, **Then** as duas ficam
   saudáveis simultaneamente e cada WebApp abre a release correta.
2. **Given** as duas stacks rodando, **When** o usuário remove a 2510 com seus dados, **Then** a
   2610 continua respondendo e seus dados permanecem intactos.
3. **Given** a fonte principal de imagens de uma release ficar indisponível, **When** o usuário
   seleciona a fonte reserva documentada, **Then** a release sobe pelo mesmo comando, com o
   README indicando as diferenças da fonte reserva.

---

### User Story 3 - Smoke de desenvolvimento: compilar e testar pela interface (Priority: P2)

A partir do container de ferramentas do lab, o desenvolvedor escolhe a release alvo e roda o
smoke: compila um fonte de exemplo no RPO da release e executa uma suíte automatizada de
interface, somente leitura, que entra no WebApp, abre uma rotina padrão, confere o título e
sai. O resultado final é "PRONTO" ou o nome do passo que falhou, com evidência salva.

**Why this priority**: prova que o lab serve para desenvolver e validar, não só para "ver o
Protheus". Depende das stories 1 e 2, mas não depende de IA configurada.

**Independent Test**: com uma release saudável, executar o smoke contra ela e conferir: fonte
compilado com SUCCESS, suíte de interface aprovada, evidências (log e captura de tela) gravadas.

**Acceptance Scenarios**:

1. **Given** a release 2610 saudável, **When** o usuário roda o smoke para 2610, **Then** a
   compilação termina com SUCCESS, a suíte de interface passa e o comando imprime PRONTO.
2. **Given** a release 2510 saudável, **When** o usuário roda o smoke para 2510, **Then** o mesmo
   resultado é obtido contra a 2510.
3. **Given** a release alvo parada, **When** o usuário roda o smoke, **Then** o comando falha
   cedo, nomeando o serviço indisponível, sem tentar compilar.
4. **Given** uma sessão de interface aberta mantendo o RPO em uso, **When** a compilação é
   disparada, **Then** o smoke encerra a sessão antes de compilar ou reporta o conflito com
   orientação clara, nunca registrando falso SUCCESS.

---

### User Story 4 - Assistente `lab setup` com IA (Claude Code e Codex) (Priority: P3)

O desenvolvedor roda o assistente, que primeiro diagnostica a release escolhida, depois pergunta
quais IAs usar (uma ou mais) e, para cada uma, se autentica por login da conta ou por chave de
API. O assistente deixa a CLI instalada na versão fixada, faz um teste trivial ("responda OK"),
publica as skills embarcadas onde cada IA as lê e gera os arquivos de instruções do workspace a
partir de um template único.

**Why this priority**: é o diferencial "desenvolver com IA sobre o padrão", mas o lab já tem
valor sem ele (stories 1–3). MVP só com Claude Code e Codex.

**Independent Test**: rodar o assistente escolhendo Claude Code e Codex; conferir CLIs
respondendo, skills publicadas, arquivos de instruções gerados e nenhuma credencial fora do
arquivo de segredos protegido. Rodar de novo e conferir que nada duplica ou quebra.

**Acceptance Scenarios**:

1. **Given** o container de ferramentas rodando, **When** o usuário escolhe uma IA com chave de
   API, **Then** a chave é lida sem eco, gravada apenas no arquivo de segredos com permissão
   restrita e a CLI responde ao teste trivial.
2. **Given** o usuário escolhe login por conta, **When** a CLI oferece fluxo por código/URL
   copiável, **Then** o assistente o apresenta; **When** não oferece, **Then** o assistente
   oferece chave de API e explica o motivo.
3. **Given** o assistente já foi executado, **When** é executado de novo, **Then** ele detecta o
   que já está configurado, não duplica arquivos nem segredos e termina no mesmo estado.
4. **Given** a IA configurada, **When** o usuário pede "crie um teste de interface que abra a
   rotina X e confira o título", **Then** a IA usa as skills embarcadas e as regras do workspace.

---

### User Story 5 - Cenários de teste de leitura em rotinas padrão (Priority: P4)

O desenvolvedor encontra, no repositório, de 3 a 5 cenários prontos de interface somente
leitura sobre rotinas padrão (cadastros e financeiro), cada um com README explicando objetivo,
pré-condição, como rodar e evidência esperada, válidos nas duas releases ou marcados com a
release em que foram confirmados.

**Why this priority**: acelera o uso real e serve de exemplo para a IA, mas é incremental.

**Independent Test**: rodar cada cenário contra cada release e conferir aprovação e evidência.

**Acceptance Scenarios**:

1. **Given** uma release saudável, **When** o usuário roda um cenário, **Then** ele passa sem
   gravar nada na base e salva a evidência descrita no README.
2. **Given** uma rotina que não existe ou tem outro menu em uma release, **When** o cenário é
   preparado, **Then** o README registra a release confirmada e o cenário não é marcado como
   válido para a outra.

---

### User Story 6 - opencode e Gemini CLI (Priority: P5)

O assistente passa a oferecer também opencode (multi-provedor) e Gemini CLI, com o mesmo
contrato de autenticação, publicação de skills e geração de instruções.

**Why this priority**: amplia o público, mas só depois do MVP fechado com Claude e Codex.

**Independent Test**: repetir os testes da story 4 para opencode e Gemini.

**Acceptance Scenarios**:

1. **Given** o MVP concluído, **When** o usuário escolhe opencode ou Gemini, **Then** o
   assistente cumpre os mesmos critérios da story 4, ou marca o item como "não testado" quando
   faltar credencial para verificar.

---

### Edge Cases

- Porta local já ocupada por outro ambiente: a subida falha com mensagem que indica a porta e
  como trocá-la por configuração, sem derrubar o ambiente existente.
- License Server sem licença válida ou no limite de conexões do modo desenvolvimento: o
  diagnóstico identifica o License Server como causa, em vez de reportar falha genérica.
- Fluxo de login do WebApp diferente do esperado pela automação de interface (ex.: tela de
  login PO UI): o smoke reporta "bloqueado no login" com captura de tela e não marca aprovado.
- Primeira subida lenta (cópia do banco para o volume, inicialização do AppServer): o comando de
  subida aguarda a saúde dos serviços até um limite documentado antes de declarar falha.
- Imagem externa removida ou com digest diferente do fixado: a subida recusa a imagem divergente
  e orienta a fonte reserva.
- Plataforma sem acesso a dispositivos de hardware exigidos por alguma imagem (ex.: leitura de
  memória física no WSL2): o lab funciona sem privilégios extras ou documenta exatamente qual
  privilégio é necessário e por quê.
- Usuário aperta Enter sem informar a chave de API: o assistente não grava segredo vazio e
  oferece repetir ou pular a IA.
- Execução do smoke com as duas releases rodando e memória insuficiente: o diagnóstico mostra o
  consumo e recomenda parar uma das releases.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O lab MUST disponibilizar uma stack por release (12.1.2610 e 12.1.2510), cada uma
  composta por banco com base padrão restaurada, License Server, DBAccess e AppServer com WebApp
  e REST.
- **FR-002**: Cada stack MUST subir e parar com um único comando documentado, sem passos manuais
  de restore de banco ou criação de empresa.
- **FR-003**: As duas stacks MUST poder rodar simultaneamente, com nomes, dados, rede e portas
  próprios, publicadas somente no endereço local da máquina.
- **FR-004**: Nenhuma stack do lab MUST usar portas, volumes, redes ou nomes de container de
  ambientes já existentes na máquina; as portas MUST ser configuráveis sem editar o arquivo
  principal da stack.
- **FR-005**: Todas as imagens externas MUST ser referenciadas por versão e identificador
  imutável (digest), com a fonte principal e a fonte reserva de cada release documentadas.
- **FR-006**: O lab MUST NOT incluir componentes de gestão que exijam controle do motor de
  containers do host ou privilégios amplos; privilégios específicos só podem ser usados se o
  teste provar a necessidade, com justificativa no README.
- **FR-007**: O lab MUST fornecer um único container de ferramentas, construído pelo próprio
  projeto, com automação de interface (TIR) fixada, navegador headless compatível, compilador
  AdvPL/TLPP por linha de comando, git e o ambiente das CLIs de IA, rodando como usuário não
  administrador.
- **FR-008**: O assistente MUST diagnosticar a release escolhida (serviços, portas, WebApp,
  login) e reportar com clareza o primeiro item que falhou.
- **FR-009**: O assistente MUST permitir escolher uma ou mais IAs e, para cada uma, autenticação
  por conta (fluxo por código/URL copiável quando a CLI oferecer) ou por chave de API.
- **FR-010**: Chaves de API MUST ser lidas sem eco e gravadas somente no arquivo de segredos do
  usuário com permissão restrita, carregadas apenas pelo wrapper da CLI correspondente; nunca em
  argumento, log, imagem, configuração versionada ou commit.
- **FR-011**: O assistente MUST instalar cada CLI na versão fixada e validar com um teste
  trivial, reportando "não testado" quando não houver credencial para executar o teste.
- **FR-012**: O assistente MUST publicar as skills embarcadas nos locais que cada CLI lê,
  conforme a documentação oficial de cada CLI, e gerar AGENTS.md, CLAUDE.md e GEMINI.md no
  workspace a partir de um template único com regras genéricas (CP1252, padrão TOTVS, validar
  símbolo no TDN, WebApp, nunca produção).
- **FR-013**: O assistente MUST ser idempotente: reexecuções não duplicam arquivos, entradas ou
  segredos e preservam escolhas anteriores salvo pedido explícito de reconfiguração.
- **FR-014**: O assistente MUST gerar a configuração da automação de interface apontando para o
  WebApp da release escolhida, com a senha obtida de variável de ambiente, nunca gravada em
  arquivo versionado.
- **FR-015**: O smoke MUST compilar o fonte de exemplo (CP1252, CRLF) no ambiente da release,
  interpretar o resultado por SUCCESS/WARN/ERROR/FATAL (um FATAL invalida o lote), apagar
  arquivos temporários com credenciais ao fim e executar a suíte de interface somente leitura.
- **FR-016**: O smoke MUST terminar com "PRONTO" ou com o nome do passo que falhou e MUST salvar
  evidências (log de compilação, resultado da suíte, captura de tela final).
- **FR-017**: O repositório MUST conter a skill pública de testes Protheus copiada dos insumos do
  kit, validada pelo seu validador e pela sua suíte de testes.
- **FR-018**: O repositório MUST conter uma skill nova de compilação dentro do container (CLI do
  compilador + configuração temporária, senha só por variável de ambiente, leitura de
  severidades, tratamento do erro de RPO em uso).
- **FR-019**: Skills de terceiros (EngPro, exemplos validados) MUST ser obtidas no setup por
  commit fixado, apenas se a licença permitir, sem serem copiadas para o repositório.
- **FR-020**: O repositório MUST conter o cenário "hello" e de 3 a 5 cenários de interface
  somente leitura em rotinas padrão, confirmadas no ambiente antes de escritas, cada um com
  README (objetivo, pré-condição, como rodar, evidência esperada, releases confirmadas).
- **FR-021**: O README MUST cobrir pré-requisitos com RAM e disco medidos por release, passo a
  passo, solução de problemas, avisos de licença (TOTVS, imagens de comunidade, IAs) e o que o
  lab não cobre (Oracle, dados reais, produção, substituição de homologação).
- **FR-022**: O projeto MUST manter `STATUS.md` com fase, concluído, evidências, pendências,
  bloqueios e perguntas AGUARDANDO_USUARIO, atualizado ao fim de cada tarefa.
- **FR-023**: O repositório MUST NOT conter binários ou fontes TOTVS, dados de empresa nem
  credenciais; a verificação final MUST incluir varredura de segredo no histórico git, nas
  camadas e metadados da imagem do lab e nos logs do setup, com zero ocorrências.
- **FR-024**: O lab MUST NOT ser criado em repositório remoto, enviado (push) ou publicado em
  registry sem autorização explícita do dono.

### Key Entities

- **Release**: versão do Protheus suportada (2610, 2510); possui fonte principal e reserva de
  imagens, portas, credencial padrão documentada, versões medidas (AppServer, DBAccess, LIB,
  WebApp) e consumo medido (RAM, disco).
- **Stack**: instância em execução de uma release (banco, License Server, DBAccess, AppServer)
  com estado de saúde por serviço.
- **Fonte de imagem**: origem das imagens de uma release (comunidade principal, oficial ou
  comunidade reserva) com tag, digest e data de verificação.
- **Provedor de IA**: CLI suportada (Claude Code, Codex, opencode, Gemini), versão fixada, modos
  de autenticação suportados, local de skills e estado (configurado, testado, não testado).
- **Skill embarcada**: pacote de instruções publicado para as IAs (origem, licença, versão ou
  commit, destino por CLI).
- **Cenário**: teste de interface somente leitura (rotina padrão, releases confirmadas,
  evidência esperada).
- **Evidência**: registro de verificação (comando, saída resumida, artefatos, data, release).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A partir de um clone limpo e com as imagens já baixadas, um usuário chega ao menu
  do Protheus 2610 no navegador em até 10 minutos, seguindo apenas o README.
- **SC-002**: As duas releases ficam disponíveis ao mesmo tempo em 100% das subidas do teste
  final, e remover/recriar uma não altera a disponibilidade nem os dados da outra.
- **SC-003**: O smoke termina com "PRONTO" nas duas releases, com evidência salva para cada uma.
- **SC-004**: Rodar o assistente duas vezes seguidas produz o mesmo estado final, sem arquivos ou
  segredos duplicados.
- **SC-005**: A varredura final de segredos encontra zero ocorrências no histórico do
  repositório, na imagem do lab e nos logs do setup.
- **SC-006**: Pelo menos 3 cenários de leitura passam em pelo menos uma release, com a release
  confirmada registrada em cada README.
- **SC-007**: 100% das combinações IA × modo de autenticação aparecem no relatório final como
  "ok" (com evidência) ou "não testado" (com motivo); nenhuma fica sem status.
- **SC-008**: Ambientes Protheus/Docker já existentes na máquina continuam saudáveis durante e
  após todos os testes do lab (verificado antes e depois).
- **SC-009**: O README informa RAM e disco medidos de cada release e das duas juntas.

## Assumptions

- Plataforma de referência: Windows 11 com Docker Desktop (WSL2), memória suficiente alocada ao
  Docker e mais de 100 GB livres; outras plataformas são "não testado".
- Fonte principal das duas releases: imagens de comunidade `emebatista/*` (base padrão já
  restaurada); a mesma família de imagens nas duas releases reduz divergência de comportamento.
  Reservas: oficial TOTVS para 2510 e `feliperaposo/protheus:p12.1.2610` para 2610.
- O administrador padrão e sua senha são os documentados publicamente pela fonte da imagem; o lab
  não os grava em arquivos versionados e os recebe por variável de ambiente.
- O License Server de desenvolvimento das imagens permite login e uso para estudo; o lab não
  comprova direito de uso nem licença TOTVS, e isso é responsabilidade de quem instala.
- Login por conta das CLIs de IA dentro do container depende de interação humana (código/URL);
  quando o dono não estiver disponível, o item fica "não testado" e entra em AGUARDANDO_USUARIO.
- SmartView e DeskFlow ficam fora do escopo.
- Oracle, SQL Server, dados reais e uso em produção ficam fora do escopo.
- Publicação (GitHub, Docker Hub, redes sociais) fica fora desta entrega e depende de autorização.
