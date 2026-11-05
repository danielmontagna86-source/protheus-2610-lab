"""Alcada - Liberar de Documentos (MATA094) com o Admin. AL_ACAO = listar | aprovar | transferir
| pendencias. AL_DOC = numero do pedido. aprovar/transferir GRAVAM (base com copia)."""
import json
import os
import sys

import plab_pw as pw

rel = sys.argv[1]
host = os.environ[f"PLAB_{rel}_HOST"]
amb = os.environ[f"PLAB_{rel}_ENV"]
acao = os.environ.get("AL_ACAO", "listar")
doc = os.environ.get("AL_DOC", "")
if acao in ("aprovar", "transferir", "ausencia") and os.environ.get("PLAB_GRAVACAO_AUTORIZADA", "") != "sim":
    sys.exit("grava no banco do lab: exige PLAB_GRAVACAO_AUTORIZADA=sim e plab snapshot antes")
pasta = os.environ.get("PLAB_EVID_DIR", f"/tmp/al-lib-{rel}")

JS_ITENS = """() => { const out = []; const deep = (root) => root.querySelectorAll('*').forEach(e => {
  const t = e.tagName.toLowerCase(); const r = e.getBoundingClientRect();
  if (['wa-menu-popup-item','wa-menu-item'].includes(t) && r.width > 0) out.push((e.getAttribute('caption') || e.textContent || '').trim());
  if (e.shadowRoot) deep(e.shadowRoot); }); deep(document); return out; }"""
JS_TELA = """() => { const out = []; const deep = (root) => root.querySelectorAll('*').forEach(e => {
  const t = e.tagName.toLowerCase(); const r = e.getBoundingClientRect();
  if (t.startsWith('wa-') && r.width > 0 && r.height > 0) { const c = e.getAttribute('caption') || e.getAttribute('title') || e.getAttribute('name');
    if (c && c.trim()) out.push(t + ' ' + Math.round(r.x) + ',' + Math.round(r.y) + ' ' + c.replace(/<[^>]+>/g,'').trim().slice(0,90)); }
  if (e.shadowRoot) deep(e.shadowRoot); }); deep(document); return out; }"""


def linhas(pg):
    return [ln for ln in pw.linhas_grade(pg)]


def outras_acoes(pg):
    pw.por_caption(pg, "wa-button", "Outras Ações").click()
    pg.wait_for_timeout(2_000)
    itens = pg.evaluate(JS_ITENS)
    pg.keyboard.press("Escape")
    pg.wait_for_timeout(1_000)
    return itens


def selecionar(pg, numero):
    """Clica na linha do browse que contem o numero do documento."""
    js = """(n) => { let a = null; const deep = (root) => root.querySelectorAll('*').forEach(e => {
      if (!a && e.tagName.toLowerCase() === 'tr' && (e.innerText || '').includes(n)) { const b = e.getBoundingClientRect();
        if (b.width > 0 && b.height > 0 && b.height < 60) a = {x: b.x + 200, y: b.y + b.height / 2}; }
      if (!a && e.shadowRoot) deep(e.shadowRoot); }); deep(document); return a; }"""
    p = pg.evaluate(js, numero)
    if not p:
        raise AssertionError(f"documento {numero} nao esta no browse")
    pg.mouse.click(p["x"], p["y"])
    pg.wait_for_timeout(1_500)


with pw.navegador() as pg:
    ev = pw.Passos(pg, pasta)
    cod = 1
    try:
        pw.entrar(pg, f"http://{host}:1234/webapp/", amb, "Admin", pw.senha_admin(rel))
        desc = pw.sessao(pg, 2)
        pw.fechar_avisos(pg)
        pw.modulo_no_menu(pg, desc)
        pw.abrir_menu(pg, ["Atualizações", "Liberação", "Liberar de Documentos"])
        pw.confirmar_ambiente(pg)
        pw.cancelar_moedas(pg)
        if not pw.confirmar_parametros(pg):
            raise AssertionError("tela Parametros nao apareceu")
        pw.fechar_novidades(pg)
        pg.wait_for_timeout(10_000)
        ev.captura("browse")
        for ln in linhas(pg):
            print(f"[al] linha: {ln[:160]}")
        print(f"[al] outras acoes: {json.dumps(outras_acoes(pg), ensure_ascii=False)}")
        if acao in ("aprovar", "transferir") and doc:
            selecionar(pg, doc)
            if acao == "aprovar":
                pw.acao_browse(pg, os.environ.get("AL_BOTAO", "Aprovar"))
            else:
                pw.acao_browse(pg, "Transferir para superior")
            pg.wait_for_timeout(12_000)
            ev.captura(f"{acao}-form")
            for t in pg.evaluate(JS_TELA):
                print(f"[al] tela: {t}")
            if os.environ.get("AL_CONFIRMAR") == "sim":
                print(f"[al] confirmar: {pw.confirmar_formulario(pg, os.environ.get('AL_BOTAO_CONF', 'Confirmar'), os.environ.get('AL_TITULO', 'Documentos Com Alçada - Aprovação de Documentos'))}")
                pg.wait_for_timeout(5_000)
                ev.captura(f"{acao}-depois")
                for ln in linhas(pg):
                    print(f"[al] linha depois: {ln[:160]}")
            else:
                for b in ("Cancelar", "Fechar"):
                    if pw.existe_caption(pg, "wa-button", b, 2_000):
                        pw.por_caption(pg, "wa-button", b).click()
                        print(f"[al] {b} (nada gravado)")
                        break
        elif acao in ("pendencias", "ausencia"):
            pw.acao_browse(pg, "Pendências de subordinados")
            pg.wait_for_timeout(10_000)
            ev.captura("pendencias")
            if acao == "ausencia":
                pw.por_caption(pg, "wa-button", "Transferir").click()
                print("[al] Transferir clicado")
                for _ in range(6):
                    pg.wait_for_timeout(4_000)
                    textos = [t for t in pg.evaluate(JS_TELA) if "wa-text-view" in t or "wa-button" in t]
                    novos = [t for t in textos if any(k in t for k in ("Sim", "Confirma", "transfer", "Transfer", "sucesso", "Help"))]
                    print(f"[al] apos transferir: {novos[:8]}")
                    resp = next((b for b in ("Confirma", "Sim") if pw.existe_caption(pg, "wa-button", b, 1_000)), "")
                    if resp:
                        ev.captura("pergunta")
                        pw.por_caption(pg, "wa-button", resp).click()
                        print(f"[al] respondeu {resp}")
                        continue
                    if pw.existe_caption(pg, "wa-button", "Transferir", 1_000):
                        continue
                    break
                ev.captura("depois-transferir")
                pg.wait_for_timeout(5_000)
                for ln in linhas(pg):
                    print(f"[al] linha depois: {ln[:160]}")
            else:
                pw.por_caption(pg, "wa-button", "Cancelar").click()
        cod = 0
    except Exception as e:  # noqa: BLE001
        print(f"[al] FALHOU: {type(e).__name__}: {e}")
        ev.captura("falha")
    print("[al] saida:", pw.sair_do_sistema(pg))
    sys.exit(cod)
