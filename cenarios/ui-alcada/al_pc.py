"""Alcada - inclui um Pedido de Compra pela MATA121 (GRAVA; base com copia).
Env: AL_CC (centro de custo do item), AL_PRECO (preco unitario, quantidade 1), AL_ROTULO."""
import json
import os
import sys

import plab_pw as pw

rel = sys.argv[1]
if os.environ.get("PLAB_GRAVACAO_AUTORIZADA", "") != "sim":
    sys.exit("grava no banco do lab: exige PLAB_GRAVACAO_AUTORIZADA=sim e plab snapshot antes")
host = os.environ[f"PLAB_{rel}_HOST"]
amb = os.environ[f"PLAB_{rel}_ENV"]
cc = os.environ["AL_CC"]
preco = os.environ["AL_PRECO"]
pasta = os.environ.get("PLAB_EVID_DIR", f"/tmp/al-pc-{rel}")

JS_CAB = """() => { const out = []; const deep = (root) => root.querySelectorAll('*').forEach(e => {
  if (e.tagName.toLowerCase() === 'wa-tgetdados') { const b = e.getBoundingClientRect();
    if (b.width > 50) { const trs = (e.shadowRoot || e).querySelectorAll('tr');
      if (trs.length) { const v = Array.from(trs).slice(0,2).map(tr => Array.from(tr.children).map(c => c.innerText.trim())); if (v[0].includes('Produto')) out.push(v); } } }
  if (e.shadowRoot) deep(e.shadowRoot); }); deep(document); return out; }"""

# Rola a celula (coluna pelo titulo, linha 1) para a area visivel da grade de itens.
JS_ROLAR = """(coluna) => { let ok = false; const deep = (root) => root.querySelectorAll('*').forEach(e => {
  if (e.tagName.toLowerCase() === 'wa-tgetdados') { const trs = (e.shadowRoot || e).querySelectorAll('tr');
    if (trs.length > 1) { const k = Array.from(trs[0].children).map(c => c.innerText.trim()).indexOf(coluna);
      if (k >= 0) { trs[1].children[k].scrollIntoView({block: 'nearest', inline: 'center'}); ok = true; } } }
  if (e.shadowRoot) deep(e.shadowRoot); }); deep(document); return ok; }"""


def celula(pg, coluna, valor):
    if not pg.evaluate(JS_ROLAR, coluna):
        raise AssertionError(f"coluna {coluna!r} nao encontrada na grade de itens")
    pg.wait_for_timeout(1_000)
    pw.preencher_celula(pg, coluna, valor)
    print(f"[al] item {coluna} = {valor}")


with pw.navegador() as pg:
    ev = pw.Passos(pg, pasta)
    cod = 1
    try:
        pw.entrar(pg, f"http://{host}:1234/webapp/", amb, "Admin", pw.senha_admin(rel))
        desc = pw.sessao(pg, 2)
        pw.fechar_avisos(pg)
        pw.modulo_no_menu(pg, desc)
        pw.abrir_menu(pg, ["Atualizações", "Pedidos", "Pedidos de Compra"])
        pw.confirmar_ambiente(pg)
        pw.cancelar_moedas(pg)
        pw.fechar_novidades(pg)
        pg.wait_for_timeout(12_000)
        pw.acao_browse(pg, "Incluir")
        pw.campo_input(pg, "cA120Forn").wait_for(state="visible", timeout=90_000)
        pg.wait_for_timeout(5_000)
        numero = pw.campo_input(pg, "cA120Num").input_value().strip()
        print(f"[al] pedido {numero}: centro de custo {cc}, preco {preco}")
        cond = os.environ.get("AL_COND", "000")
        pw.preencher(pg, "cA120Forn", "000002")
        pw.preencher(pg, "cA120Loj", "01")
        # O fornecedor nao tem condicao (A2_COND vazio): a loja limpa a condicao e mostra a Help
        # do C7_COND. Fecha a Help e so entao preenche a condicao.
        if pw.existe_caption(pg, "wa-button", "Fechar", 5_000):
            pw.fechar_help(pg, "C7_COND")
            print("[al] Help C7_COND depois da loja fechada")
        pw.preencher(pg, "cCondicao", cond)
        print(f"[al] condicao {cond}")
        cab = pg.evaluate(JS_CAB)
        print(f"[al] cabecalho da grade: {json.dumps(cab[-1][0] if cab else [], ensure_ascii=False)}")
        celula(pg, "Produto", "IND.001")
        celula(pg, "Quantidade", "1")
        celula(pg, "Prc Unitario", preco)
        cab = pg.evaluate(JS_CAB)
        print(f"[al] cabecalho depois dos itens: {json.dumps(cab[-1][0] if cab else [], ensure_ascii=False)[:600]}")
        col_cc = next((h for h in (cab[-1][0] if cab else []) if "Custo" in h), "")
        if not col_cc:
            raise AssertionError("coluna de centro de custo nao encontrada")
        celula(pg, col_cc, cc)
        cab = pg.evaluate(JS_CAB)
        print(f"[al] linha 1: {json.dumps(cab[-1][1] if cab else [], ensure_ascii=False)[:400]}")
        ev.captura("pedido")
        print(f"[al] salvar: {pw.confirmar_formulario(pg, 'Salvar', 'Pedido de Compra - INCLUIR', 'cA120Num')}")
        ev.captura("depois")
        print(f"[al] OK pedido {numero}")
        cod = 0
    except Exception as e:  # noqa: BLE001
        print(f"[al] FALHOU: {type(e).__name__}: {e}")
        ev.captura("falha")
    print("[al] saida:", pw.sair_do_sistema(pg))
    sys.exit(cod)
