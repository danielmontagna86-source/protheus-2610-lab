# Cenários de gravação

Cada cenário **grava no banco do lab**: inclui um registro de teste pela rotina padrão, confere no
browse, exclui pela própria rotina e confere que sumiu. Só a interface é usada (Playwright, os
mesmos ajudantes de `lab/tir/plab_pw.py`); nada é escrito direto no banco.

| Nome | Rotina | Módulo | Menu | Registro de teste | Efeito conferido no banco |
|---|---|---|---|---|---|
| solicitacao-compras | MATA110 | 2 Compras | Atualizações > Solicitações > Solicitação de Compras | SC com o número que a tela der, 1 item IND.001 × 1 | SC1 +1 ativa; `B2_SALPEDI` de IND.001/01 sobe 1 e volta na exclusão |
| natureza | FINA010 | 6 Financeiro | Atualizações > Cadastros > Naturezas | natureza `ZZLAB01` "LAB TESTE", despesa | SED +1 e volta |
| condicao-pagamento | MATA360 | 5 Faturamento | Atualizações > Cadastros > Condições de Pagamento | condição `ZZ9` tipo 1, "30", "LAB TESTE" | SE4 +1 e volta |
| inventario | MATA270 | 4 Estoque | Atualizações > Movimentações > Internas > Inventário | digitação doc `ZZINV01`, IND.001/01, quantidade 197 (igual ao saldo) | SB7 +1 e volta; `B2_QATU` não muda (o acerto MATA340 nunca roda) |

As quatro passam na 2610 e na 2510 (04/11/2026).

## Como rodar

Só com autorização do dono do ambiente. Antes, no host, guarde a base:

```bash
plab snapshot 2610 antes_gravacao
```

Dentro do container lab:

```bash
PLAB_GRAVACAO_AUTORIZADA=sim lab gravacoes 2610            # os quatro
PLAB_GRAVACAO_AUTORIZADA=sim lab gravacoes 2610 natureza   # um só
```

Sem `PLAB_GRAVACAO_AUTORIZADA=sim` o comando recusa e sai com código 3. Depois, se quiser a base
exatamente como antes (sem as linhas excluídas com `D_E_L_E_T_ = '*'`), volte a cópia no host:

```bash
plab restore 2610 antes_gravacao
```

Evidências em `evidencias/<rel>/gravacoes-<data>/<nome>/`: antes, formulário preenchido, incluído,
formulário de exclusão e excluído.

## O que o cenário faz e o que ele aceita

- Pré-condição: a chave de teste (prefixo `ZZ`) não pode existir no browse; se existir, o cenário
  falha e pede `plab restore`. Na SC a chave é o número que o formulário mostra.
- A única pergunta respondida com "Sim" é "Confirma Exclusão?" (FINA010). Qualquer Help no lugar da
  mensagem de sucesso faz o cenário falhar.
- O aviso intermitente de login da 2610 (issue #21) refaz o cenário desde o login uma vez, só
  quando nenhum formulário foi preenchido.

Campos do `gravacoes.json` (validados por `lab/tests/test_gravacoes_json.py`): `chave` (fixa, com
`ZZ`) ou `chave_campo` (lida do formulário); `campos` (`valor` digitado ou `opcao` de lista; o 1º é
esperado ao abrir o formulário); `itens` (coluna e valor na linha 1 da grade de itens);
`botao` ("Salvar" nas telas antigas), `botao_excluir`; `campo_reabre` (telas antigas que reabrem a
inclusão depois de salvar: o valor do campo muda e o formulário novo é cancelado); `titulo` e
`pesquisa: false` (browse conferido pelo título e registro achado nas linhas da grade, sem a lupa);
`aviso` e `parametros`, como nos cenários de leitura.

## Comportamentos observados no WebApp (04/11/2026)

- O `<input>` dos campos vem preenchido com espaços até o tamanho do campo: sem selecionar tudo
  antes de digitar, o 1º caractere estoura o tamanho e o foco pula para o campo seguinte.
- No campo "Pesquisar" do browse o Ctrl+A digita "a" e o Enter não pesquisa: o cenário limpa o
  campo e clica na lupa. Sem resultado, a rotina mostra o Help PESQ01 e a grade fica sem filtro.
- MATA110 e MATA270 (telas antigas) reabrem a inclusão depois de salvar; a MATA110 já mostra o
  próximo número.
- A numeração da SC (`000093`, `000094`...) não volta com `plab restore`: o controle dessa
  numeração fica fora do volume do banco (onde, exatamente, não foi confirmado). O cenário lê o
  número da tela, então isso não quebra nada.
- Na base de demonstração, `MV_SCSLDBL` = .F. e mesmo assim a inclusão da SC somou 1 em
  `B2_SALPEDI` (e a exclusão tirou).
