# Alçada de aprovação do Pedido de Compra (issue #16)

Sugestão da comunidade (LinkedIn, 03 e 04/11/2026): testar a alçada de verdade, incluindo
**troca de aprovador por ausência** e **limite por centro de custo**, onde costuma aparecer
diferença de comportamento entre releases. Executado em 05/11/2026 nas duas releases, com cópia da
base antes e `plab restore` depois. Roteiros em [`cenarios/ui-alcada/`](../../cenarios/ui-alcada/).

## Resultado

| Id | Cenário | 2610 | 2510 |
|---|---|---|---|
| AL1 | PC com centro de custo 1.001, R$ 500 | bloqueado; `SCR` tipo `IP` para o grupo 000001 / aprovador `labapr1` | igual |
| AL2 | PC com centro de custo 1.002, R$ 500; Admin aprova na Liberar de Documentos | `SCR` para o grupo 000002 / Admin; aprovado, PC `C7_CONAPRO = L` | igual |
| AL3 | PC com centro de custo 1.001, R$ 5.000 (acima do teto do perfil de `labapr1`) | **liberado direto, sem nenhuma `SCR`** | igual |
| AL4 | Ausência: Admin (superior) usa "Pendências de subordinados" → Transferir → aprova | `SCR` passa para o Admin guardando a origem (`CR_APRORI`, `CR_USERORI`); aprovado | igual |
| AL5 | Menu "Substituição de Aprovadores" | **tela nova (PO UI)** com transferência pontual, temporária e permanente | bloqueada: Help `A230CONFIG` exige Smart Schedule com o agendamento `A230EXECSCHED` |

Conferido por SQL somente leitura (`SC7`, `SCR`, `SAK`, `SAL`, `DBL`, `DHL`) e por capturas das
telas; evidências em `evidencias/<rel>/alcada-20261105/` (não versionadas).

## Achados

- **AL3 é o ponto de atenção.** Com um nível só no grupo e perfil com valor máximo, um pedido acima
  desse máximo não gerou alçada nenhuma e entrou liberado, nas duas releases. A leitura provável é
  que o aprovador só participa na faixa do perfil (`DHL_LIMMIN`–`DHL_LIMMAX`) e, sem aprovador na
  faixa, não há o que aprovar; não foi confirmada no código. Na prática: quem configura alçada por
  perfil precisa cobrir todas as faixas de valor (outro nível ou outro aprovador), senão o pedido
  grande passa sem aprovação.
- **A ausência funciona igual nas duas releases** pela Liberar de Documentos, sem agendador: a
  transferência leva todas as pendências do aprovador ausente para o superior (a tela avisa antes)
  e a `SCR` guarda quem era o aprovador original.
- **A Substituição de Aprovadores é a diferença entre releases.** A 2610 trouxe uma tela nova, que
  abre sem configuração extra; na 2510 a rotina exige o Smart Schedule. A tela nova da 2610 ainda
  não foi exercitada (próximo passo).
- **Base da imagem 2610**: 25 tabelas com a sequência de RECNO atrasada fazem qualquer inclusão
  nelas cair com chave duplicada, inclusive a de usuário (issue #30). Para o teste, as sequências
  foram ajustadas só no banco do lab.

## Configuração usada (igual nas duas releases)

| Item | Valor |
|---|---|
| `MV_APRPCEC` ("Habilita o controle de alçadas por item do pedido") | `T` (ligado por SQL no banco do lab: a tela de parâmetros é a árvore antiga) |
| Usuário de teste | `labapr1` (`000001`), ativo, senha gerada e descartada |
| Perfis (`DHL`) | `ZZ1` até 1.000; `ZZ2` até 1.000.000 |
| Aprovadores (`SAK`) | `000001` Admin; `000002` `labapr1`, superior `000001` |
| Grupos (`SAL` + `DBL`) | `000001`: `labapr1`, perfil ZZ1, nível 01, centro de custo 1.001; `000002`: Admin, perfil ZZ2, nível 01, centro de custo 1.002 |
| Pedidos | fornecedor 000002/01, condição 000, 1 × IND.001 |

O comprador da base (`001`, usuário Admin) não tem grupo; com `MV_APRPCEC = T` o grupo veio do
centro de custo do item, pela `DBL`.

## Fontes

- Fontes padrão da 2510 (pacote do dono, não versionado): MATA114 (grupo com grade `DBL`), MATA095
  (aprovador com `AK_APROSUP`; um usuário só pode ser aprovador uma vez), MATA094 ("Transferir para
  superior", "Pendências de subordinados" / `A097Ausente`).
- TDN, "Alçadas Entidade Contábil": a alçada do PC por entidade contábil depende de `MV_APRPCEC`.

## Fora deste teste

- Login como `labapr1` (exigiria guardar credencial de teste).
- A tela nova de Substituição de Aprovadores da 2610.
- Aprovação por e-mail/WF, contratos e cotações; alçada da Solicitação de Compras (`MV_APRSCEC`).
