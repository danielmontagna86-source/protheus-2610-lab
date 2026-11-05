# Alçada de aprovação do Pedido de Compra

Roteiros usados em 05/11/2026 para testar a alçada do PC nas duas releases (issue #16). Todos
**gravam no banco do lab**: só com autorização do dono, `PLAB_GRAVACAO_AUTORIZADA=sim` e uma cópia
da base antes (`plab snapshot <rel>`). Resultado e achados em
[`docs/propostas/alcada-compras.md`](../../docs/propostas/alcada-compras.md).

Diferente do `lab gravacoes`, aqui cada passo é um roteiro separado e a ordem importa. Rode dentro
do container lab, com `PYTHONPATH=/opt/plab/lab/tir`:

| Ordem | Roteiro | O que faz |
|---|---|---|
| 1 | `al_usuario.py <rel>` | cria o usuário `labapr1` no Configurador (senha gerada na hora, nunca impressa) |
| 2 | — | `MV_APRPCEC = T` (a tela de parâmetros é a árvore antiga; no teste foi ligado por SQL no banco do lab) e `plab restart <rel>` |
| 3 | `AL_ETAPA=perfis al_config.py <rel>` | perfis `ZZ1` (até 1.000) e `ZZ2` (até 1.000.000) |
| 4 | `AL_ETAPA=aprovadores al_config.py <rel>` | Admin (`000001`) e `labapr1` (`000002`, superior `000001`) |
| 5 | `AL_ETAPA=grupos al_config.py <rel>` | grupo `000001` (labapr1, ZZ1, centro de custo 1.001) e `000002` (Admin, ZZ2, 1.002) |
| 6 | `AL_CC=… AL_PRECO=… al_pc.py <rel>` | pedido de 1 item IND.001 com o centro de custo e o preço informados |
| 7 | `AL_ACAO=… al_lib.py <rel>` | Liberar de Documentos: `listar`, `aprovar` (`AL_DOC`, `AL_CONFIRMAR=sim`), `ausencia` |

Na 2610, antes do passo 1, as sequências de RECNO atrasadas da base da imagem precisam ser
ajustadas (issue #30); sem isso a inclusão do usuário cai com chave duplicada.

No fim: `plab restore <rel> <copia>`.

## Comportamentos do WebApp vistos nestas telas

- Grade MVC (`wa-tgrid`, ex.: Grupo de Aprovação): o clique só seleciona a célula; Enter (ou duplo
  clique) abre o editor, e é o **Tab** que confirma o valor. O helper `preencher_celula` do
  `plab_pw` agora acha a célula em `wa-tgrid` também.
- Pedido de Compra: o fornecedor da base não tem condição de pagamento; o Tab da loja limpa a
  condição e mostra a Help `C7_COND`. Ordem que funciona: fornecedor, loja, fechar a Help, condição.
- O cadastro de usuários do Configurador usa `type=text` no campo de senha: nenhuma captura é tirada
  com a senha digitada.
