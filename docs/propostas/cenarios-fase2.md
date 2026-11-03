# Cenários da fase 2: proposta

author: daniel.montagna
Pesquisa: 03/11/2026. Situação: **proposta, nada executado**. Nenhum cenário abaixo foi rodado no
lab; todos entram com `"releases": []` e só ganham release depois de passar com evidência
(regra de `cenarios/README.md`).

## Como ler este documento

- **Confirmado na fonte**: o item (rotina, menu, tabela) aparece no texto de uma página TOTVS
  (TDN ou Central de Atendimento) citada na seção do cenário.
- **A confirmar no lab**: não achei fonte primária, ou a fonte é antiga. Antes de criar a entrada
  no JSON, rode o explorador de menu (somente leitura) no container `lab`:

  ```bash
  python /opt/plab/lab/tir/explorar_menu.py <rel> <modulo> "Atualizações>..." [item]
  ```

  Ele lista os itens do caminho e, com `[item]`, abre a rotina e mostra abas, títulos e se a grade
  carregou.
- **Limite desta pesquisa**: a sessão em que este documento foi escrito não alcançava
  `tdn.totvs.com`, `centraldeatendimento.totvs.com` nem `protheus-release.totvs.io` (bloqueio de
  rede). As fontes TOTVS foram lidas pelo trecho que o buscador indexou, não pela página aberta.
  Por isso cada fonte traz a data de acesso e o que foi lido nela. Reabra as páginas no navegador
  antes de promover um cenário.
- Nomes de campo (`F4_CODIGO`, `C5_NUM` etc.) seguem o padrão de prefixo do Protheus, mas não foram
  conferidos no dicionário do lab. A pré-checagem começa sempre pelo SX2/SX3 da base.

## Resumo

| # | Nome | Rotina | Módulo | Tipo | Por que entra |
|---|---|---|---|---|---|
| 1 | tes | MATA080 | 5 Faturamento (a confirmar) | leitura + **visualizar** registro | Na 2610 os campos fiscais saem da TES e vão para o Configurador de Tributos: é a tela que mais muda entre 2510 e 2610 |
| 2 | configurador-tributos | FISA170 | 9 Livros Fiscais | leitura | Ponto central da Reforma Tributária (IBS/CBS) no Protheus |
| 3 | pedido-venda | MATA410 | 5 Faturamento | leitura + **pesquisa e visualizar** | Rotina mais usada do faturamento; alvo do agente de liberação de crédito anunciado na 2610 |
| 4 | documento-entrada | MATA103 | 2 Compras | leitura | Porta de entrada fiscal; depende da TES e do cálculo de tributos |
| 5 | pedido-compra-alcada | MATA121 + MATA094 | 2 Compras | leitura; **grava** só se a base não tiver documento com alçada | Sugestão recebida na divulgação; testa o fluxo de aprovação |

Os cenários 1 e 3 vão além de "abrir browse". O cenário 5 é o único que pode gravar, e só como
plano B, com reversão descrita.

## Requisito comum: o runner atual só abre browse

`lab cenarios` lê do JSON apenas `nome`, `modulo`, `menu`, `aba`, `titulo`, `aviso` e `releases`
(`lab/bin/lib/cenarios.sh`) e o `smoke_ui.py` só confere título ou grade. Para os passos "visualizar"
e "pesquisar" proponho uma chave opcional `passos`, **ainda não implementada**. Como o `jq` do runner
ignora chaves que não conhece, uma entrada com `passos` roda hoje como leitura simples de browse.
Implementar `passos` é trabalho de outro PR (script + skill), fora deste.

Regras para esses passos, já seguidas pelos cenários existentes:

- só botões de leitura: **Pesquisar**, **Visualizar**, **Fechar**/**Cancelar**. Nunca Incluir,
  Alterar, Excluir, Copiar nem Confirmar;
- todo clique que fecha diálogo precisa de pós-condição (o diálogo sumiu), como em
  `references/tir.md`, "Complemento Playwright";
- sair sempre por "Log Off → Finalizar".

## Pré-checagem comum na base (somente leitura)

Rode em transação somente leitura no PostgreSQL da release (porta do `.env`; usuário e senha do
banco ficam no container, nunca em argumento):

```sql
BEGIN TRANSACTION READ ONLY;
-- 1) nome físico e modo de compartilhamento de cada tabela do cenário (empresa 99)
SELECT X2_CHAVE, X2_ARQUIVO, X2_MODO, X2_MODOUN, X2_MODOEMP
  FROM SX2990
 WHERE X2_CHAVE IN ('SF4','SC5','SC6','SF1','SD1','SC7','SCR','SAL','SAK','F2B','CIN','F27','F28')
   AND D_E_L_E_T_ = ' ';
-- 2) campos que a consulta vai usar existem?
SELECT X3_ARQUIVO, X3_CAMPO, X3_TAMANHO
  FROM SX3990
 WHERE X3_CAMPO IN ('F4_CODIGO','F4_TIPO','C5_NUM','C6_NUM','F1_DOC','D1_DOC','C7_NUM','CR_NUM')
   AND D_E_L_E_T_ = ' ';
ROLLBACK;
```

- Se `SX2990` não existir, o dicionário não está no banco nesta base: registre e confira pelo
  Configurador antes de seguir. Não presuma nome físico.
- Filial: `X2_MODO = 'C'` (compartilhada) usa filial em branco com o tamanho do campo `*_FILIAL`;
  `'E'` (exclusiva) usa `01`. Nas consultas abaixo, `:filial` é esse valor.
- Toda consulta de negócio filtra `D_E_L_E_T_ = ' '` e a filial. Use o nome físico vindo de
  `X2_ARQUIVO` (abaixo escrito como `<SF4>` etc.).

---

## 1. tes: Tipos de Entrada e Saída (MATA080)

**Rotina:** MATA080, tabela SF4.
**Módulo:** 5 Faturamento (a confirmar no lab; a TES também aparece em Compras e Livros Fiscais).
**Menu:** Atualizações > Cadastros > Tipos de Entrada e Saída (**a confirmar no lab**; não achei
o caminho no texto das fontes):

```bash
python /opt/plab/lab/tir/explorar_menu.py 2610 5 "Atualizações>Cadastros"
```

**Por que:** o TDN informa que, a partir da 12.1.2610 (12.1.2510 para clientes novos), os campos
fiscais deixam o cadastro de TES e o cálculo de tributos passa a ser feito só pelo Configurador de
Tributos. Na TES ficam campos de integração entre módulos, como `F4_TIPO`, `F4_TESDV`, `F4_TESP3`,
`F4_TESENV`, `F4_TESE3`, `F4_CFPS` e `F4_OPEMOV`, e a própria TOTVS avisa que a lista pode mudar.
É a tela com mais chance de quebrar customização (pontos de entrada, validações, `ExecAuto` que
preenche campo fiscal) na atualização. Rodar o mesmo cenário nas duas releases mostra a diferença
lado a lado.

**O que conferir na tela:**

1. Browse abre com a grade carregada (título do browse a confirmar no lab; até lá, `titulo` vazio).
2. Passo de leitura: posicionar na primeira linha, **Visualizar**, capturar as abas e os campos do
   formulário, **Fechar** e conferir que o formulário sumiu.
3. Comparar a captura da 2510 com a da 2610: registrar quais campos fiscais (ex.: "Calcula ICMS",
   `F4_ICM`; "PIS/COFINS", `F4_PISCOF`) aparecem em cada release. **Não afirmar** que um campo sumiu
   sem a captura das duas.

**Pré-checagem na base:**

```sql
BEGIN TRANSACTION READ ONLY;
SELECT COUNT(*) AS qtd, MIN(F4_CODIGO) AS primeira, MAX(F4_CODIGO) AS ultima
  FROM <SF4> WHERE F4_FILIAL = :filial AND D_E_L_E_T_ = ' ';
-- campos fiscais ainda no dicionário? (diferença 2510 x 2610)
SELECT X3_CAMPO, X3_TITULO, X3_USADO, X3_FOLDER
  FROM SX3990 WHERE X3_ARQUIVO = 'SF4' AND D_E_L_E_T_ = ' ' ORDER BY X3_ORDEM;
ROLLBACK;
```

Esperado: ao menos 1 TES (a base de demonstração costuma trazer várias; confirmar). O resultado do
SX3 nas duas releases é a evidência de dicionário da mudança; o `X3_USADO` codificado não deve ser
interpretado sem conferir na tela.

**Riscos:**

- O MATA080 pode abrir um aviso sobre o Configurador de Tributos na 2610. Se for só informativo,
  use a chave `aviso` com um trecho do texto; se tiver botão que grava ou migra, **pare** e registre.
- A tela de visualização pode ser MVC com abas; capture todas antes de concluir.
- Diálogo "Moedas" no primeiro acesso do dia: Cancelar (já tratado pelo runner).

**Fontes (acesso em 03/11/2026, pelo trecho indexado):**

- TDN, "CFGTRIB - Campos que Permanecem no TES" (lista de campos e aviso de que pode mudar):
  https://tdn-homolog.totvs.com/display/public/PROT/CFGTRIB+-+Campos+que+Permanecem+no+TES
- Central TOTVS, "FIS - FISA170 - Campos da TES irá permanecer com a implantação do Configurador de
  Tributos":
  https://centraldeatendimento.totvs.com/hc/pt-br/articles/34900857950615
- TDN, "Tipos de Entrada e Saída (MATA080 - SIGATMK)" (rotina e tabela; página de 2018):
  https://tdn.totvs.com/x/ycUBGQ
- TDN, campos da TES como `F4_ICM` e `F4_PISCOF` (cópia de homologação): https://tdn-homolog.totvs.com/x/AdogLg
- TDN, Central de Diagnóstico "Reforma Tributária - Configurações Mínimas" (índice CFGTRIB, cita as
  páginas de campos descontinuados e campos que permanecem): https://tdn.totvs.com/x/l4lLK

**Rascunho JSON:**

```json
{"nome": "tes", "rotina": "MATA080", "modulo": 5, "menu": ["Atualizações", "Cadastros", "Tipos de Entrada e Saída"], "aba": "Tipos de Entrada e Saída", "titulo": "", "passos": [{"acao": "visualizar", "linha": 1, "capturar": "formulario"}], "releases": []}
```

`menu` e `aba` são suposições até o `explorar_menu.py` confirmar o rótulo exato.

---

## 2. configurador-tributos: Configurador de Tributos (FISA170)

**Rotina:** FISA170.
**Módulo:** 9 Livros Fiscais (SIGAFIS).
**Menu:** Atualizações > Facilitadores > Configurador de Tributos (confirmado no TDN, nota da
release 12.1.22.10; confirmar o rótulo na 2610 e na 2510).
**Tabelas:** F2B, CIN, F27, F28 e F29 citadas no material CFGTRIB de compartilhamento de tabelas
(F2B, CIN, F27 e F28 com o mesmo nível de compartilhamento). Não achei qual tela cadastra cada
uma: **a confirmar no SX2 do lab**.

**Por que:** é onde a Reforma Tributária (IBS, CBS, IS) é parametrizada no Protheus e, na 2610,
passa a ser o único lugar do cálculo fiscal (ver cenário 1). Um defeito ou mudança de layout aqui
afeta pedido, nota de entrada e de saída. Também é a rotina que o time de sustentação vai abrir
para diagnosticar cálculo errado depois da atualização.

**O que conferir na tela:**

1. A rotina abre sem erro e mostra a tela inicial do configurador. Ela pode não ser um browse
   comum: o `explorar_menu.py` diz se há grade e quais títulos aparecem. Se não houver grade, use
   `titulo` com o texto que aparecer.
2. Nada é clicado além de abrir e fechar. Simuladores e importação de tabelas oficiais ficam fora
   (podem gravar).

```bash
python /opt/plab/lab/tir/explorar_menu.py 2610 9 "Atualizações>Facilitadores" "Configurador de Tributos"
python /opt/plab/lab/tir/explorar_menu.py 2510 9 "Atualizações>Facilitadores" "Configurador de Tributos"
```

**Pré-checagem na base:**

```sql
BEGIN TRANSACTION READ ONLY;
SELECT X2_CHAVE, X2_NOME, X2_ARQUIVO, X2_MODO FROM SX2990
 WHERE X2_CHAVE IN ('F2B','CIN','F27','F28','F29') AND D_E_L_E_T_ = ' ';
-- quantas regras existem (nome físico do SX2; prefixo de campo de tabela não-S tem 3 letras)
SELECT COUNT(*) FROM <F2B> WHERE F2B_FILIAL = :filial AND D_E_L_E_T_ = ' ';
ROLLBACK;
```

Esperado: tabelas presentes no SX2 das duas releases. A quantidade de regras na base de
demonstração é desconhecida; zero regras não reprova o cenário (ele confere a tela, não a
configuração), mas troca a conferência de "grade" para "título".

**Riscos:**

- A rotina pode pedir para rodar compatibilizador, importar tabela ou criar regra padrão ao abrir.
  Qualquer pergunta com "Sim/Confirmar" que grave: responder **Não/Cancelar** e registrar o texto.
- Pode haver stored procedure ou outro processo exigido (janela "Incompatibilidade"): tratar como
  bloqueio de ambiente, conforme `references/procedures.md`.
- Módulo 9 nunca foi aberto pelo runner; confirmar que `pw.sessao(pg, 9)` acha o módulo.

**Fontes (acesso em 03/11/2026, pelo trecho indexado):**

- TDN, "Release 12.1.22.10" (caminho Livros Fiscais > Atualizações > Facilitadores > Configurador de
  Tributos, FISA170): https://tdn.totvs.com/x/bRnlLQ
- TDN, Central de Diagnóstico "Reforma Tributária - Configurações Mínimas" (índice CFGTRIB: IBS, CBS,
  IS, perfis, campos do TES): https://tdn.totvs.com/x/l4lLK
- TDN, material CFGTRIB sobre compartilhamento de F2B/CIN/F27/F28 (trecho da busca; página exata a
  reabrir): https://tdn.totvs.com/x/5SApK
- TOTVS Espaço Legislação, "Momento Legislação Protheus" (dez/2025; vincular classificação
  tributária à regra de cálculo; simuladores):
  https://midias-sites.totvs.com/espacolegislacao/wp-content/uploads/2025/12/Momento-Legislacao-Protheus.pdf

**Rascunho JSON:**

```json
{"nome": "configurador-tributos", "rotina": "FISA170", "modulo": 9, "menu": ["Atualizações", "Facilitadores", "Configurador de Tributos"], "aba": "Configurador de Tributos", "titulo": "", "releases": []}
```

---

## 3. pedido-venda: Pedidos de Venda (MATA410)

**Rotina:** MATA410. **Tabelas:** SC5 (cabeçalho) e SC6 (itens); SC9 guarda a liberação.
**Módulo:** 5 Faturamento.
**Menu:** Atualizações > Pedidos > Pedidos de Venda. O caminho aparece no TDN, mas o rótulo final
vem como "Pedido de Venda" em uma fonte e "Pedidos de Venda" em outra: **confirmar no lab**.

```bash
python /opt/plab/lab/tir/explorar_menu.py 2610 5 "Atualizações>Pedidos"
```

**Por que:** é a rotina mais usada do faturamento e a que mais recebe ponto de entrada
(`MT410BRW`, `M410AGRV` e outros no TDN). Na 2610 a TOTVS anunciou um agente de IA de liberação de
crédito sobre pedidos de venda (notícia, não fonte técnica), e o pedido também passa a calcular os
tributos da reforma pelo Configurador. É o melhor candidato a "além do browse".

**O que conferir na tela:**

1. Browse com a grade carregada e legenda de status.
2. **Pesquisar** pelo número de um pedido existente (vindo da pré-checagem), conferir que a linha
   posicionada mostra esse número (ler o valor completo, não só "sem erro").
3. **Visualizar** o pedido: cabeçalho com o mesmo número e cliente da consulta SQL e ao menos 1 item
   na grade; capturar; **Fechar** e conferir que o formulário sumiu.
4. Não abrir "Planilha financeira" nem "Prep. Doc. Saída": a primeira é leitura, mas não confirmei
   que não grava; a segunda gera nota.

**Pré-checagem na base:**

```sql
BEGIN TRANSACTION READ ONLY;
SELECT C5_NUM, C5_CLIENTE, C5_LOJACLI, C5_EMISSAO
  FROM <SC5> WHERE C5_FILIAL = :filial AND D_E_L_E_T_ = ' '
 ORDER BY C5_NUM LIMIT 5;
SELECT C6_NUM, COUNT(*) AS itens
  FROM <SC6> WHERE C6_FILIAL = :filial AND D_E_L_E_T_ = ' '
   AND C6_NUM IN (SELECT C5_NUM FROM <SC5> WHERE C5_FILIAL = :filial AND D_E_L_E_T_ = ' ')
 GROUP BY C6_NUM ORDER BY C6_NUM LIMIT 5;
ROLLBACK;
```

Esperado: ao menos 1 pedido com 1 item ou mais. Se a SC5 estiver vazia, o cenário fica só no
browse (registre "sem pedido na base") e o passo de pesquisa não roda; **não crie pedido**.

**Riscos:**

- Filtro de browse por vendedor (`MT410BRW`) não existe na base padrão, mas em cliente pode esconder
  linhas: o teste confere o número pesquisado, não a quantidade de linhas.
- Pesquisa de browse no WebApp pode autocompletar ou truncar (problema visto no campo de ambiente
  do TIR): ler de volta o valor digitado antes de confirmar.
- Possível aviso da base ao abrir (como o MV_1DUP do financeiro): usar `aviso` se for informativo.

**Fontes (acesso em 03/11/2026, pelo trecho indexado):**

- TDN, árvore do Faturamento com "Pedidos de Venda (MATA410)", SC5/SC6 e caminho
  Atualizações / Pedidos: https://tdn.totvs.com/x/X4Vn
- TDN, ponto de entrada M410AGRV (SC6 via aCols/aHeader): https://tdn.totvs.com/x/joRn
- TDN, ponto de entrada MTA410E: https://tdn.totvs.com/x/hoVn
- TDN, boletim "Melhoria Liberação de Pedidos" (legenda: verde = sem SC9; MATA410 não mostra
  bloqueio de crédito/estoque):
  https://tdn.totvs.com.br/download/attachments/63276049/FAT_BT_Melhoria%20Liberacao%20de%20Pedidos_TGSVUD.pdf?api=v2
- Notícia (fonte secundária) sobre o agente de liberação de crédito da 2610:
  https://www.letsmoney.com.br/ia/totvs-agentes-ia-backoffice-protheus/

**Rascunho JSON:**

```json
{"nome": "pedido-venda", "rotina": "MATA410", "modulo": 5, "menu": ["Atualizações", "Pedidos", "Pedidos de Venda"], "aba": "Pedidos de Venda", "titulo": "", "passos": [{"acao": "pesquisar", "valor_de": "pre-checagem C5_NUM"}, {"acao": "visualizar", "conferir": ["C5_NUM", "C5_CLIENTE"], "capturar": "formulario"}], "releases": []}
```

---

## 4. documento-entrada: Documento de Entrada (MATA103)

**Rotina:** MATA103. **Tabelas:** SF1 (cabeçalho) e SD1 (itens).
**Módulo:** 2 Compras.
**Menu:** Atualizações > Movimentos > Documento Entrada (confirmado em boletim técnico do TDN;
confirmar o rótulo exato na 2610).

```bash
python /opt/plab/lab/tir/explorar_menu.py 2610 2 "Atualizações>Movimentos"
```

**Por que:** é a porta de entrada fiscal e de estoque, a rotina com mais ponto de entrada no
Compras (`SF1100I`, `SD1100I`, `MT103DNF`, `MT100AG`...) e a que sente primeiro a mudança da TES e
do Configurador de Tributos (cenários 1 e 2). Completa o par com `pedido-compra` (MATA121), já
proposto para o JSON.

**O que conferir na tela:** browse com a grade carregada (como os 6 cenários atuais). Sem visualizar
nesta fase: a visualização do documento de entrada monta abas fiscais e financeiras que convém
mapear antes com o `explorar_menu.py`.

**Pré-checagem na base:**

```sql
BEGIN TRANSACTION READ ONLY;
SELECT COUNT(*) AS docs FROM <SF1> WHERE F1_FILIAL = :filial AND D_E_L_E_T_ = ' ';
SELECT COUNT(*) AS itens FROM <SD1> WHERE D1_FILIAL = :filial AND D_E_L_E_T_ = ' ';
ROLLBACK;
```

Esperado: ao menos 1 documento, para que "grade carregada" faça sentido. Se a SF1 estiver vazia,
o browse abre vazio e o critério de grade falha: nesse caso conferir pelo título do browse
(`titulo`) e anotar "sem documento na base". Não lance nota para preencher a grade.

**Riscos:**

- Rotina que pode usar stored procedures em algumas operações; se abrir "Incompatibilidade",
  seguir `references/procedures.md` e registrar como bloqueio, como no FINA050 da 2610.
- Avisos de parâmetro ao abrir (como MV_1DUP no financeiro): usar `aviso` só se for informativo.
- O browse pode demorar mais que os cadastros (legenda calculada por linha); o tempo padrão do
  runner é 600 s por cenário.

**Fontes (acesso em 03/11/2026, pelo trecho indexado):**

- TDN, boletim "Desabilita Validação de Itens Utilizados no Documento de Entrada" (caminho
  Atualizações/Movimentos/Documento Entrada, SF1 e SD1):
  https://tdn.totvs.com/download/attachments/22479114/COM_Desabilita%20Validacao%20de%20Itens%20Utilizados%20no%20Documento%20de%20Entrada_TEXKUM.pdf?api=v2
- TDN, ponto de entrada SF1100I (após gravar SF1/SD1): https://tdn.totvs.com/x/8Ntc
- TDN, ponto de entrada SD1100I: https://tdn.totvs.com/x/7dtc
- TDN, ponto de entrada MT103DNF: https://tdn.totvs.com/x/Itxc

**Rascunho JSON:**

```json
{"nome": "documento-entrada", "rotina": "MATA103", "modulo": 2, "menu": ["Atualizações", "Movimentos", "Documento Entrada"], "aba": "Documento Entrada", "titulo": "", "releases": []}
```

---

## 5. pedido-compra-alcada: aprovação de pedido de compra (MATA121 + MATA094)

**Rotinas:** MATA121 (Pedidos de Compra, já proposta para o JSON) e MATA094 (Liberação de
Documentos). **Tabelas:** SC7 (pedido de compra), SCR (documentos com alçada; guarda bloqueio e
registro de aprovação), DBM (itens do documento sob alçada); cadastro de aprovadores e grupos
(SAK e SAL, **a confirmar no SX2**; não achei fonte TOTVS que os cite).
**Módulo:** 2 Compras.
**Menu da MATA094:** **a confirmar no lab** (não achei o caminho em fonte primária):

```bash
python /opt/plab/lab/tir/explorar_menu.py 2610 2 "Atualizações>Movimentos"
python /opt/plab/lab/tir/explorar_menu.py 2610 2 "Atualizações>Pedidos"
```

**Por que:** foi o cenário sugerido no único comentário do post de divulgação ("Pedido de Compra
com alçada", ver `STATUS.md`, Divulgação). Alçada é configuração que costuma quebrar em atualização
(pontos de entrada `MT094CPC`, `MT094CCR`; correções na `MATXALC`) e é o fluxo em que o time de
sustentação mais recebe chamado.

### Parte A: leitura (padrão)

1. Pré-checar se a base já tem documento com alçada.
2. Se tiver: abrir a MATA094, conferir a grade e **Visualizar** um documento (sem Aprovar, Estornar
   nem Rejeitar). Não grava.

```sql
BEGIN TRANSACTION READ ONLY;
SELECT CR_TIPO, CR_STATUS, COUNT(*) AS qtd
  FROM <SCR> WHERE CR_FILIAL = :filial AND D_E_L_E_T_ = ' '
 GROUP BY CR_TIPO, CR_STATUS;
SELECT COUNT(*) AS aprovadores FROM <SAK> WHERE AK_FILIAL = :filial AND D_E_L_E_T_ = ' ';
SELECT COUNT(*) AS grupos FROM <SAL> WHERE AL_FILIAL = :filial AND D_E_L_E_T_ = ' ';
ROLLBACK;
```

Os valores de `CR_TIPO` (PC, IP, AE, citados no TDN do `MT094CPC`) e de `CR_STATUS` não foram
confirmados no dicionário: leia o SX3/combo antes de interpretar.

### Parte B: **grava** (só se a Parte A não achar documento, e só com autorização registrada do dono)

Pré-requisitos: aprovador e grupo de aprovação já cadastrados na base. Se não houver, **não**
cadastrar nesta fase: isso já seriam três gravações, fora do limite. Registrar "base sem alçada" e
parar.

Plano:

1. Baseline (somente leitura): `MAX(C7_NUM)`, contagem de SC7 e SCR por filial, guardados na
   evidência.
2. Incluir 1 pedido de compra pela MATA121, com fornecedor e produto existentes, 1 item, valor
   acima do limite do grupo (para gerar SCR). Anotar número.
3. Conferir: SC7 com 1 pedido novo bloqueado; SCR com o documento do pedido novo.
4. MATA094: localizar o documento e **Visualizar**. Não aprovar.
5. **Reversão:** excluir o pedido pela MATA121 (Excluir). Conferir: SC7 e SCR do número anotado
   com `D_E_L_E_T_ = '*'` ou ausentes, e contagens ativas iguais ao baseline.
6. Se a reversão falhar ou deixar resto: `plab down 2610 --volumes` + `plab up 2610` (volta ao
   estado da imagem; depois rodar de novo `lab procedures 2610 08` para o FINA050) e registrar a
   falha no relatório.

Regras: rodar só na release escolhida pelo dono; nunca aprovar (aprovação grava SCR e libera o
pedido para outras rotinas); numeração consumida não volta, e isso é aceito por ser base de
laboratório.

**Riscos:**

- A alçada pode exigir parâmetros ligados (ex.: `MV_APRSCEC` para solicitação de compra, citado em
  fonte de terceiros). Não alterar parâmetro para fazer o teste passar: registrar e parar.
- Excluir pedido com alçada pode exigir estornar antes; se a MATA121 recusar, ir direto ao passo 6.
- Esta parte não entra no `cenarios.json`, que é só leitura: vira script próprio com flag explícita
  (como `lab procedures`), em outro PR.

**Fontes (acesso em 03/11/2026, pelo trecho indexado):**

- TDN, ponto de entrada MT094CPC (chamado no "Aprovar" da MATA094; tipos PC, IP e AE):
  https://tdn.totvs.com/pages/releaseview.action?pageId=286224513
- TDN, DMANMAT02-2006 "Liberação Documento, Ponto Entrada MT094CCR":
  https://tdn.totvs.com.br/pages/releaseview.action?pageId=306844678
- TDN, DMANMAT02-7926 "Alçadas Entidade Contábil PC..." (correção em MATXALC e MATA094; SCR):
  https://tdn.totvs.com/pages/releaseview.action?pageId=346495116
- Central TOTVS, "SIGACOM - Ciclo de vida - Rotina Liberação de Documentos (MATA097)" (troca da
  MATA097 pela MATA094; SCR e DBM):
  https://centraldeatendimento.totvs.com/hc/pt-br/articles/360036907834
- Terceiros (não primário, só para orientar a pré-checagem): https://tecnologia.bynem.com.br/mata094-liberacao-de-documentos/

**Rascunho JSON (só a Parte A):**

```json
{"nome": "liberacao-documentos", "rotina": "MATA094", "modulo": 2, "menu": ["Atualizações", "Movimentos", "Liberação de Documentos"], "aba": "Liberação de Documentos", "titulo": "", "passos": [{"acao": "visualizar", "linha": 1, "capturar": "formulario"}], "releases": []}
```

`menu` é suposição até o `explorar_menu.py` confirmar.

---

## Temas da 2610 que ficaram de fora, e por quê

- **Nova Home / SmartX.** A 2610 traz uma nova Home (notícias e consultorias). Não achei página
  técnica do TDN sobre ela. No lab o login já passa pela tela PO UI e cai no menu clássico; se a
  Home nova aparecer, o efeito é no TIR (chave `NewHome` da EngPro) e no `pw.sessao`, não num
  cenário de rotina. Sugestão: quando o TDN publicar, criar um cenário de "home" separado.
- **Fim do c-tree.** Não achei fonte primária ligando a 2610 ao fim do c-tree. A pré-checagem comum
  (SX2/SX3 no banco) já mostra se o dicionário desta base está no banco.
- **Stored procedures.** Fontes secundárias citam instalação automática de algumas procedures na
  2610; não confirmei no TDN. Os cenários 2 e 4 tratam a janela "Incompatibilidade" como bloqueio,
  como o FINA050.
- **Fontes secundárias sobre a 2610** (para orientar, não para afirmar; lidas pelo trecho indexado), acesso em 03/11/2026:
  https://www.2fconsultoria.com.br/2026/10/totvs-protheus-12-1-2610-novidades-e-atualizacao/ ,
  https://erpworks.com.br/conteudos/protheus-12-1-2610-o-que-muda-tes-requisitos/ ,
  https://elewa.com.br/2026/09/15/protheus-12-1-2610-tes-configurador-de-tributos/ . Página oficial
  citada por elas, não aberta nesta sessão: https://protheus-release.totvs.io/2610

## Integração com a EngPro `tir-test-generator`

Cada cenário pode virar suíte TIR de três arquivos (`{ROTINA}TESTCASE.py`, `{ROTINA}TESTSUITE.py`,
config em runtime), com `Webapp` (todas as rotinas acima são browse legado/MVC, não SmartX nativo).
Enquanto o `Setup` do TIR não concluir no WebApp 26 ([totvs/tir#2169](https://github.com/totvs/tir/issues/2169)),
a execução segue pelo Playwright. Pontos para o pedido à EngPro:

- `Program("MATA080")`, `Program("FISA170")` etc. com o módulo do cenário;
- passos "visualizar" via `SetButton("Visualizar")` e `CheckResult` no campo-chave, lendo de volta o
  valor (`GetValue`), nunca concluindo só por ausência de exceção;
- cenário 5 Parte B fora da geração automática: suíte que grava só com autorização e com o passo
  de reversão como `tearDown`, cuja falha aparece no resultado.

## Próximos passos (na máquina com o lab)

1. Rodar os `explorar_menu.py` acima nas duas releases e corrigir `menu`, `aba` e `titulo`.
2. Rodar as pré-checagens SQL e anotar as quantidades.
3. Incluir os cenários 2 e 4 (só browse) no `cenarios.json` com `"releases": []`, rodar
   `lab cenarios <rel> <nome>` e só então acrescentar a release.
4. Abrir PR à parte para a chave `passos` (cenários 1, 3 e 5A) e, se o dono autorizar, para o
   script da Parte B do cenário 5.
