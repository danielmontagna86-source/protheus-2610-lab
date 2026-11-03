# Cenários da fase 2: proposta

author: daniel.montagna
Pesquisa: 03/11/2026. Situação: **proposta, nada executado** pela sessão que escreveu este documento.
Todos os cenários entram com `"releases": []` e só ganham release depois de passar com evidência
(regra de `cenarios/README.md`).

20 cenários: 5 de Compras (módulo 2), 5 de Estoque/Custos (4), 5 de Financeiro (6) e 5 de
Faturamento (5). Mais 1 transversal fiscal (FISA170, módulo 9), fora da contagem.

## Como ler este documento

- **Confirmado na fonte**: rotina, menu ou tabela aparecem no texto de uma página TOTVS (TDN ou
  Central de Atendimento) citada no cenário.
- **Conferido no lab (03/11/2026)**: fato informado pela sessão que tem o lab rodando, na base de
  demonstração, empresa 99, nas duas releases. Está marcado assim no texto.
- **A confirmar no lab**: não achei fonte primária, ou ela é antiga. Antes de criar a entrada no
  JSON, rode o explorador de menu (somente leitura) no container `lab`:

  ```bash
  python /opt/plab/lab/tir/explorar_menu.py <rel> <modulo> "Atualizações>..." [item]
  ```

  Ele lista os itens do caminho e, com `[item]`, abre a rotina e mostra abas, títulos e se a grade
  carregou.
- **Limite desta pesquisa**: a sessão em que este documento foi escrito não alcançava
  `tdn.totvs.com`, `centraldeatendimento.totvs.com` nem `protheus-release.totvs.io` (bloqueio de
  rede). As fontes TOTVS foram lidas pelo trecho que o buscador indexou, não pela página aberta.
  Todas foram acessadas em **03/11/2026**. Muitas são boletins de releases antigas (11 ou 12.1.x):
  o caminho de menu pode ter mudado e por isso o `explorar_menu.py` vem antes de qualquer entrada.
  Reabra as páginas no navegador antes de promover um cenário.
- Nomes de campo (`F4_CODIGO`, `C5_NUM` etc.) seguem o padrão de prefixo do Protheus, mas não foram
  conferidos no dicionário do lab. A pré-checagem começa sempre pelo SX2/SX3 da base.

## Resumo e prioridade

Prioridade 1 = rodar primeiro (menu confirmado em fonte ou no lab, dado conhecido na base, risco
baixo). Critério na seção [Priorização](#priorização).

| # | Módulo | Nome | Rotina | Tipo | Menu | Prior. |
|---|---|---|---|---|---|---|
| C1 | 2 Compras | pedido-compra-visualizar | MATA121 | leitura + visualizar | conferido no lab | **1** |
| C2 | 2 Compras | documento-entrada | MATA103 | leitura | fonte | **1** |
| C3 | 2 Compras | solicitacao-compras | MATA110 | leitura; **grava** (opcional) | lab (pasta) + fonte antiga | 2 |
| C4 | 2 Compras | cotacoes | MATA150 (a confirmar) | leitura | lab (pasta) | 3 |
| C5 | 2 Compras | liberar-documentos | MATA094 (a confirmar) | leitura, Help esperado | conferido no lab | 2 |
| E1 | 4 Estoque | movimentos-internos | MATA240 | leitura | fonte | **1** |
| E2 | 4 Estoque | transferencia-multipla | MATA261 | leitura | a confirmar | 2 |
| E3 | 4 Estoque | inventario | MATA270 | leitura; **grava** (opcional) | a confirmar | **1** |
| E4 | 4 Estoque | consulta-produto | MATC050 | consulta em tela | a confirmar | 3 |
| E5 | 4 Estoque | kardex | MATR900 | relatório em tela | a confirmar | 3 |
| F1 | 6 Financeiro | movimentos-bancarios | FINA100 | leitura | fonte | **1** |
| F2 | 6 Financeiro | posicao-cliente | FINC010 | consulta em tela | a confirmar | **1** |
| F3 | 6 Financeiro | naturezas | FINA010 | leitura; **grava** (opcional) | fonte | 2 |
| F4 | 6 Financeiro | compensacao-pagar | FINA340 | leitura | a confirmar | 2 |
| F5 | 6 Financeiro | bancos | MATA070 | leitura | a confirmar | 3 |
| V1 | 5 Faturamento | tes | MATA080 | leitura + visualizar | a confirmar | **1** |
| V2 | 5 Faturamento | pedido-venda | MATA410 | leitura + pesquisa + visualizar | fonte | **1** |
| V3 | 5 Faturamento | liberacao-estoque | MATA455 | leitura | fonte | 2 |
| V4 | 5 Faturamento | analise-credito-pedido | MATA450 | leitura | a confirmar | 2 |
| V5 | 5 Faturamento | condicao-pagamento | MATA360 | leitura; **grava** (opcional) | a confirmar | 3 |
| T1 | 9 Livros Fiscais | configurador-tributos | FISA170 | leitura | fonte | (fora) |

Grava: no máximo 1 por módulo (C3, E3, F3, V5). Cada uma é opcional, roda só com autorização
registrada do dono e tem reversão. A parte de leitura de cada cenário roda sem ela.

Mudança em relação à primeira versão deste PR: o cenário "pedido-compra-alcada" (gravar pedido com
alçada) saiu. No lab, a SCR está vazia, a tabela SAL não existe no banco, a SAK está vazia na 2610 e
não existe na 2510, e `MV_APRPCEC` = F (conferido no lab, 03/11/2026). Gerar alçada exigiria
cadastrar aprovador, grupo e mudar parâmetro: três gravações além do pedido. No lugar entram C1
(visualizar o pedido 000001 que já existe) e C5 (Liberar Documentos só leitura).

## Requisito comum: o runner atual só abre browse

`lab cenarios` lê do JSON apenas `nome`, `modulo`, `menu`, `aba`, `titulo`, `aviso` e `releases`
(`lab/bin/lib/cenarios.sh`), e o `smoke_ui.py` só confere título ou grade. Para os passos
"visualizar", "pesquisar", "consulta" e "relatório em tela" proponho uma chave opcional `passos`,
**ainda não implementada**. Como o `jq` do runner ignora chaves que não conhece, uma entrada com
`passos` roda hoje como leitura simples de browse. Implementar `passos` é trabalho de outro PR
(script + skill).

Regras desses passos:

- só botões de leitura: **Pesquisar**, **Visualizar**, **Fechar**/**Cancelar**. Nunca Incluir,
  Alterar, Excluir, Copiar, Aprovar, Liberar nem Confirmar;
- todo clique que fecha diálogo precisa de pós-condição (o diálogo sumiu), como em
  `references/tir.md`, "Complemento Playwright";
- pergunta (SX1) de consulta ou relatório: preencher só os parâmetros do cenário e conferir de
  volta cada valor antes de confirmar a pergunta (confirmar a pergunta não grava dado de negócio,
  mas grava o último valor usado no perfil do usuário: registrar isso como efeito aceito);
- sair sempre por "Log Off → Finalizar".

As partes "grava" não entram no `cenarios.json` (que é só leitura). Viram script próprio com flag
explícita, como `lab procedures`, em outro PR.

## Pré-checagem comum na base (somente leitura)

Rode em transação somente leitura no PostgreSQL da release (porta do `.env`; usuário e senha do
banco ficam no container, nunca em argumento):

```sql
BEGIN TRANSACTION READ ONLY;
-- 1) nome físico e modo de compartilhamento das tabelas do cenário (empresa 99)
SELECT X2_CHAVE, X2_ARQUIVO, X2_MODO
  FROM SX2990
 WHERE X2_CHAVE IN ('SC7','SF1','SD1','SC1','SC8','SCR','SD3','SB7','SB1','SB2','SB9',
                    'SE5','SE1','SA1','SED','SE2','FK2','SA6','SF4','SC5','SC6','SC9',
                    'SE4','F2B','CIN','F27','F28')
   AND D_E_L_E_T_ = ' ';
-- 2) a tabela física existe? (no PostgreSQL o nome fica em minúsculas)
SELECT table_name FROM information_schema.tables
 WHERE lower(table_name) IN ('sc7990','scr990','sak990','sal990','sb7990');
-- 3) campos que a consulta vai usar existem?
SELECT X3_ARQUIVO, X3_CAMPO, X3_TAMANHO FROM SX3990
 WHERE X3_CAMPO IN ('C7_NUM','F1_DOC','C1_NUM','D3_DOC','B7_COD','E5_DATA','ED_CODIGO')
   AND D_E_L_E_T_ = ' ';
ROLLBACK;
```

- Se `SX2990` não existir, o dicionário não está no banco nesta base: registre e confira pelo
  Configurador antes de seguir. Não presuma nome físico.
- **Tabela no SX2 sem tabela física** (caso da SAL e da SAK na 2510, conferido no lab): abrir a
  rotina pode fazer o Protheus criar a tabela física. Isso é DDL no banco do lab. Não confirmei em
  fonte se e quando isso acontece: compare a consulta 2 antes e depois da execução e registre o
  efeito, que não é gravação de dado de negócio mas também não é "nada mudou".
- Filial: `X2_MODO = 'C'` (compartilhada) usa filial em branco com o tamanho do campo `*_FILIAL`;
  `'E'` (exclusiva) usa `01`. Nas consultas abaixo, `:filial` é esse valor.
- Toda consulta de negócio filtra `D_E_L_E_T_ = ' '` e a filial. Use o nome físico vindo de
  `X2_ARQUIVO` (abaixo escrito como `<SC7>` etc.).
- Tabelas que não começam com S usam prefixo de 3 letras no campo (`FK2_FILIAL`, `F2B_FILIAL`).

---

# Compras (módulo 2)

Menu **conferido no lab** (03/11/2026) em Atualizações: Cadastros, Administração de Compras,
Central de Compras, Solicitações, Cotações, Pedidos (Pedidos de Compra, Eliminar Resíduos),
Liberação (Liberar de Documentos, Substituição de Aprovadores), Contratos, Movimentos, Acd, Novo
Fluxo de Compras, Central de Ia (só 2610) e Controle Orçamentário (só 2610).

## C1. pedido-compra-visualizar: visualizar um pedido de compra (MATA121)

| | |
|---|---|
| Rotina | MATA121 (Pedidos de Compra) |
| Menu | Atualizações > Pedidos > Pedidos de Compra (conferido no lab) |
| Tabelas | SC7 |
| Tipo | leitura + visualizar |
| Prioridade | **1** |

**Por que:** o cenário `pedido-compra` já abre o browse. Este vai um passo além com dado conhecido:
a SC7 da base tem 1 pedido, **000001, com 14 itens, todos `C7_CONAPRO = L`** (conferido no lab,
03/11/2026). Visualizar um pedido de 14 itens exercita a grade de itens, que é onde customização
de pedido de compra costuma quebrar em atualização. Não repete o cenário existente: o browse é
pré-condição, a conferência é do formulário.

**O que conferir na tela:**

1. Browse carregado; **Pesquisar** pelo número `000001` e conferir que a linha posicionada mostra
   esse número.
2. **Visualizar**: cabeçalho com número 000001 e o fornecedor da consulta; grade de itens com 14
   linhas (rolar a grade e contar; não aceitar "tem linhas" como 14).
3. **Fechar** e conferir que o formulário sumiu.

**Pré-checagem na base:**

```sql
BEGIN TRANSACTION READ ONLY;
SELECT C7_NUM, C7_FORNECE, C7_LOJA, COUNT(*) AS itens,
       SUM(CASE WHEN C7_CONAPRO = 'L' THEN 1 ELSE 0 END) AS liberados
  FROM <SC7> WHERE C7_FILIAL = :filial AND D_E_L_E_T_ = ' '
 GROUP BY C7_NUM, C7_FORNECE, C7_LOJA;
ROLLBACK;
```

Esperado: 1 linha, `000001`, 14 itens, 14 liberados. Valor diferente = base mudou; registre e não
ajuste o teste para passar.

**Riscos:** a grade de itens do pedido pode ter rolagem virtual (só renderiza as linhas visíveis);
contar pelo DOM visível dá número errado. Conferir pela rolagem ou registrar a limitação.

**Fontes:** cenário `pedido-compra` (MATA121, módulo 2, Atualizações > Pedidos > Pedidos de
Compra) e fatos do lab informados em 03/11/2026. Ver também C5 (alçada), onde aparece a relação de
MATA121 com MATA094 no TDN.

```json
{"nome": "pedido-compra-visualizar", "rotina": "MATA121", "modulo": 2, "menu": ["Atualizações", "Pedidos", "Pedidos de Compra"], "aba": "Pedidos de Compra", "titulo": "", "passos": [{"acao": "pesquisar", "valor": "000001"}, {"acao": "visualizar", "conferir": {"C7_NUM": "000001", "itens": 14}, "capturar": "formulario"}], "releases": []}
```

## C2. documento-entrada: Documento de Entrada (MATA103)

| | |
|---|---|
| Rotina | MATA103 |
| Menu | Atualizações > Movimentos > Documento Entrada (fonte: boletim do TDN; a pasta "Movimentos" existe no lab) |
| Tabelas | SF1 (cabeçalho), SD1 (itens) |
| Tipo | leitura |
| Prioridade | **1** |

**Por que:** porta de entrada fiscal e de estoque, a rotina com mais ponto de entrada no Compras
(`SF1100I`, `SD1100I`, `MT103DNF`, `MT100AG`...) e a primeira a sentir a mudança da TES e do
Configurador de Tributos na 2610 (V1 e T1).

**O que conferir na tela:** browse com a grade carregada. Sem visualizar nesta fase: a
visualização monta abas fiscais e financeiras que convém mapear antes com o `explorar_menu.py`.

```bash
python /opt/plab/lab/tir/explorar_menu.py 2610 2 "Atualizações>Movimentos" "Documento Entrada"
```

**Pré-checagem na base:**

```sql
BEGIN TRANSACTION READ ONLY;
SELECT COUNT(*) AS docs FROM <SF1> WHERE F1_FILIAL = :filial AND D_E_L_E_T_ = ' ';
SELECT COUNT(*) AS itens FROM <SD1> WHERE D1_FILIAL = :filial AND D_E_L_E_T_ = ' ';
ROLLBACK;
```

Esperado: ao menos 1 documento. Se a SF1 estiver vazia, o critério de grade falha: conferir pelo
título do browse (`titulo`) e anotar "sem documento na base". Não lance nota para preencher a grade.

**Riscos:** stored procedure exigida (janela "Incompatibilidade"): tratar como bloqueio, conforme
`references/procedures.md`; avisos de parâmetro ao abrir: usar `aviso` só se for informativo.

**Fontes:**

- TDN, boletim "Desabilita Validação de Itens Utilizados no Documento de Entrada" (caminho, SF1 e
  SD1):
  https://tdn.totvs.com/download/attachments/22479114/COM_Desabilita%20Validacao%20de%20Itens%20Utilizados%20no%20Documento%20de%20Entrada_TEXKUM.pdf?api=v2
- TDN, pontos de entrada SF1100I https://tdn.totvs.com/x/8Ntc , SD1100I https://tdn.totvs.com/x/7dtc ,
  MT103DNF https://tdn.totvs.com/x/Itxc

```json
{"nome": "documento-entrada", "rotina": "MATA103", "modulo": 2, "menu": ["Atualizações", "Movimentos", "Documento Entrada"], "aba": "Documento Entrada", "titulo": "", "releases": []}
```

## C3. solicitacao-compras: Solicitação de Compras (MATA110), com gravação opcional

| | |
|---|---|
| Rotina | MATA110 |
| Menu | Atualizações > Solicitações > Solicitação de Compras (pasta "Solicitações" conferida no lab; o boletim do TDN, da versão 11, usa "Solicitar/Cotar": **rótulo do item a confirmar**) |
| Tabelas | SC1; efeito em SB2 (`B2_SALPEDI`, quantidade prevista) |
| Tipo | leitura; **grava** opcional (Parte B) |
| Prioridade | 2 |

```bash
python /opt/plab/lab/tir/explorar_menu.py 2610 2 "Atualizações>Solicitações"
```

**Por que:** início do ciclo de compras e o cadastro mais simples de gravar e reverter no módulo. A
inclusão mexe em estoque previsto (`B2_SALPEDI`, conforme o parâmetro `MV_SCSLDBL` do boletim), o
que dá uma conferência de efeito de negócio além da própria SC1.

**Parte A (leitura):** browse; se houver SC na base, também **Visualizar** a primeira.

**Parte B (grava; só com autorização registrada do dono):**

1. Baseline: `MAX(C1_NUM)`, contagem ativa da SC1 e `B2_SALPEDI` do produto e armazém escolhidos.
2. Incluir 1 SC com 1 item, produto e armazém existentes, quantidade 1. Anotar número.
3. Conferir: 1 SC nova na SC1; `B2_SALPEDI` com a variação que o `MV_SCSLDBL` da base indica (ler o
   parâmetro antes; não presumir).
4. **Reversão:** excluir a SC pela própria MATA110. Conferir: SC1 do número anotado com
   `D_E_L_E_T_ = '*'` ou ausente, contagem ativa igual ao baseline e `B2_SALPEDI` igual ao baseline.
5. Se sobrar diferença: `plab down <rel> --volumes` + `plab up <rel>` (na 2610, depois
   `lab procedures 2610 08`) e registrar a falha.

**Pré-checagem na base:**

```sql
BEGIN TRANSACTION READ ONLY;
SELECT COUNT(*) AS scs, MAX(C1_NUM) AS ultima FROM <SC1> WHERE C1_FILIAL = :filial AND D_E_L_E_T_ = ' ';
SELECT X6_VAR, X6_CONTEUD FROM SX6990
 WHERE X6_VAR IN ('MV_SCSLDBL') AND X6_FIL IN (:filial, '  ') AND D_E_L_E_T_ = ' ';
ROLLBACK;
```

**Riscos:** a SC pode cair em alçada se a base tiver parâmetro de aprovação de SC ligado (hoje não
há aprovador, ver C5); numeração consumida não volta (aceito em base de lab).

**Fontes:**

- TDN, boletim "Criação do parâmetro MV_SCSLDBL" (MATA110, SC1, `B2_SALPEDI`):
  https://tdn.totvs.com.br/download/attachments/185758344/COM_BT_Criacao_do_parametro_MV_SCSLDBL_TRVHF1.pdf?api=v2
- TDN, boletim "Rateio do Pedido de Compras por Edital" (MATA110 alimentando o pedido):
  https://tdn.totvs.com/download/attachments/55542260/COM_BT_%20Rateio%20do%20Pedido%20de%20Compras%20por%20Edital_BRA_TFNV96.pdf?api=v2

```json
{"nome": "solicitacao-compras", "rotina": "MATA110", "modulo": 2, "menu": ["Atualizações", "Solicitações", "Solicitação de Compras"], "aba": "Solicitação de Compras", "titulo": "", "releases": []}
```

## C4. cotacoes: Atualizar Cotações (rotina a confirmar)

| | |
|---|---|
| Rotina | **a confirmar no lab**; pela pasta, esperado MATA150 (Atualizar Cotações). Não achei fonte TOTVS |
| Menu | Atualizações > Cotações > (item a confirmar) — pasta conferida no lab |
| Tabelas | SC8 (a confirmar no SX2) |
| Tipo | leitura |
| Prioridade | 3 |

```bash
python /opt/plab/lab/tir/explorar_menu.py 2610 2 "Atualizações>Cotações"
```

**Por que:** fecha o ciclo SC → cotação → pedido. A cotação é a tela de compras com mais variação
entre clientes (composição de preço, várias condições de pagamento por fornecedor, citada em nota
de release TOTVS) e é candidata natural a mudar na "Central de Compras" e no "Novo Fluxo de Compras"
que aparecem no menu.

**O que conferir na tela:** abrir só o item de **atualização/consulta** da cotação. Não abrir
"Gerar Cotações" (grava SC8 a partir de SC) nem "Analisar Cotações" (gera pedido).

**Pré-checagem na base:**

```sql
BEGIN TRANSACTION READ ONLY;
SELECT COUNT(*) FROM <SC8> WHERE C8_FILIAL = :filial AND D_E_L_E_T_ = ' ';
ROLLBACK;
```

Esperado: desconhecido. SC8 vazia → conferir por título.

**Riscos:** a rotina pode abrir uma pergunta (SX1) antes do browse; responder só com Cancelar se não
der para seguir sem gravar perfil, e registrar.

**Fontes:** nenhuma primária para a rotina. Contexto: nota de release TOTVS com "Composição de Preço
da Cotação" e mais de uma condição de pagamento por fornecedor:
https://tdn.totvs.com.br/download/attachments/545623085/Novidades%20da%20vers%C3%A3o%2012.1.28%20%281%29.pdf?api=v2

```json
{"nome": "cotacoes", "rotina": "MATA150", "modulo": 2, "menu": ["Atualizações", "Cotações", "Atualiza Cotações"], "aba": "", "titulo": "", "releases": []}
```

`rotina`, item de menu e `aba` são suposições até o `explorar_menu.py`.

## C5. liberar-documentos: Liberação de Documentos sem aprovador (Help esperado)

| | |
|---|---|
| Rotina | **a confirmar no lab**: o TDN liga "Liberação de Documentos" à MATA094 (que substituiu a MATA097); o Help observado no lab é `A097APROV` |
| Menu | Atualizações > Liberação > Liberar de Documentos (conferido no lab, rótulo exato) |
| Tabelas | SCR (documentos com alçada), DBM (itens), SAK/SAL (aprovadores e grupos, sem fonte TOTVS) |
| Tipo | leitura, com mensagem esperada |
| Prioridade | 2 |

**Por que:** foi o fluxo sugerido no comentário do post de divulgação (`STATUS.md`). Na base do lab
não há alçada: SCR vazia, SAL inexistente, SAK vazia na 2610 e inexistente na 2510,
`MV_APRPCEC` = F, e **na 2610 a rotina abre com o Help `A097APROV` para o Admin** (tudo conferido
no lab, 03/11/2026). Um cenário negativo útil: confere que a rotina recusa usuário que não é
aprovador, com a mensagem certa, nas duas releases. Customização de alçada (`MT094CPC`,
`MT094CCR`) costuma quebrar justamente nessa entrada.

**O que conferir na tela:**

1. Abrir o item; esperar o Help. Capturar o texto completo; conferir que contém `A097APROV`.
2. Fechar o Help pelo botão do próprio Help e conferir que sumiu. Registrar o que sobra na tela
   (rotina fechada ou browse vazio).
3. Na 2510, registrar o comportamento observado (pode ser o mesmo Help ou outro). **Não** concluir
   que é igual sem a captura.

**Pré-checagem na base:** a consulta 2 da pré-checagem comum (SAK e SAL físicas) **antes e depois**:
na 2510 a SAK não existe e abrir a rotina pode criá-la (ver "Tabela no SX2 sem tabela física").

```sql
BEGIN TRANSACTION READ ONLY;
SELECT COUNT(*) FROM <SCR> WHERE CR_FILIAL = :filial AND D_E_L_E_T_ = ' ';
SELECT X6_VAR, X6_CONTEUD FROM SX6990
 WHERE X6_VAR = 'MV_APRPCEC' AND X6_FIL IN (:filial, '  ') AND D_E_L_E_T_ = ' ';
ROLLBACK;
```

**Riscos:** o runner atual trata janela inesperada como falha; o Help aqui é o resultado esperado,
por isso precisa de `passos` (`esperar_help`). Não cadastrar aprovador para "fazer abrir".

**Fontes:**

- TDN, ponto de entrada MT094CPC (botão "Aprovar" da MATA094; tipos PC, IP e AE):
  https://tdn.totvs.com/pages/releaseview.action?pageId=286224513
- TDN, DMANMAT02-2006 "Liberação Documento, Ponto Entrada MT094CCR":
  https://tdn.totvs.com.br/pages/releaseview.action?pageId=306844678
- TDN, DMANMAT02-7926 "Alçadas Entidade Contábil PC..." (MATXALC e MATA094; SCR):
  https://tdn.totvs.com/pages/releaseview.action?pageId=346495116
- Central TOTVS, "SIGACOM - Ciclo de vida - Rotina Liberação de Documentos (MATA097)" (troca da
  MATA097 pela MATA094; SCR e DBM):
  https://centraldeatendimento.totvs.com/hc/pt-br/articles/360036907834

```json
{"nome": "liberar-documentos", "rotina": "MATA094", "modulo": 2, "menu": ["Atualizações", "Liberação", "Liberar de Documentos"], "aba": "", "titulo": "", "passos": [{"acao": "esperar_help", "contem": "A097APROV", "fechar": true}], "releases": []}
```

---

# Estoque/Custos (módulo 4)

Nenhum item do menu de Estoque foi conferido no lab até aqui. Comece por:

```bash
python /opt/plab/lab/tir/explorar_menu.py 2610 4 "Atualizações"
python /opt/plab/lab/tir/explorar_menu.py 2610 4 "Atualizações>Movimentos Internos"
```

## E1. movimentos-internos: Movimentos Internos (MATA240)

| | |
|---|---|
| Rotina | MATA240 |
| Menu | Atualizações > Movimentos Internos > Internos (fonte: boletim do TDN) |
| Tabelas | SD3 (movimentos internos); saldo em SB2 |
| Tipo | leitura |
| Prioridade | **1** |

**Por que:** é a rotina de requisição e devolução interna, base de custo e de quase toda integração
de produção e manutenção. O saldo considerado nela depende de parâmetro (`MV_SLDEMPE`, `MV_TPSALDO`),
o que torna a tela sensível a atualização. Menu confirmado em fonte.

**O que conferir na tela:** browse com a grade carregada.

**Pré-checagem na base:**

```sql
BEGIN TRANSACTION READ ONLY;
SELECT D3_TM, COUNT(*) FROM <SD3> WHERE D3_FILIAL = :filial AND D_E_L_E_T_ = ' ' GROUP BY D3_TM;
ROLLBACK;
```

Esperado: desconhecido. SD3 vazia → conferir por título.

**Riscos:** a rotina pode filtrar o browse por tipo de movimento; grade vazia não prova SD3 vazia.

**Fontes:**

- TDN, boletim "Parâmetro MV_SLDEMPE" (caminho Atualizações / Movimentos Internos / Internos,
  MATA240):
  https://tdn.totvs.com/download/attachments/23199768/EST_Parametro%20MV_SLDEMPE_TENATG.pdf?api=v2
- TDN, "Movimentos Internos - Estoque": https://tdn.totvs.com/display/public/PROT/Movimentos+Internos+-+Estoque

```json
{"nome": "movimentos-internos", "rotina": "MATA240", "modulo": 4, "menu": ["Atualizações", "Movimentos Internos", "Internos"], "aba": "Internos", "titulo": "", "releases": []}
```

## E2. transferencia-multipla: Transferência Modelo 2 (MATA261)

| | |
|---|---|
| Rotina | MATA261 (transferência múltipla / modelo 2) |
| Menu | **a confirmar no lab**: esperado em Atualizações > Movimentos Internos (onde o TDN coloca a MATA310, Transferência Filiais) |
| Tabelas | SD3 (`D3_DOC`) |
| Tipo | leitura |
| Prioridade | 2 |

**Por que:** transferência entre armazéns é a movimentação mais usada depois do movimento interno,
e tem ponto de entrada de numeração (`MT261DOCT`) e integração com WMS (`MA261WMS`), ambos
sensíveis a atualização.

**O que conferir na tela:** browse com a grade carregada (ou título, se a SD3 não tiver
transferências).

**Pré-checagem na base:**

```sql
BEGIN TRANSACTION READ ONLY;
SELECT COUNT(DISTINCT D3_DOC) FROM <SD3>
 WHERE D3_FILIAL = :filial AND D_E_L_E_T_ = ' ' AND D3_CF IN ('RE4','DE4');
ROLLBACK;
```

Os códigos `RE4`/`DE4` para transferência são conhecimento de uso, **não conferidos em fonte**;
confirme pelo combo do SX3 de `D3_CF` antes de usar o resultado.

**Fontes:**

- TDN, DLOGWMSMSP-15057 "PE MT261DOCT - Permitir a alteração do número do documento na rotina de
  transferência múltipla":
  https://tdn.totvs.com/download/attachments/743698516/16346908%20DLOGWMSMSP-15057%20DT%20PE%20MT261DOCT%20-%20Permitir%20a%20altera%C3%A7%C3%A3o%20%20do%20n%C3%BAmero%20do%20documento%20na%20rotina%20de%20transfer%C3%AAncia%20m%C3%BAltipla.pdf?api=v2
- TDN, DLOGWMSMSP-13546 "Geração do número do documento na tabela SD3 (MATA261)":
  https://tdn.totvs.com.br/download/attachments/667927728/13481667%20DLOGWMSMSP-13546%20DT%20Gera%C3%A7%C3%A3o%20do%20n%C3%BAmero%20do%20documento%20na%20%20tabela%20SD3%20%28MATA261%29.pdf?api=v2
- TDN, boletim "MATA310 TES Inteligente" (Atualizações / Movimentos Internos / Transferência
  Filiais):
  https://tdn.totvs.com.br/download/attachments/187829987/EST_BT_MATA310_TES_Inteligente_TRVFY1.pdf?api=v2

```json
{"nome": "transferencia-multipla", "rotina": "MATA261", "modulo": 4, "menu": ["Atualizações", "Movimentos Internos", "Transferência Mod. 2"], "aba": "", "titulo": "", "releases": []}
```

Item de menu e `aba` são suposições.

## E3. inventario: Inventário (MATA270), com gravação opcional

| | |
|---|---|
| Rotina | MATA270 (digitação do inventário); MATA340 é o acerto, **fora** do cenário |
| Menu | **a confirmar no lab** (esperado Atualizações > Inventário) |
| Tabelas | SB7 (lançamentos de inventário; campo `B7_ORIGEM` citado no TDN) |
| Tipo | leitura; **grava** opcional (Parte B) |
| Prioridade | **1** (Parte A) |

**Por que:** fontes de mercado sobre a 2610 citam mudança no agendamento de inventário para a
MATA270 (fonte secundária, a confirmar no TDN). A digitação de inventário é a gravação mais segura
do módulo: só muda saldo quando o acerto (MATA340) roda, e o cenário nunca roda o acerto.

**Parte A (leitura):** browse da digitação (grade ou título).

**Parte B (grava; só com autorização registrada do dono):**

1. Baseline: contagem ativa da SB7 e `B2_QATU` do produto/armazém escolhidos.
2. Incluir 1 lançamento de inventário (produto e armazém existentes, quantidade igual ao
   `B2_QATU`, data do dia).
3. Conferir: 1 linha nova na SB7; `B2_QATU` **inalterado**.
4. **Reversão:** excluir o lançamento pela própria MATA270. Conferir SB7 igual ao baseline e
   `B2_QATU` inalterado.
5. Nunca executar MATA340. Se sobrar diferença: `plab down <rel> --volumes` + `plab up <rel>`.

**Pré-checagem na base:**

```sql
BEGIN TRANSACTION READ ONLY;
SELECT COUNT(*) FROM <SB7> WHERE B7_FILIAL = :filial AND D_E_L_E_T_ = ' ';
SELECT B2_COD, B2_LOCAL, B2_QATU FROM <SB2>
 WHERE B2_FILIAL = :filial AND D_E_L_E_T_ = ' ' AND B2_QATU > 0 ORDER BY B2_COD LIMIT 5;
ROLLBACK;
```

**Riscos:** com `MV_WMSNEW` ativo, o "Incluir" da MATA270 tem problema registrado no TDN; ler o
parâmetro antes da Parte B. Inventário pode bloquear o produto para movimentação enquanto houver
lançamento aberto (boletim "bloqueio inventário"): por isso a exclusão vem logo depois.

**Fontes:**

- TDN, boletim "Integração WMS Logix - Inventário" (MATA270, SB7, MATA340, `B7_ORIGEM`):
  https://tdn.totvs.com/download/attachments/547227753/est_bt_integracao_wmslogix_inventario_tfgagt.pdf?api=v2
- TDN, DLOGWMSMSP-14367 "Divergência na abertura da tela de inventário no módulo 04 (MATA270)":
  https://tdn.totvs.com/download/attachments/706126737/14618309%20DLOGWMSMSP-14367%20DT%20Diverg%C3%AAncia%20na%20abertura%20da%20tela%20de%20invent%C3%A1rio%20no%20m%C3%B3dulo%2004%20%28MATA270%29.pdf?api=v2
- TDN, boletim "Gestão de empresas no bloqueio inventário":
  https://tdn.totvs.com.br/download/attachments/150635284/EST_BT_Gestao_de_empresas_no_bloqueio_inventario_TPYPN8.pdf?api=v2
- Secundária (agendamento de inventário na MATA270 na 2610):
  https://www.2fconsultoria.com.br/2026/10/totvs-protheus-12-1-2610-pontos-de-atencao-obrigatorios-antes-de-atualizar-o-erp/

```json
{"nome": "inventario", "rotina": "MATA270", "modulo": 4, "menu": ["Atualizações", "Inventário", "Digitação"], "aba": "", "titulo": "", "releases": []}
```

## E4. consulta-produto: consulta de saldos do produto (MATC050)

| | |
|---|---|
| Rotina | MATC050 (consulta; nome exato da tela a confirmar) |
| Menu | **a confirmar no lab** (esperado Consultas, fora de Atualizações) |
| Tabelas | SB1, SB2 (saldo físico e financeiro por produto e armazém, `B2_QATU`, `B2_QFIM`) |
| Tipo | consulta em tela (além do browse) |
| Prioridade | 3 |

```bash
python /opt/plab/lab/tir/explorar_menu.py 2610 4 "Consultas"
```

**Por que:** consulta de saldo é o que o usuário abre para conferir estoque antes de chamar a TI.
Dá um cenário "além do browse" sem gravar: escolher um produto e conferir o saldo exibido contra o
SB2.

**O que conferir na tela:** informar o código de um produto da pré-checagem (ou usar F3 para
escolher), conferir o saldo exibido igual a `SUM(B2_QATU)` do produto (ou por armazém, se a tela
separar), fechar.

**Pré-checagem na base:**

```sql
BEGIN TRANSACTION READ ONLY;
SELECT B2_COD, SUM(B2_QATU) AS qatu FROM <SB2>
 WHERE B2_FILIAL = :filial AND D_E_L_E_T_ = ' ' GROUP BY B2_COD HAVING SUM(B2_QATU) > 0
 ORDER BY B2_COD LIMIT 5;
ROLLBACK;
```

**Riscos:** a tela pode mostrar saldo em outra unidade ou com empenho descontado; não ajustar a
comparação sem entender qual saldo é exibido.

**Fontes:** TDN cita MATC050 só em índice de páginas (sem conteúdo lido). SB2 e campos `B2_QFIM`:
boletim "Conferência de Saldos"
https://tdn.totvs.com.br/download/attachments/126714501/EST_BT_Conferencia_de_Saldos_THZJVF.pdf?api=v2

```json
{"nome": "consulta-produto", "rotina": "MATC050", "modulo": 4, "menu": ["Consultas", "Cadastros", "Produtos"], "aba": "", "titulo": "", "passos": [{"acao": "consulta", "campo": "produto", "valor_de": "pre-checagem B2_COD", "conferir": "saldo"}], "releases": []}
```

Menu é suposição.

## E5. kardex: Kardex por período (MATR900), relatório em tela

| | |
|---|---|
| Rotina | MATR900 |
| Menu | **a confirmar no lab** (esperado Relatórios) |
| Tabelas | SD1, SD2, SD3, SB2, SB9 |
| Tipo | relatório em tela (visualização, sem impressora) |
| Prioridade | 3 |

**Por que:** Kardex é o relatório que mais vai para auditoria de estoque e um dos que mais
"quebra" layout em atualização. É o único cenário que testa o caminho pergunta (SX1) → relatório,
pedido pelos critérios ("relatório em tela").

**O que conferir na tela:** abrir, preencher período e 1 produto, saída **em tela** (visualização),
conferir o código do produto no relatório e fechar. Não enviar para impressora, e-mail ou disco do
servidor. Se a única saída for arquivo no servidor, registrar e parar.

**Pré-checagem:** mesma do E4 (produto com movimento) e `SELECT MIN(D3_EMISSAO), MAX(D3_EMISSAO)`
da SD3 para escolher o período.

**Riscos:** relatório TReport no WebApp pode abrir nova aba ou baixar arquivo; o runner precisa
capturar e fechar sem deixar sessão presa (licença).

**Fontes:** TDN cita "Kardex por período (MATR900)" só pelo título (sem conteúdo lido). Relação SB2,
SB9, SD1, SD2 e SD3 na conferência de saldos (MATR282): boletim acima.

```json
{"nome": "kardex", "rotina": "MATR900", "modulo": 4, "menu": ["Relatórios", "Movimentações", "Kardex"], "aba": "", "titulo": "", "passos": [{"acao": "relatorio_tela", "perguntas": {"produto": "pre-checagem", "periodo": "pre-checagem"}}], "releases": []}
```

Menu é suposição.

---

# Financeiro (módulo 6)

Os cenários existentes FINA040 e FINA050 abrem os browses de títulos. Os de baixo cobrem banco,
consulta, cadastro e compensação.

## F1. movimentos-bancarios: Movimentos Bancários (FINA100)

| | |
|---|---|
| Rotina | FINA100 |
| Menu | Atualizações > Movimento Bancário > Movimentos Bancários (fonte: TDN) |
| Tabelas | SE5 (`E5_DATA`) |
| Tipo | leitura |
| Prioridade | **1** |

**Por que:** é onde o caixa e o banco do dia a dia aparecem; contabilização on-line depende de
parâmetro (`MV_DTCNMOV`) e de F12. Menu confirmado em fonte.

**O que conferir na tela:** browse com a grade carregada. Não apertar F12 (abre parâmetros da
rotina; confirmar grava o perfil).

**Pré-checagem na base:**

```sql
BEGIN TRANSACTION READ ONLY;
SELECT COUNT(*), MIN(E5_DATA), MAX(E5_DATA) FROM <SE5> WHERE E5_FILIAL = :filial AND D_E_L_E_T_ = ' ';
ROLLBACK;
```

**Riscos:** aviso MV_1DUP da base, como no FINA040/050 (`aviso`); possível procedure exigida
(tratar como bloqueio).

**Fontes:** TDN, artigo sobre `MV_DTCNMOV` (caminho Atualizações / Movimento Bancário / Movimentos
Bancários, FINA100, `E5_DATA`): https://tdn.totvs.com/x/-HtvJw ; guia de importação de movimentos no
FINA100 via MILE (SE5): https://tdn.totvs.com/x/5b6mHQ

```json
{"nome": "movimentos-bancarios", "rotina": "FINA100", "modulo": 6, "menu": ["Atualizações", "Movimento Bancário", "Movimentos Bancários"], "aba": "Movimentos Bancários", "titulo": "", "aviso": "MV_1DUP", "releases": []}
```

## F2. posicao-cliente: Posição de Clientes (FINC010), consulta em tela

| | |
|---|---|
| Rotina | FINC010 |
| Menu | **a confirmar no lab** (esperado Consultas > Posição Clientes) |
| Tabelas | SA1, SE1 (relação esperada; não achei fonte que cite as tabelas) |
| Tipo | consulta em tela (além do browse) |
| Prioridade | **1** |

```bash
python /opt/plab/lab/tir/explorar_menu.py 2610 6 "Consultas"
```

**Por que:** é a tela que cobrança e comercial mais abrem, e o TDN documenta as opções (cheques,
títulos recebidos, títulos em aberto, pedidos). A base tem títulos a receber (o cenário
contas-receber carrega a grade), então há dado para conferir.

**O que conferir na tela:** escolher um cliente com título em aberto (pré-checagem), abrir a
consulta, conferir a quantidade e o total em aberto exibidos contra o SQL, abrir a opção
**Títulos em aberto**, fechar. Não usar a opção de impressão.

**Pré-checagem na base:**

```sql
BEGIN TRANSACTION READ ONLY;
SELECT E1_CLIENTE, E1_LOJA, COUNT(*) AS titulos, SUM(E1_SALDO) AS saldo
  FROM <SE1> WHERE E1_FILIAL = :filial AND D_E_L_E_T_ = ' ' AND E1_SALDO > 0
 GROUP BY E1_CLIENTE, E1_LOJA ORDER BY titulos DESC LIMIT 5;
ROLLBACK;
```

**Riscos:** a consulta pode somar abatimentos, juros ou outra moeda; diferença de valor exige
entender a coluna antes de reprovar. Pergunta inicial (SX1) grava o último valor no perfil.

**Fontes:** TDN (cópia de homologação), opções da FINC010: https://tdn-homolog.totvs.com/x/EEEWJQ ;
impressão da FINC010 e seus limites: https://tdn-homolog.totvs.com/x/G0MWJQ

```json
{"nome": "posicao-cliente", "rotina": "FINC010", "modulo": 6, "menu": ["Consultas", "Posição Clientes"], "aba": "", "titulo": "", "aviso": "MV_1DUP", "passos": [{"acao": "consulta", "campo": "cliente", "valor_de": "pre-checagem E1_CLIENTE", "conferir": ["titulos", "saldo"]}, {"acao": "botao_leitura", "rotulo": "Títulos em aberto"}], "releases": []}
```

## F3. naturezas: Naturezas (FINA010), com gravação opcional

| | |
|---|---|
| Rotina | FINA010 |
| Menu | Atualizações > Cadastros > Naturezas (fonte: boletim TOTVS de integração) |
| Tabelas | SED |
| Tipo | leitura; **grava** opcional (Parte B) |
| Prioridade | 2 |

**Por que:** toda movimentação financeira usa natureza; é o cadastro de financeiro mais simples de
gravar e excluir sem efeito em saldo. Bom para provar o ciclo grava → confere → reverte do runner.

**Parte A (leitura):** browse; **Visualizar** a primeira natureza.

**Parte B (grava; só com autorização):**

1. Baseline: contagem ativa da SED; escolher código que **não existe** (ex.: prefixo `ZZ`,
   conferido por SQL).
2. Incluir a natureza com descrição "LAB TESTE". Conferir 1 linha nova.
3. **Reversão:** excluir pela FINA010. Conferir SED igual ao baseline.
4. Se a exclusão for recusada ou sobrar resto: `plab down <rel> --volumes` + `plab up <rel>`.

**Pré-checagem na base:**

```sql
BEGIN TRANSACTION READ ONLY;
SELECT COUNT(*) FROM <SED> WHERE ED_FILIAL = :filial AND D_E_L_E_T_ = ' ';
SELECT ED_CODIGO FROM <SED> WHERE ED_FILIAL = :filial AND ED_CODIGO LIKE 'ZZ%';
ROLLBACK;
```

**Riscos:** natureza pode ter estrutura sintética/analítica e máscara; o código de teste precisa
respeitar a máscara da base (ler o SX3).

**Fontes:** boletim "TOTVS Incorporação x Back Office Protheus - Cadastros - Natureza Financeira"
(caminho Atualizações > Cadastros > Naturezas):
https://tdn.totvs.com.br/download/attachments/123602193/TOTVS%20Incorpora%2B%C2%BA%2B%C3%BAo%20x%20Back%20Office%20Protheus%20%C3%94%C3%87%C3%B4%20Cadstros-%20Natureza%20Financeira.pdf?api=v2 ;
TDN (homologação), execução automática da FINA010 sobre a SED: https://tdn-homolog.totvs.com/x/DRAdJQ

```json
{"nome": "naturezas", "rotina": "FINA010", "modulo": 6, "menu": ["Atualizações", "Cadastros", "Naturezas"], "aba": "Naturezas", "titulo": "", "aviso": "MV_1DUP", "passos": [{"acao": "visualizar", "linha": 1, "capturar": "formulario"}], "releases": []}
```

## F4. compensacao-pagar: Compensação Contas a Pagar (FINA340)

| | |
|---|---|
| Rotina | FINA340 |
| Menu | **a confirmar no lab** (esperado Atualizações > Contas a Pagar > Compensação) |
| Tabelas | SE2, SE5, FK2, FKA, FK6, FK7 (citadas em correção do TDN) |
| Tipo | leitura |
| Prioridade | 2 |

```bash
python /opt/plab/lab/tir/explorar_menu.py 2610 6 "Atualizações>Contas a Pagar"
```

**Por que:** fontes de mercado sobre a 2610 citam a lógica de compensação passando para os campos
`FK1_IDCOMP`/`FK2_IDCOMP` (fonte secundária; **não achei no TDN**). Se for verdade, é mudança de
estrutura que quebra relatório e query customizados sobre compensação. O cenário abre a tela e a
pré-checagem confere se o campo existe no SX3 de cada release.

**O que conferir na tela:** abrir a rotina até a seleção (pergunta ou browse) e **Cancelar**. Não
compensar.

**Pré-checagem na base:**

```sql
BEGIN TRANSACTION READ ONLY;
SELECT X3_ARQUIVO, X3_CAMPO FROM SX3990
 WHERE X3_CAMPO IN ('FK1_IDCOMP','FK2_IDCOMP') AND D_E_L_E_T_ = ' ';
SELECT COUNT(*) FROM <SE2> WHERE E2_FILIAL = :filial AND D_E_L_E_T_ = ' ' AND E2_SALDO > 0;
ROLLBACK;
```

Esperado: campos presentes só na 2610 (hipótese). O resultado nas duas releases é a evidência; não
afirmar a mudança sem ele.

**Riscos:** FINA050 na 2610 exigiu procedure 08; a compensação pode exigir outro processo
(janela "Incompatibilidade" = bloqueio).

**Fontes:** TDN, pontos de entrada da compensação CP: F340VLD https://tdn.totvs.com/x/J6Vc ,
FA340FIL https://tdn.totvs.com/x/rqNc , F340GREST https://tdn.totvs.com/x/iqVc ; nota com
`U_FA340FIX` (SE5, FKA, FK2, FK6, FK7) no resultado da busca (página a reabrir); secundária sobre
`FK1_IDCOMP`/`FK2_IDCOMP`:
https://www.2fconsultoria.com.br/2026/10/totvs-protheus-12-1-2610-pontos-de-atencao-obrigatorios-antes-de-atualizar-o-erp/

```json
{"nome": "compensacao-pagar", "rotina": "FINA340", "modulo": 6, "menu": ["Atualizações", "Contas a Pagar", "Compensação"], "aba": "", "titulo": "", "aviso": "MV_1DUP", "releases": []}
```

## F5. bancos: Bancos (MATA070)

| | |
|---|---|
| Rotina | MATA070 (nome por conhecimento de uso; **a confirmar**) |
| Menu | **a confirmar no lab** (esperado Atualizações > Cadastros > Bancos) |
| Tabelas | SA6 (citada no TDN do boleto Santander); SEE (subconta) |
| Tipo | leitura |
| Prioridade | 3 |

**Por que:** cadastro de banco é pré-requisito de boleto, CNAB e movimento bancário (F1); é
pequeno e estável, bom como controle: se ele falhar, o problema é de ambiente.

**O que conferir na tela:** browse com a grade carregada.

**Pré-checagem na base:**

```sql
BEGIN TRANSACTION READ ONLY;
SELECT COUNT(*) FROM <SA6> WHERE A6_FILIAL = :filial AND D_E_L_E_T_ = ' ';
ROLLBACK;
```

**Riscos:** baixo. Cadastro de banco pode ter acesso restrito por usuário (o tutorial TOTVS cita
liberação de acesso depois do cadastro); com o Admin não deve haver restrição.

**Fontes:** TDN, "Santander - Bank Slip Configuration - FINA710" (SA6 e SEE):
https://tdn.totvs.com.br/display/LMPING/Santander+-+Bank+Slip+Configuration+-+FINA710 ; tutorial
TOTVS de cadastro de banco:
https://tdn.totvs.com.br/download/attachments/317000767/Tutorial%20Homologa%C3%A7%C3%A3o%20do%20Banco%20Safra%20em%20correspondencia%20ao%20Bradesco.pdf?api=v2

```json
{"nome": "bancos", "rotina": "MATA070", "modulo": 6, "menu": ["Atualizações", "Cadastros", "Bancos"], "aba": "Bancos", "titulo": "", "aviso": "MV_1DUP", "releases": []}
```

---

# Faturamento (módulo 5)

## V1. tes: Tipos de Entrada e Saída (MATA080)

| | |
|---|---|
| Rotina | MATA080 |
| Menu | **a confirmar no lab** (esperado Atualizações > Cadastros > Tipos de Entrada e Saída) |
| Tabelas | SF4 |
| Tipo | leitura + visualizar; comparação 2510 x 2610 |
| Prioridade | **1** |

```bash
python /opt/plab/lab/tir/explorar_menu.py 2610 5 "Atualizações>Cadastros"
```

**Por que:** o TDN informa que, a partir da 12.1.2610 (12.1.2510 para clientes novos), os campos
fiscais deixam o cadastro de TES e o cálculo passa a ser só pelo Configurador de Tributos (T1). Na
TES ficam campos de integração como `F4_TIPO`, `F4_TESDV`, `F4_TESP3`, `F4_TESENV`, `F4_TESE3`,
`F4_CFPS` e `F4_OPEMOV`, e a TOTVS avisa que a lista pode mudar. É a tela com mais chance de quebrar
customização (pontos de entrada, validações, `ExecAuto` que preenche campo fiscal) na atualização.

**O que conferir na tela:**

1. Browse com a grade carregada.
2. **Visualizar** a primeira TES; capturar todas as abas; **Fechar** e conferir que sumiu.
3. Comparar as capturas da 2510 e da 2610: quais campos fiscais (ex.: "Calcula ICMS", `F4_ICM`;
   "PIS/COFINS", `F4_PISCOF`) aparecem em cada release. **Não afirmar** que um campo sumiu sem as
   duas capturas.

**Pré-checagem na base:**

```sql
BEGIN TRANSACTION READ ONLY;
SELECT COUNT(*), MIN(F4_CODIGO), MAX(F4_CODIGO) FROM <SF4> WHERE F4_FILIAL = :filial AND D_E_L_E_T_ = ' ';
SELECT X3_CAMPO, X3_TITULO, X3_FOLDER FROM SX3990 WHERE X3_ARQUIVO = 'SF4' AND D_E_L_E_T_ = ' ' ORDER BY X3_ORDEM;
ROLLBACK;
```

O resultado do SX3 nas duas releases é a evidência de dicionário da mudança.

**Riscos:** aviso sobre o Configurador ao abrir na 2610: se for informativo, `aviso`; se tiver botão
que migra ou grava, **parar** e registrar.

**Fontes:**

- TDN, "CFGTRIB - Campos que Permanecem no TES":
  https://tdn-homolog.totvs.com/display/public/PROT/CFGTRIB+-+Campos+que+Permanecem+no+TES
- Central TOTVS, "FIS - FISA170 - Campos da TES irá permanecer com a implantação do Configurador de
  Tributos": https://centraldeatendimento.totvs.com/hc/pt-br/articles/34900857950615
- TDN, "Tipos de Entrada e Saída (MATA080 - SIGATMK)": https://tdn.totvs.com/x/ycUBGQ
- TDN (homologação), campos `F4_ICM` e `F4_PISCOF`: https://tdn-homolog.totvs.com/x/AdogLg
- TDN, Central de Diagnóstico "Reforma Tributária - Configurações Mínimas": https://tdn.totvs.com/x/l4lLK

```json
{"nome": "tes", "rotina": "MATA080", "modulo": 5, "menu": ["Atualizações", "Cadastros", "Tipos de Entrada e Saída"], "aba": "Tipos de Entrada e Saída", "titulo": "", "passos": [{"acao": "visualizar", "linha": 1, "capturar": "formulario"}], "releases": []}
```

## V2. pedido-venda: Pedidos de Venda (MATA410)

| | |
|---|---|
| Rotina | MATA410 |
| Menu | Atualizações > Pedidos > Pedidos de Venda (fonte: TDN; rótulo varia entre "Pedido" e "Pedidos": **confirmar**) |
| Tabelas | SC5 (cabeçalho), SC6 (itens); SC9 (liberação) |
| Tipo | leitura + pesquisa + visualizar |
| Prioridade | **1** |

**Por que:** rotina mais usada do faturamento e a que mais recebe ponto de entrada (`MT410BRW`,
`M410AGRV`...). Na 2610 a TOTVS anunciou um agente de IA de liberação de crédito sobre pedidos de
venda (notícia), e o pedido calcula os tributos da reforma pelo Configurador.

**O que conferir na tela:**

1. Browse com a grade carregada.
2. **Pesquisar** pelo número de um pedido da pré-checagem; conferir o número na linha posicionada.
3. **Visualizar**: mesmo número e cliente do SQL, ao menos 1 item; **Fechar** e conferir que sumiu.
4. Não abrir "Planilha financeira" (não confirmei que não grava) nem "Prep. Doc. Saída" (gera nota).

**Pré-checagem na base:**

```sql
BEGIN TRANSACTION READ ONLY;
SELECT C5_NUM, C5_CLIENTE, C5_LOJACLI, C5_EMISSAO FROM <SC5>
 WHERE C5_FILIAL = :filial AND D_E_L_E_T_ = ' ' ORDER BY C5_NUM LIMIT 5;
SELECT C6_NUM, COUNT(*) AS itens FROM <SC6>
 WHERE C6_FILIAL = :filial AND D_E_L_E_T_ = ' ' GROUP BY C6_NUM ORDER BY C6_NUM LIMIT 5;
ROLLBACK;
```

SC5 vazia → só o browse, sem pesquisa. **Não crie pedido.**

**Riscos:** pesquisa no WebApp pode autocompletar ou truncar: ler de volta o valor digitado.

**Fontes:** TDN, árvore do Faturamento (MATA410, SC5/SC6, Atualizações / Pedidos):
https://tdn.totvs.com/x/X4Vn ; M410AGRV https://tdn.totvs.com/x/joRn ; MTA410E
https://tdn.totvs.com/x/hoVn ; boletim "Melhoria Liberação de Pedidos":
https://tdn.totvs.com.br/download/attachments/63276049/FAT_BT_Melhoria%20Liberacao%20de%20Pedidos_TGSVUD.pdf?api=v2 ;
notícia sobre o agente de crédito da 2610: https://www.letsmoney.com.br/ia/totvs-agentes-ia-backoffice-protheus/

```json
{"nome": "pedido-venda", "rotina": "MATA410", "modulo": 5, "menu": ["Atualizações", "Pedidos", "Pedidos de Venda"], "aba": "Pedidos de Venda", "titulo": "", "passos": [{"acao": "pesquisar", "valor_de": "pre-checagem C5_NUM"}, {"acao": "visualizar", "conferir": ["C5_NUM", "C5_CLIENTE"], "capturar": "formulario"}], "releases": []}
```

## V3. liberacao-estoque: Liberação de Estoque (MATA455)

| | |
|---|---|
| Rotina | MATA455 |
| Menu | Atualizações > Pedidos > Liberação Estoque (fonte: boletim do TDN) |
| Tabelas | SC9 (bloqueios de crédito e estoque) |
| Tipo | leitura |
| Prioridade | 2 |

**Por que:** o TDN explica que o MATA410 não mostra bloqueio de crédito ou estoque; isso só aparece
nas rotinas de liberação, sobre a SC9. Abrir a MATA455 confere a outra metade do fluxo de pedido
sem gravar. Liberação manual é "forçada" e ignora regras: o cenário **nunca** usa
Ações Relacionadas > Manual.

**O que conferir na tela:** browse (grade ou título) e legenda dos itens.

**Pré-checagem na base:**

```sql
BEGIN TRANSACTION READ ONLY;
SELECT C9_BLEST, C9_BLCRED, COUNT(*) FROM <SC9>
 WHERE C9_FILIAL = :filial AND D_E_L_E_T_ = ' ' GROUP BY C9_BLEST, C9_BLCRED;
ROLLBACK;
```

SC9 vazia (nenhum pedido liberado) → conferir por título.

**Riscos:** a rotina pode abrir pergunta de filtro antes do browse.

**Fontes:** TDN, boletim "Criação do Parâmetro MV_SELTNEW" (Atualizações/Pedidos/Liberação Estoque,
MATA455):
https://tdn.totvs.com.br/download/attachments/849112094/FAT_BT_Criacao_do_Parametro_MV_SELTNEW_BRA_THKUOT.pdf?api=v2 ;
TDN, "Liberações e Bloqueios do Pedido de Vendas" (MATA450, MATA450A, MATA455, MATA456, MATA460A,
SC9): https://tdn.totvs.com/x/RjS4Ew

```json
{"nome": "liberacao-estoque", "rotina": "MATA455", "modulo": 5, "menu": ["Atualizações", "Pedidos", "Liberação Estoque"], "aba": "", "titulo": "", "releases": []}
```

## V4. analise-credito-pedido: Análise de Crédito de Pedido (MATA450)

| | |
|---|---|
| Rotina | MATA450 |
| Menu | **a confirmar no lab** (esperado Atualizações > Pedidos, ao lado da Liberação Estoque) |
| Tabelas | SC9 |
| Tipo | leitura |
| Prioridade | 2 |

**Por que:** é a tela que o agente de liberação de crédito anunciado para a 2610 substitui ou
apoia (notícia). Abrir nas duas releases mostra se a 2610 mudou a tela ou o menu (ex.: novo item na
"Central de Ia", que existe no menu de Compras da 2610).

**O que conferir na tela:** browse ou pergunta inicial; **Cancelar** se a pergunta for de
processamento. Não liberar nem rejeitar.

**Pré-checagem:** a mesma do V3 (`C9_BLCRED`).

**Riscos:** a 2610 pode trazer um aviso ou convite para o agente de IA: registrar o texto, não
aceitar.

**Fontes:** TDN, "Liberações e Bloqueios do Pedido de Vendas": https://tdn.totvs.com/x/RjS4Ew ;
notícia: https://www.letsmoney.com.br/ia/totvs-agentes-ia-backoffice-protheus/

```json
{"nome": "analise-credito-pedido", "rotina": "MATA450", "modulo": 5, "menu": ["Atualizações", "Pedidos", "Análise Crédito Pedido"], "aba": "", "titulo": "", "releases": []}
```

Item de menu é suposição.

## V5. condicao-pagamento: Condição de Pagamento (MATA360), com gravação opcional

| | |
|---|---|
| Rotina | MATA360 |
| Menu | **a confirmar no lab** (esperado Atualizações > Cadastros > Condição de Pagamento) |
| Tabelas | SE4 (por conhecimento de uso; **a confirmar no SX2**) |
| Tipo | leitura; **grava** opcional (Parte B) |
| Prioridade | 3 |

**Por que:** usada em pedido de venda, pedido de compra e títulos; o TDN documenta tipos de
condição (ex.: tipo B, que combina vencimentos) e a inativação com movimentos pendentes.

**Parte A (leitura):** browse; **Visualizar** a primeira condição.

**Parte B (grava; só com autorização):** incluir condição com código inexistente (ex.: `ZZ9`,
conferido por SQL), descrição "LAB TESTE", tipo 1; conferir 1 linha nova; **excluir** pela MATA360;
conferir SE4 igual ao baseline. Se sobrar resto: `plab down <rel> --volumes` + `plab up <rel>`.

**Pré-checagem na base:**

```sql
BEGIN TRANSACTION READ ONLY;
SELECT COUNT(*) FROM <SE4> WHERE E4_FILIAL = :filial AND D_E_L_E_T_ = ' ';
SELECT E4_CODIGO FROM <SE4> WHERE E4_FILIAL = :filial AND E4_CODIGO LIKE 'ZZ%';
ROLLBACK;
```

**Fontes:** TDN (homologação), "Type B (MATA360 - SIGAFAT)": https://tdn-homolog.totvs.com/x/RFiaHg ;
nota TOTVS sobre inativar condição de pagamento com movimentos pendentes (no mesmo resultado de
busca, página a reabrir).

```json
{"nome": "condicao-pagamento", "rotina": "MATA360", "modulo": 5, "menu": ["Atualizações", "Cadastros", "Condição de Pagamento"], "aba": "", "titulo": "", "passos": [{"acao": "visualizar", "linha": 1, "capturar": "formulario"}], "releases": []}
```

---

# Transversal fiscal (fora da contagem)

## T1. configurador-tributos: Configurador de Tributos (FISA170)

| | |
|---|---|
| Rotina | FISA170 |
| Módulo | 9 Livros Fiscais |
| Menu | Atualizações > Facilitadores > Configurador de Tributos (fonte: TDN, release 12.1.22.10) |
| Tabelas | F2B, CIN, F27, F28, F29 (material CFGTRIB de compartilhamento; **a confirmar no SX2**) |
| Tipo | leitura |

**Por que:** é onde IBS, CBS e IS são parametrizados e, na 2610, o único lugar do cálculo fiscal
(V1). Defeito aqui afeta pedido, nota de entrada e de saída.

**O que conferir na tela:** a rotina abre sem erro e mostra a tela inicial (pode não ser browse
comum; usar `titulo` se não houver grade). Simuladores e importação de tabelas oficiais ficam fora
(podem gravar). Pergunta com "Sim/Confirmar" que grave: **Não/Cancelar** e registrar.

```bash
python /opt/plab/lab/tir/explorar_menu.py 2610 9 "Atualizações>Facilitadores" "Configurador de Tributos"
```

**Pré-checagem na base:**

```sql
BEGIN TRANSACTION READ ONLY;
SELECT X2_CHAVE, X2_NOME, X2_ARQUIVO, X2_MODO FROM SX2990
 WHERE X2_CHAVE IN ('F2B','CIN','F27','F28','F29') AND D_E_L_E_T_ = ' ';
SELECT COUNT(*) FROM <F2B> WHERE F2B_FILIAL = :filial AND D_E_L_E_T_ = ' ';
ROLLBACK;
```

**Riscos:** módulo 9 nunca foi aberto pelo runner (confirmar que `pw.sessao(pg, 9)` acha o módulo);
compatibilizador ou procedure exigidos ao abrir = bloqueio.

**Fontes:** TDN, "Release 12.1.22.10": https://tdn.totvs.com/x/bRnlLQ ; Central de Diagnóstico
"Reforma Tributária - Configurações Mínimas": https://tdn.totvs.com/x/l4lLK ; material CFGTRIB de
compartilhamento (trecho da busca): https://tdn.totvs.com/x/5SApK ; TOTVS Espaço Legislação,
"Momento Legislação Protheus" (dez/2025):
https://midias-sites.totvs.com/espacolegislacao/wp-content/uploads/2025/12/Momento-Legislacao-Protheus.pdf

```json
{"nome": "configurador-tributos", "rotina": "FISA170", "modulo": 9, "menu": ["Atualizações", "Facilitadores", "Configurador de Tributos"], "aba": "Configurador de Tributos", "titulo": "", "releases": []}
```

---

## Priorização

Critério, nesta ordem:

1. **Dá para rodar já com o runner atual** (só browse) ou o dado está conferido no lab.
2. **Menu confirmado** em fonte ou no lab (menos tentativa e erro com o `explorar_menu.py`).
3. **Valor para a 2610**: tela que muda entre 2510 e 2610 (TES, Configurador, compensação,
   inventário) ou que mais recebe customização.
4. **Risco**: leitura antes de grava; grava só depois que a leitura do mesmo cenário passou.

Rodar primeiro (1 ou 2 por módulo):

| Módulo | Primeiro | Segundo | Motivo |
|---|---|---|---|
| Compras | C2 documento-entrada | C1 pedido-compra-visualizar | C2 roda hoje (só browse, menu na fonte e pasta no lab); C1 tem dado conhecido (000001, 14 itens) e é o primeiro "visualizar" com resultado exato |
| Estoque | E1 movimentos-internos | E3 inventario (Parte A) | E1 é o único com menu confirmado em fonte; E3 é a mudança citada para a 2610 e prepara a única gravação segura do módulo |
| Financeiro | F1 movimentos-bancarios | F2 posicao-cliente | F1 roda hoje (menu na fonte, mesmo `aviso` do FINA040); F2 é a consulta em tela com dado garantido (SE1 tem títulos) |
| Faturamento | V1 tes | V2 pedido-venda | V1 é a maior mudança da 2610 (campos fiscais saindo da TES); V2 é a rotina mais usada e testa pesquisa + visualizar |

Os 4 "primeiros" só abrem browse e podem entrar no `cenarios.json` já (com `releases` vazia),
depois do `explorar_menu.py`. Os "segundos" dependem da chave `passos`.

## Temas da 2610 que ficaram de fora, e por quê

- **Nova Home / SmartX.** Sem página técnica do TDN encontrada. Se a Home nova aparecer, o efeito é
  no TIR (chave `NewHome` da EngPro) e no `pw.sessao`, não num cenário de rotina.
- **Fim do c-tree.** Sem fonte primária ligando a 2610 ao fim do c-tree. A pré-checagem comum
  (SX2/SX3 no banco) mostra se o dicionário desta base está no banco.
- **Stored procedures.** Fontes secundárias citam instalação automática de procedures na 2610; não
  confirmei no TDN. Todos os cenários tratam a janela "Incompatibilidade" como bloqueio, como o
  FINA050.
- **Documento de saída (MATA460A/MATA461).** Fora: gerar nota grava em vários lugares (SF2, SD2,
  SE1, livros, estoque) e não tem reversão simples.
- **Central de Ia e Controle Orçamentário** (menu de Compras só na 2610, conferido no lab): bons
  candidatos à fase 3, mas sem fonte TOTVS lida nesta pesquisa.
- **Fontes secundárias sobre a 2610** (para orientar, não para afirmar; lidas pelo trecho indexado):
  https://www.2fconsultoria.com.br/2026/10/totvs-protheus-12-1-2610-novidades-e-atualizacao/ ,
  https://erpworks.com.br/conteudos/protheus-12-1-2610-o-que-muda-tes-requisitos/ ,
  https://elewa.com.br/2026/09/15/protheus-12-1-2610-tes-configurador-de-tributos/ . Página oficial
  citada por elas, não aberta nesta sessão: https://protheus-release.totvs.io/2610

## Integração com a EngPro `tir-test-generator`

Cada cenário pode virar suíte TIR de três arquivos (`{ROTINA}TESTCASE.py`, `{ROTINA}TESTSUITE.py`,
config em runtime), com `Webapp` (todas as rotinas acima são browse legado/MVC, não SmartX nativo).
Enquanto o `Setup` do TIR não concluir no WebApp 26 ([totvs/tir#2169](https://github.com/totvs/tir/issues/2169)),
a execução segue pelo Playwright. Pontos para o pedido à EngPro:

- `Program("<ROTINA>")` com o módulo do cenário;
- passos "visualizar" via `SetButton("Visualizar")` e `CheckResult` no campo-chave, lendo de volta o
  valor (`GetValue`), nunca concluindo só por ausência de exceção;
- Help esperado (C5) como verificação explícita da mensagem, não como erro genérico;
- partes "grava" (C3, E3, F3, V5) fora da geração automática: suíte que grava só com autorização,
  com a reversão no `tearDown`, cuja falha aparece no resultado.

## Próximos passos (na máquina com o lab)

1. Rodar os `explorar_menu.py` de cada módulo nas duas releases e corrigir `menu`, `aba`, `titulo`
   e, onde marcado, `rotina`.
2. Rodar as pré-checagens SQL e anotar as quantidades no próprio cenário.
3. Incluir C2, E1, F1 e V1 (só browse) no `cenarios.json` com `"releases": []`, rodar
   `lab cenarios <rel> <nome>` e só então acrescentar a release.
4. PR à parte para a chave `passos`; depois, se o dono autorizar, PR do script das partes "grava".
