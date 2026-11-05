"""Alcada - Substituicao de Aprovadores (2610, tela nova PO UI). SUB_FASE = obs1 (so mostra os documentos) | obs2
(avanca para o passo Substituto, sem confirmar) | gravar (informa o substituto e confirma: GRAVA).
Env: SUB_APROV, SUB_OPCAO, SUB_DOC, SUB_SUBST."""
import os
import sys

import plab_pw as pw

rel = sys.argv[1]
host = os.environ[f"PLAB_{rel}_HOST"]
amb = os.environ[f"PLAB_{rel}_ENV"]
aprov = os.environ.get("SUB_APROV", "000004")
opcao = os.environ.get("SUB_OPCAO", "Transferência pontual")
fase = os.environ.get("SUB_FASE", "obs1")
pasta = os.environ.get("PLAB_EVID_DIR", f"/tmp/sub-{rel}")
if fase == "gravar" and os.environ.get("PLAB_GRAVACAO_AUTORIZADA", "") != "sim":
    sys.exit("gravar exige PLAB_GRAVACAO_AUTORIZADA=sim e plab snapshot antes")


def frame_po(pg):
    for _ in range(120):
        for f in pg.frames:
            try:
                if f.locator("text=Substituição do aprovador").count():
                    return f
            except Exception:  # noqa: BLE001
                pass
        pg.wait_for_timeout(500)
    raise AssertionError(f"frame PO UI nao achado: {[f.url for f in pg.frames]}")


def mostrar(fr, rotulo):
    print(f"[sub] ---- {rotulo}")
    print(fr.locator("body").inner_text())
    print("[sub] ----")


with pw.navegador() as pg:
    ev = pw.Passos(pg, pasta)
    try:
        pw.entrar(pg, f"http://{host}:1234/webapp/", amb, "Admin", pw.senha_admin(rel))
        desc = pw.sessao(pg, 2)
        pw.fechar_avisos(pg)
        pw.modulo_no_menu(pg, desc)
        pw.abrir_menu(pg, ["Atualizações", "Liberação", "Substituição de Aprovadores"])
        pw.confirmar_ambiente(pg)
        pw.cancelar_moedas(pg)
        pw.fechar_novidades(pg)
        fr = frame_po(pg)
        pg.wait_for_timeout(3_000)
        cod = fr.locator("input").first
        cod.click()
        cod.fill(aprov)
        cod.press("Tab")
        pg.wait_for_timeout(4_000)
        fr.get_by_text(opcao, exact=True).click()
        pg.wait_for_timeout(6_000)
        ev.captura("opcao")
        mostrar(fr, "documentos")
        if fase in ("obs2", "gravar"):
            linha = fr.locator("tbody tr").filter(has_text=os.environ.get("SUB_DOC", "000005")).first
            linha.locator("po-checkbox, input[type=checkbox]").first.click()
            pg.wait_for_timeout(1_500)
            ev.captura("documento")
            fr.get_by_role("button", name="Próximo passo").click()
            pg.wait_for_timeout(5_000)
            ev.captura("passo2")
            mostrar(fr, "passo2")
            print("[sub] inputs visiveis:", fr.locator("input:visible").count())
        if fase == "gravar":
            sub = fr.locator("input:visible").first
            sub.click()
            sub.fill(os.environ.get("SUB_SUBST", "000003"))
            sub.press("Tab")
            pg.wait_for_timeout(4_000)
            ev.captura("substituto")
            mostrar(fr, "substituto")
            fr.get_by_role("button", name="Confirmar").click()
            modal = fr.locator("po-modal").filter(has_text="Transferência de documentos")
            modal.get_by_text("Deseja transferir").wait_for(state="visible", timeout=20_000)
            ev.captura("pergunta")
            modal.get_by_role("button", name="Confirmar").click()
            pg.wait_for_timeout(8_000)
            ev.captura("confirmado")
            mostrar(fr, "depois")
    except Exception as e:  # noqa: BLE001
        print(f"[sub] FALHOU: {type(e).__name__}: {e}")
        ev.captura("falha")
    print("[sub] saida:", pw.sair_do_sistema(pg))
