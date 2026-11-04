# Contract: `lab menus` e `lab menus-diff` (dentro do container)

Incluído em 04/11/2026. Relatório do que mudou no menu entre a 2610 e a 2510, para quem vai
atualizar e para divulgação.

```text
lab menus <2610|2510> <modulo> [caminho]   # mapeia o menu (somente leitura) → evidencias/<rel>/menus/<modulo>.json
lab menus-diff <modulo>                    # compara os dois JSON → evidencias/menus-diff-<modulo>.md
```

- `<modulo>`: código numérico do módulo (ex.: `2` = Compras, `5` = Faturamento, `6` = Financeiro).
- `[caminho]`: padrão `Atualizações`. Aceita subcaminho (`Atualizações>Cadastros`), lista separada
  por vírgula (`Atualizações,Consultas`) ou `todos` (`Atualizações`, `Consultas`, `Relatórios`,
  `Miscelânea`). Um novo `lab menus` do mesmo módulo substitui o JSON anterior.

## Regras de `lab menus` (somente leitura)

1. Entra pelo login PO UI, sessão grupo 99 / filial 01 no módulo pedido, fecha avisos com `Fechar`.
2. Percorre o menu clicando **só em grupos** (caption terminado em `(N)`) e nos passos do caminho.
   Antes de cada clique confere no navegador que o item na posição esperada tem o caption esperado;
   se não tiver, não clica e falha. Passo de subcaminho que não é grupo também falha. Nenhuma
   rotina é aberta.
3. Filhos de um grupo = bloco de `wa-menu-item` visíveis inserido logo abaixo dele após o clique
   (mesma técnica de `lab/tir/explorar_menu.py`). Contador `(N)` diferente do número de filhos vira
   aviso. Depois de percorrer um grupo, clica de novo para recolher; se o menu não recolher, segue
   com o grupo aberto (as posições são recalculadas) e registra aviso.
4. Sempre sai por **Log Off → Finalizar** num `finally`, mesmo após erro ou limite. Imprime
   `saida: ok` ou `saida: FALHOU (...)`.
5. Grava o JSON também quando falha (com `"completo": false`). Em erro, captura
   `<modulo>-erro.png` com o formulário de login limpo.

| Variável | Padrão | Efeito |
|---|---|---|
| `PLAB_MENUS_PROFUNDIDADE` | `5` | níveis abaixo de cada raiz; grupos mais fundos não são abertos (`completo: false`) |
| `PLAB_MENUS_TEMPO` | `1200` | segundos de navegação; ao estourar, para, grava o parcial e sai pelo Log Off |
| `PLAB_MENUS_LIMITE` | `TEMPO + 300` | corte duro do processo (`timeout`); se ele cortar, a sessão fica presa: `plab restart <rel>` |

### Formato do JSON

```json
{
  "release": "2610", "modulo": 2, "descricao_modulo": "...",
  "coletado_em": "2026-11-04T10:00:00-03:00",
  "raizes": ["Atualizações"], "profundidade_max": 5, "completo": true,
  "topo": ["Atualizações", "Consultas", "..."],
  "avisos": [],
  "menus": {
    "Atualizações": ["Cadastros (30)", "Administração de Compras (11)", "..."],
    "Atualizações>Cadastros": ["Produtos", "Fornecedores", "..."]
  }
}
```

Chave de `menus` = caminho com `>` e nomes **sem** o contador; valores = captions como aparecem
(com o contador nos grupos), em ordem de tela.

### Códigos de saída

`0` mapa completo e saída confirmada; `1` mapa incompleto ou erro de navegação (JSON parcial
gravado); `2` uso inválido (release, módulo ou caminho); `4` saída por Log Off não confirmada
(rode `plab restart <rel>`); `124` corte duro por `PLAB_MENUS_LIMITE`.

## Regras de `lab menus-diff`

Lê `evidencias/2610/menus/<modulo>.json` e `evidencias/2510/menus/<modulo>.json`; não acessa o
Protheus. Itens são comparados pelo rótulo sem contador e sem diferenciar caixa (repetidos contam).

- **Só na 2610 / Só na 2510**: itens de um caminho mapeado dos dois lados que faltam no outro; se o
  grupo inteiro é exclusivo, o grupo e todos os filhos mapeados aparecem.
- **Grupos com contagem diferente**: mesmo grupo com `(N)` diferente (ex.: `Cadastros` 30 × 28).
- **Não comparados**: grupo aberto só de um lado embora exista nos dois (limite, raiz diferente).
- Mapa incompleto em qualquer lado gera um alerta no topo do relatório.

Saída na tela: `menus-diff <modulo>: so 2610=N so 2510=M contagem diferente=K nao comparados=Z relatorio=...`.

Códigos de saída: `0` relatório gerado (com ou sem diferenças); `2` uso inválido; `3` JSON ausente
ou inválido.

## Testes sem Protheus (CI)

- `lab/tests/test_menus.py`: diff com o dado real de Compras (fixtures em `lab/tests/fixtures/menus`,
  coletado em 03/11/2026, só o 1º nível de `Atualizações`: 2610 tem `Cadastros (30)` e
  `Controle Orçamentário (6)`; 2510 tem `Cadastros (28)`), casos sintéticos e o mapeador contra um
  menu simulado (confere que nenhuma rotina é clicada).
- `lab/tests/test_menus_cli.sh`: códigos de saída e relatório pela linha de comando.
