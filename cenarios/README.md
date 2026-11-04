# Cenários

Todos rodam dentro do container `lab`. Os de interface são **somente leitura**: entram, abrem a
rotina padrão, conferem o browse e saem pelo "Log Off → Finalizar". Nada é gravado: "Moedas" usa
Cancelar, "Novidades do Produto" usa Fechar e o aviso MV_1DUP da base é fechado com Esc.

| Pasta | O que é | Comando |
|---|---|---|
| `hello/` | `LABHELLO.prw` (CP1252 + CRLF) para provar a compilação | `lab compile <rel> /opt/plab/cenarios/hello/LABHELLO.prw` |
| `ui-smoke/` | smoke de interface (Playwright): MATA010 | `lab ui <rel>` |
| `ui-leitura/` | 6 cenários de leitura em `cenarios.json` | `lab cenarios <rel> [nome]` |
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

¹ Na 2610 exige o processo de stored procedures 08 atualizado: rode
`lab procedures 2610 08` e depois `plab restart 2610` (ver README principal, Problemas conhecidos).

² Incluído em 03/11/2026 por sugestão da comunidade (Pedido de Compra com alçada). A base de
demonstração das duas releases tem um pedido (000001, 14 itens) já liberado (`C7_CONAPRO = L`),
nenhum aprovador e nenhum documento de alçada (`SCR` vazia; a `SAL` nem existe no banco), e
`MV_APRPCEC` = F. Por isso o cenário só confere o browse: testar alçada exige cadastrar grupo e
aprovadores, o que grava na base e fica fora dos cenários de leitura. Na 2610, "Liberar de
Documentos" abre com o Help A097APROV (sem texto de problema) para o Admin; a `SAK` não tem
aprovadores, o que é a causa provável, ainda não confirmada.

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
