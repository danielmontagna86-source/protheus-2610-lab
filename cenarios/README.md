# Cenários

Todos rodam dentro do container `lab`. Os de interface de `ui-smoke/` e `ui-leitura/` são **somente leitura**: entram, abrem a
rotina padrão, conferem o browse e saem pelo "Log Off → Finalizar". Nada é gravado: "Moedas" usa
Cancelar, "Novidades do Produto" usa Fechar e o aviso MV_1DUP da base é fechado com Esc.
A tela "Parametros" (Pergunte), quando o cenário pede, é confirmada com OK sem alterar nenhum
campo: isso só guarda as respostas padrão no perfil de perguntas do usuário, nenhum dado de negócio.
Os de `ui-gravacao/` são a exceção: gravam no banco do lab e só rodam com autorização e cópia da base.

| Pasta | O que é | Comando |
|---|---|---|
| `hello/` | `LABHELLO.prw` (CP1252 + CRLF) para provar a compilação | `lab compile <rel> /opt/plab/cenarios/hello/LABHELLO.prw` |
| `ui-smoke/` | smoke de interface (Playwright): MATA010 | `lab ui <rel>` |
| `ui-leitura/` | 31 cenários de leitura em `cenarios.json` | `lab cenarios <rel> [nome]` |
| `ui-gravacao/` | 4 cenários que **gravam** e revertem (inclui e exclui um registro de teste) | `lab gravacoes <rel> [nome]` (ver `ui-gravacao/README.md`) |
| `tir-smoke/` | a mesma MATA010 em TIR (bloqueada no WebApp 26, totvs/tir#2169) | `lab tir <rel> /opt/plab/cenarios/tir-smoke/SMOKETESTSUITE.py` |

## Cenários de leitura

| Nome | Rotina | Módulo | Menu | Conferência | 2610 | 2510 |
|---|---|---|---|---|---|---|
| produtos | MATA010 | 5 Faturamento | Atualizações > Cadastros > Produtos | título "Atualizacao de Produtos" | ok | ok |
| fornecedores | MATA020 | 2 Compras | Atualizações > Cadastros > Fornecedores | grade carregada | ok | ok |
| clientes | MATA030 / CRMA980 | 5 Faturamento | Atualizações > Cadastros > Clientes | grade carregada | ok | ok |
| contas-receber | FINA040 | 6 Financeiro | Atualizações > Contas a Receber > Contas a Receber | grade carregada | ok | ok |
| contas-pagar | FINA050 | 6 Financeiro | Atualizações > Contas a Pagar > Contas a Pagar | grade carregada | ok¹ | ok |
| pedido-compra | MATA121 | 2 Compras | Atualizações > Pedidos > Pedidos de Compra | grade carregada | ok² | ok² |
| liberar-documentos | MATA094 | 2 Compras | Atualizações > Liberação > Liberar de Documentos | Help A097APROV (Admin não é aprovador)² | ok | ok |
| documento-entrada | MATA103 | 2 Compras | Atualizações > Movimentos > Documento Entrada | grade carregada | ok | ok |
| solicitacao-compras | MATA110 | 2 Compras | Atualizações > Solicitações > Solicitação de Compras | grade carregada | ok | ok |
| cotacoes | MATA150 | 2 Compras | Atualizações > Cotações > Atualizar Cotações | Parametros + título "Atualizaçao Preços da Cotaçao"³ | não⁴ | ok |
| movimentacao-multipla | MATA241 | 4 Estoque | Atualizações > Movimentações > Internas > Movimentação Múltipla | grade carregada | ok | ok |
| transferencia-multipla | MATA261 | 4 Estoque | Atualizações > Movimentações > Internas > Transferência Múltipla | grade carregada | ok | ok |
| inventario | MATA270 | 4 Estoque | Atualizações > Movimentações > Internas > Inventário | Parametros + título "Digitaçäo do Inventário"³ ⁵ | ok | ok |
| documento-entrada-estoque | MATA103 | 4 Estoque | Atualizações > Movimentações > Fiscais > Documento de Entrada | grade carregada | ok | ok |
| movimentos-bancarios | FINA100 | 6 Financeiro | Atualizações > Movimento Bancario > Movimentos Bancários | grade carregada | ok | ok |
| naturezas | FINA010 | 6 Financeiro | Atualizações > Cadastros > Naturezas | grade carregada | ok | ok |
| compensacao-pagar | FINA340 | 6 Financeiro | Atualizações > Contas a Pagar > Compensação Contas a Pagar | grade carregada | ok | ok |
| bancos | MATA070 | 6 Financeiro | Atualizações > Cadastros > Bancos | grade carregada | ok | ok |
| tes | MATA080 | 5 Faturamento | Atualizações > Cadastros > Tipos de Entrada e Saída | grade carregada | ok | ok |
| pedido-venda | MATA410 | 5 Faturamento | Atualizações > Pedidos > Pedidos de Venda | grade carregada | ok | ok |
| liberacao-estoque | MATA455 | 5 Faturamento | Atualizações > Pedidos > Liberação de Estoque | Parametros + Help RECNO³ | ok | ok |
| analise-credito-pedido | MATA450 | 5 Faturamento | Atualizações > Pedidos > Análise de Crédito de Pedido de Venda | Parametros + título "Liberacao de Credito"³ | ok | ok |
| condicao-pagamento | MATA360 | 5 Faturamento | Atualizações > Cadastros > Condições de Pagamento | grade carregada | ok | ok |
| pedido-compra-visualizar | MATA121 | 2 Compras | Atualizações > Pedidos > Pedidos de Compra | grade + Visualizar "Pedido de Compra - VISUALIZAR"⁶ | ok | ok |
| tes-visualizar | MATA080 | 5 Faturamento | Atualizações > Cadastros > Tipos de Entrada e Saída | grade + Visualizar "Visualização de TES"⁶ | ok | ok |
| pedido-venda-visualizar | MATA410 | 5 Faturamento | Atualizações > Pedidos > Pedidos de Venda | grade + Visualizar "Pedidos de Venda - VISUALIZAR"⁶ | ok | ok |
| condicao-pagamento-visualizar | MATA360 | 5 Faturamento | Atualizações > Cadastros > Condições de Pagamento | grade + Visualizar "Condiçäo de Pagamento - VISUALIZAR"⁶ | ok | ok |
| naturezas-visualizar | FINA010 | 6 Financeiro | Atualizações > Cadastros > Naturezas | grade + Visualizar "Naturezas - VISUALIZAR"⁶ | ok | ok |
| consulta-produto | MATC050 (a confirmar) | 4 Estoque | Consultas > Cadastros > Produto | Parametros + grade carregada | ok | ok |
| kardex-diario | a confirmar | 4 Estoque | Consultas > Cadastros > Kardex Diário | Parametros + grade carregada | ok | ok |
| posicao-cliente | FINC010 | 6 Financeiro | Consultas > Contas a Receber > Posição de Cliente | grade carregada | ok | ok |

¹ Na 2610 exige o processo de stored procedures 08 atualizado: rode
`lab procedures 2610 08` e depois `plab restart 2610` (ver README principal, Problemas conhecidos).

² Incluído em 03/11/2026 por sugestão da comunidade (Pedido de Compra com alçada). A base de
demonstração das duas releases tem um pedido (000001, 14 itens) já liberado (`C7_CONAPRO = L`),
nenhum aprovador e nenhum documento de alçada (`SCR` vazia; a `SAL` nem existe no banco), e
`MV_APRPCEC` = F. Por isso o cenário só confere o browse: testar alçada exige cadastrar grupo e
aprovadores, o que grava na base e fica fora dos cenários de leitura. "Liberar de Documentos" abre
com o Help A097APROV (sem texto de problema) para o Admin nas duas releases (cenário
`liberar-documentos`, 04/11/2026); a `SAK` não tem aprovadores, o que é a causa provável, ainda
não confirmada.

³ A base de demonstração não tem cotações, inventário nem pedidos liberados. Essas rotinas abrem a
tela "Parametros" antes do browse e, depois dela, mostram o browse vazio (conferido pelo título) ou,
na Liberação de Estoque, o Help RECNO "Não existem registros no arquivo em pauta" (fechado com
"Fechar"). As 25 entradas a partir de liberar-documentos vêm da proposta
`docs/propostas/cenarios-fase2.md` e foram conferidas nas duas releases em 04/11/2026.

⁴ Na 2610 a Atualizar Cotações (MATA150) abre o "Comunicado Ciclo de Vida de Software - TOTVS
Linha Protheus": rotina descontinuada, manutenção encerrada em 30/06/2025, com os botões
"Confirmar" e "Descubra o novo". Na 2510 o comunicado não aparece. O cenário não clica no
comunicado e fica confirmado só na 2510; a diferença entre as releases é o resultado (04/11/2026).

⁵ O título vem da rotina como "Digitaçäo" (com "ä", não "ã"); na tela parece igual. O cenário
compara o texto exato.

⁶ "Visualizar" abre o primeiro registro do browse em modo de visualização, captura a tela
(`NN-visualizar.png`), fecha com "Cancelar" ou "Fechar" (nunca "Confirmar") e confere que o browse
voltou. No pedido de compra a captura mostra o pedido 000001 com os 14 itens; o cenário não conta
as linhas, só confere que o formulário abriu e fechou.

"Grade carregada" quer dizer que a grade do browse tem linhas e está de fato visível na tela.
A checagem usa o elemento no centro da grade, para não aceitar uma tela em branco.

## Mapa e diferenças de menu

`lab menus <rel> <modulo> [caminho]` percorre o menu do módulo abrindo só grupos (itens com
"(N)" no fim) e nunca uma rotina, e grava `evidencias/<rel>/menus/<modulo>.json`. Sai pelo
"Log Off → Finalizar" mesmo se falhar ou estourar o limite. `lab menus-diff <modulo>` compara os
JSON das duas releases e grava `evidencias/menus-diff-<modulo>.md` com os itens só na 2610, só na
2510 e os grupos com contagem diferente. Exemplo com Compras:

```bash
docker exec plab-lab-lab-1 lab menus 2610 2
docker exec plab-lab-lab-1 lab menus 2510 2
docker exec plab-lab-lab-1 lab menus-diff 2
```

Caminho padrão `Atualizações`; use `todos` para incluir Consultas, Relatórios e Miscelânea.
Limites em `PLAB_MENUS_PROFUNDIDADE` (5) e `PLAB_MENUS_TEMPO` (1200 s). Contrato:
`specs/001-protheus-2610-lab/contracts/lab-menus.md`.

## Resultado e evidências

`lab cenarios <rel>` termina com `cenarios <rel>: total=N falhas=F pulados=P repeticoes=R` e sai com código 0
só se não houver falha. Cada cenário grava `<nome>.out` e as capturas em
`evidencias/<rel>/cenarios-<data>/<nome>/`. As capturas limpam o formulário de login antes de
serem tiradas, para nenhuma senha aparecer em imagem.

Para acrescentar um cenário, inclua uma entrada em `ui-leitura/cenarios.json` com `releases`
vazia, rode `lab cenarios <rel> <nome>` e só acrescente a release depois de passar.

Campos opcionais de cada entrada: `titulo` (texto do título do browse; vazio = conferir a grade),
`aviso` (trecho de aviso informativo a fechar com Esc, ex.: `MV_1DUP`), `parametros` (`"ok"` =
confirmar a tela "Parametros" com os valores padrão), `visualizar` (`true` = abrir o primeiro
registro em Visualizar e fechar) e `help` (código do Help esperado no lugar do
browse, ex.: `RECNO`; o cenário passa se o Help aparecer e for fechado).

Repetição: um cenário só é refeito, uma vez e desde o login, quando a interface nova da 2610 mostra
"Não foi possível enviar a requisição" na tela de sessão e a sessão não abre (intermitente, visto em
03 e 04/11/2026, causa não confirmada). A linha do cenário diz que foi refeito, a 1ª tentativa fica em
`<nome>-1a-tentativa.out` e o resumo conta `repeticoes=R`. Qualquer outra falha conta direto.

## Erros que o teste reconhece

- "Erro de servidor de licença: -20": sessões anteriores não devolveram a licença. Rode
  `plab restart <rel>`.
- "Incompatibilidade ... stored procedure ... desatualizada": ver
  `skills/testes-protheus/references/procedures.md`.

author: daniel.montagna
