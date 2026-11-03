"""Explora (somente leitura) o menu de um modulo: lista os itens de 'Atualizações > Cadastros' ou de
outro caminho e, opcionalmente, abre um item e mostra o titulo do browse. Uso no container lab:
  python explorar_menu.py <release> <modulo> "Atualizações>Cadastros" [item_para_abrir]
author: daniel.montagna
"""
import os
import sys

import plab_pw as pw

JS_ITENS = """() => { const r=[]; const deep=(root)=>root.querySelectorAll('*').forEach(e=>{
  if(e.tagName.toLowerCase()==='wa-menu-item'){ const b=e.getBoundingClientRect();
    if(b.width>0) r.push((e.getAttribute('caption')||'').replace(/<[^>]+>/g,'')); }
  if(e.shadowRoot) deep(e.shadowRoot)}); deep(document); return r; }"""
JS_TITULOS = """() => { const r=[]; const deep=(root)=>root.querySelectorAll('*').forEach(e=>{
  const t=e.tagName.toLowerCase(); const c=(e.getAttribute && e.getAttribute('caption')||'').replace(/<[^>]+>/g,'').trim();
  const b=e.getBoundingClientRect ? e.getBoundingClientRect() : {width:0};
  if((t==='wa-tab-page'||(t==='wa-text-view' && c.endsWith(':'))) && c && b.width>0) r.push(t+'['+c+']');
  if(e.shadowRoot) deep(e.shadowRoot)}); deep(document); return [...new Set(r)]; }"""

rel, modulo, caminho = sys.argv[1], int(sys.argv[2]), sys.argv[3].split(">")
abrir = sys.argv[4] if len(sys.argv) > 4 else ""
host, amb = os.environ[f"PLAB_{rel}_HOST"], os.environ[f"PLAB_{rel}_ENV"]
with pw.navegador() as pg:
    pw.entrar(pg, f"http://{host}:1234/webapp/", amb, os.environ.get("PLAB_ADMIN_USER", "Admin"), pw.senha_admin(rel))
    print("modulo:", pw.sessao(pg, modulo))
    pw.fechar_avisos(pg)
    antes = set(pg.evaluate(JS_ITENS))
    pw.abrir_menu(pg, caminho)
    novos = [i for i in pg.evaluate(JS_ITENS) if i not in antes]
    print("itens:", novos)
    if abrir:
        pw.abrir_menu(pg, [abrir])
        pw.confirmar_ambiente(pg)
        pw.cancelar_moedas(pg)
        pg.wait_for_timeout(8000)
        print("titulos:", pg.evaluate(JS_TITULOS))
        print("grade visivel:", pw.grade_carregada(pg, 30_000))
    destino = os.environ.get("PLAB_EXPLORA_CAPTURA")
    if destino:
        pg.screenshot(path=destino)
        print("captura:", destino)
    # Sair pelo Log Off -> Finalizar devolve a licenca de desenvolvimento (fechar o navegador nao).
    print("saida:", "ok" if pw.sair_do_sistema(pg) else "FALHOU (plab restart <rel> libera a licenca)")
