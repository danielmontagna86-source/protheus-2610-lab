"""Alcada - preparacao pela interface (GRAVA; base com copia). AL_ETAPA = perfis | aprovadores | grupos."""
import json
import os
import sys

import plab_pw as pw

rel = sys.argv[1]
if os.environ.get("PLAB_GRAVACAO_AUTORIZADA", "") != "sim":
    sys.exit("grava no banco do lab: exige PLAB_GRAVACAO_AUTORIZADA=sim e plab snapshot antes")
etapa = os.environ["AL_ETAPA"]
host = os.environ[f"PLAB_{rel}_HOST"]
amb = os.environ[f"PLAB_{rel}_ENV"]
pasta = os.environ.get("PLAB_EVID_DIR", f"/tmp/al-{rel}")
MENU = {"perfis": "Perfis de Aprovação", "aprovadores": "Aprovadores", "grupos": "Grupos de Aprovação"}

JSG = """() => { const out = []; const deep = (root) => root.querySelectorAll("*").forEach(e => {
  const t = e.tagName.toLowerCase(); const r = e.getBoundingClientRect();
  if (['wa-tgrid','wa-tgetdados'].includes(t) && r.width > 50 && r.height > 20) { const trs = (e.shadowRoot || e).querySelectorAll("tr");
    if (trs.length) out.push([t, Math.round(r.y), Array.from(trs).slice(0,3).map(tr => Array.from(tr.children).map(c => c.innerText.trim()).slice(0,12))]); }
  if (e.shadowRoot) deep(e.shadowRoot); }); deep(document); return out; }"""


def grades(pg, rotulo):
    for g in pg.evaluate(JSG):
        print(f"[al] grade {rotulo}: {json.dumps(g, ensure_ascii=False)}")


JSA = """() => { let a = document.activeElement; while (a && a.shadowRoot && a.shadowRoot.activeElement) a = a.shadowRoot.activeElement;
  return a ? a.tagName : null; }"""


def editor_aberto(pg):
    return pg.evaluate(JSA) == "INPUT"


def celula_mvc(pg, coluna, valor, linha=1):
    """Grade MVC (wa-tgrid): clique seleciona a celula, Enter abre o editor, Ctrl+A + digitacao,
    Tab confirma (o Enter nao confirma sempre). Confere o texto da celula."""
    texto = ""
    for _ in range(3):
        c = pg.evaluate(pw._JS_CELULA, [coluna, linha])
        if not c:
            raise AssertionError(f"coluna {coluna!r} nao encontrada")
        pg.mouse.click(c["x"], c["y"])
        pg.wait_for_timeout(1_000)
        pg.keyboard.press("Enter")
        pg.wait_for_timeout(1_500)
        if not editor_aberto(pg):
            pg.mouse.dblclick(c["x"], c["y"])
            pg.wait_for_timeout(1_500)
        if not editor_aberto(pg):
            print(f"[al] editor da celula {coluna} nao abriu")
            continue
        pg.keyboard.press("Control+a")
        pg.keyboard.type(valor, delay=80)
        pg.wait_for_timeout(600)
        pg.keyboard.press("Tab")
        pg.wait_for_timeout(2_500)
        texto = pg.evaluate(pw._JS_CELULA, [coluna, linha])["texto"]
        print(f"[al] celula {coluna}: {texto!r}")
        if texto.upper() == valor.upper():
            return
    raise AssertionError(f"celula {coluna!r}: {texto!r} != {valor!r}")


JS_TEXTO = """(t) => { let a = null; const deep = (root) => root.querySelectorAll("*").forEach(e => {
  if (!a && e.children.length === 0 && (e.textContent || "").trim() === t) { const b = e.getBoundingClientRect();
    if (b.width > 0) a = {x: b.x + b.width / 2, y: b.y + b.height / 2}; }
  if (!a && e.shadowRoot) deep(e.shadowRoot); }); deep(document); return a; }"""


def clicar_texto(pg, texto):
    p = pg.evaluate(JS_TEXTO, texto)
    if not p:
        raise AssertionError(f"texto {texto!r} nao encontrado")
    pg.mouse.click(p["x"], p["y"])
    pg.wait_for_timeout(3_000)


def incluir(pg, primeiro):
    pw.acao_browse(pg, "Incluir")
    pw.campo_input(pg, primeiro).wait_for(state="visible", timeout=60_000)
    pg.wait_for_timeout(4_000)


def confirmar(pg, titulo):
    print(f"[al] confirmar: {pw.confirmar_formulario(pg, 'Confirmar', titulo)}")
    pg.wait_for_timeout(4_000)


with pw.navegador() as pg:
    ev = pw.Passos(pg, pasta)
    cod = 1
    try:
        pw.entrar(pg, f"http://{host}:1234/webapp/", amb, "Admin", pw.senha_admin(rel))
        desc = pw.sessao(pg, 2)
        pw.fechar_avisos(pg)
        pw.modulo_no_menu(pg, desc)
        pw.abrir_menu(pg, ["Atualizações", "Administração de Compras", MENU[etapa]])
        pw.confirmar_ambiente(pg)
        pw.cancelar_moedas(pg)
        pw.fechar_novidades(pg)
        pg.wait_for_timeout(8_000)
        if etapa == "perfis":
            for codigo, descr, maximo in (("ZZ1", "LAB ATE 1000", "1000,00"), ("ZZ2", "LAB ATE 1000000", "1000000,00")):
                incluir(pg, "M->DHL_COD")
                pw.preencher(pg, "M->DHL_COD", codigo)
                pw.preencher(pg, "M->DHL_DESCRI", descr)
                pw.preencher(pg, "M->DHL_LIMMAX", maximo)
                ev.captura(f"perfil-{codigo}")
                confirmar(pg, "Perfil de Aprovadores - INCLUIR")
        elif etapa == "aprovadores":
            for usuario, superior, limite in (("000000", "", "1000000,00"), ("000001", "000001", "1000,00")):
                incluir(pg, "M->AK_COD")
                codigo = pw.campo_input(pg, "M->AK_COD").input_value().strip()
                pw.preencher(pg, "M->AK_USER", usuario)
                pg.wait_for_timeout(2_000)
                if superior:
                    pw.preencher(pg, "M->AK_APROSUP", superior)
                pw.preencher(pg, "M->AK_LIMITE", limite)
                nome = pw.campo_input(pg, "M->AK_NOME").input_value().strip()
                print(f"[al] aprovador {codigo}: usuario {usuario} ({nome}) superior '{superior}' limite {limite}")
                ev.captura(f"aprovador-{usuario}")
                confirmar(pg, "Aprovadores - INCLUIR")
        elif etapa == "grupos":
            for descr, aprov, perfil, cc in (("LAB CC MONTAGEM", "000002", "ZZ1", "1.001"),
                                             ("LAB CC TORNO", "000001", "ZZ2", "1.002")):
                incluir(pg, "M->AL_COD")
                codigo = pw.campo_input(pg, "M->AL_COD").input_value().strip()
                pw.preencher(pg, "M->AL_DESC", descr)
                celula_mvc(pg, "Aprovador", aprov)
                celula_mvc(pg, "Perfil Aprov", perfil)
                celula_mvc(pg, "Nivel", "01")
                grades(pg, "aprovadores")
                clicar_texto(pg, "Entidades Contábeis")
                grades(pg, "entidades")
                ev.captura(f"grupo-{codigo}-entidades")
                col = os.environ.get("AL_COL_CC", "") or next((h for g in pg.evaluate(JSG) for h in g[2][0] if "Custo" in h), "")
                if not col:
                    raise AssertionError("coluna de centro de custo nao encontrada na grade de entidades")
                print(f"[al] coluna do centro de custo: {col!r}")
                celula_mvc(pg, col, cc)
                ev.captura(f"grupo-{codigo}")
                print(f"[al] grupo {codigo} {descr}: aprovador {aprov}, perfil {perfil}, centro de custo {cc}")
                confirmar(pg, "Grupos de Aprovação - INCLUIR")
        ev.captura("browse-final")
        cod = 0
    except Exception as e:  # noqa: BLE001
        print(f"[al] FALHOU: {type(e).__name__}: {e}")
        ev.captura("falha")
    print("[al] saida:", pw.sair_do_sistema(pg))
    sys.exit(cod)
