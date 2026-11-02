"""Smoke de interface (Playwright) somente leitura: login PO UI, modulo, abrir rotina padrao, conferir
titulo do browse, sair. Complementa o TIR nos WebApps em que o Setup do TIR 2.14.12 nao conclui.

Uso (dentro do container lab):  lab ui <2610|2510>
Variaveis opcionais: PLAB_UI_MODULO (codigo, padrao 5 = Faturamento),
PLAB_UI_MENU ("Atualizações>Cadastros>Produtos"), PLAB_UI_ABA ("Produtos"),
PLAB_UI_TITULO ("Atualizacao de Produtos"), PLAB_EVID_DIR (pasta de capturas).
author: daniel.montagna
"""
import os
import sys

import plab_pw as pw

rel = sys.argv[1] if len(sys.argv) > 1 else ""
if rel not in ("2610", "2510"):
    sys.exit("uso: smoke_ui.py <2610|2510>")

host = os.environ[f"PLAB_{rel}_HOST"]
ambiente = os.environ[f"PLAB_{rel}_ENV"]
modulo = int(os.environ.get("PLAB_UI_MODULO", "5"))
menu = os.environ.get("PLAB_UI_MENU", "Atualizações>Cadastros>Produtos").split(">")
aba = os.environ.get("PLAB_UI_ABA", "Produtos")
titulo = os.environ.get("PLAB_UI_TITULO", "Atualizacao de Produtos")
pasta = os.environ.get("PLAB_EVID_DIR", f"/tmp/plab-ui-{rel}")

with pw.navegador() as pg:
    ev = pw.Passos(pg, pasta)
    try:
        pw.entrar(pg, f"http://{host}:1234/webapp/", ambiente,
                  os.environ.get("PLAB_ADMIN_USER", "Admin"), pw.senha_admin(rel))
        print(f"[ui] parametros iniciais: SIGAMDI / {ambiente}")
        descricao = pw.sessao(pg, modulo)
        print(f"[ui] login ok; empresa 99 / filial 01 / modulo {modulo} ({descricao})")
        print(f"[ui] avisos fechados: {pw.fechar_avisos(pg)}")
        if not pw.modulo_no_menu(pg, descricao):
            raise AssertionError(f"menu nao mostra o modulo '{descricao}'")
        ev.captura("menu")
        pw.abrir_menu(pg, menu)
        print(f"[ui] menu: {' > '.join(menu)}")
        if pw.confirmar_ambiente(pg):
            print("[ui] modal de confirmacao de ambiente: Confirmar (parametros da sessao)")
        if pw.cancelar_moedas(pg):
            print("[ui] dialogo Moedas: Cancelar (nada gravado)")
        if not pw.aba_aberta(pg, aba):
            raise AssertionError(f"aba '{aba}' nao abriu")
        # O titulo do browse vem com ':' no fim ("Atualizacao de Produtos:"); compara sem ele.
        if not (pw.existe_caption(pg, "wa-text-view", titulo, 60_000)
                or pw.existe_caption(pg, "wa-text-view", titulo + ":", 1_000)):
            raise AssertionError(f"titulo '{titulo}' nao encontrado no browse")
        ev.captura("rotina")
        print(f"[ui] OK: aba '{aba}' aberta com titulo '{titulo}'")
    except Exception as erro:  # noqa: BLE001
        ev.captura("falha")
        print(f"[ui] FALHOU: {type(erro).__name__}: {erro}")
        sys.exit(1)
