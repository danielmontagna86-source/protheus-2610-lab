"""Alcada - preparacao: cria o usuario de teste LABAPR1 no Configurador (GRAVA; base com copia).
Senha gerada aqui, nunca impressa nem guardada: o usuario so existe para ser aprovador subordinado."""
import os
import re
import secrets
import string
import sys

import plab_pw as pw

rel = sys.argv[1]
if os.environ.get("PLAB_GRAVACAO_AUTORIZADA", "") != "sim":
    sys.exit("grava no banco do lab: exige PLAB_GRAVACAO_AUTORIZADA=sim e plab snapshot antes")
host = os.environ[f"PLAB_{rel}_HOST"]
amb = os.environ[f"PLAB_{rel}_ENV"]
pasta = os.environ.get("PLAB_EVID_DIR", f"/tmp/al-usr-{rel}")
alfabeto = string.ascii_letters + string.digits
senha = "La1#" + "".join(secrets.choice(alfabeto) for _ in range(12))

with pw.navegador() as pg:
    ev = pw.Passos(pg, pasta)
    cod = 1
    try:
        pw.parametros_iniciais(pg, f"http://{host}:1234/webapp/", amb, programa="SIGACFG")
        pw.login_po_ui(pg, "Admin", pw.senha_admin(rel))
        cfg = pw.frame_por_url(pg, "/session-settings")
        cfg.locator("po-lookup input").first.wait_for(state="visible")
        pg.wait_for_timeout(3_000)
        cfg.get_by_role("button", name=re.compile(r"^\s*Entrar\s*$")).click()
        pw.fechar_avisos(pg)
        pw.cancelar_moedas(pg)
        pg.wait_for_timeout(5_000)
        pw.abrir_menu(pg, ["Usuário", "Senhas", "Usuários"])
        pg.wait_for_timeout(10_000)
        pw.acao_browse(pg, "Incluir")
        pw.campo_input(pg, "M->USR_CODIGO").wait_for(state="visible", timeout=60_000)
        pg.wait_for_timeout(3_000)
        pw.preencher(pg, "M->USR_CODIGO", "labapr1")
        pw.preencher(pg, "M->USR_NOME", "LAB Aprovador Teste")
        ev.captura("dados")
        for campo in ("M->USR_PSW", "M->USR_PSWCMP"):
            c = pw.campo_input(pg, campo)
            c.click(); c.press("Control+a"); c.press_sequentially(senha, delay=40); c.press("Tab")
            pg.wait_for_timeout(800)
        tipo = pw.campo_input(pg, "M->USR_PSW").get_attribute("type")
        print(f"[al] senha preenchida (campo type={tipo})")
        print(f"[al] confirmar: {pw.confirmar_formulario(pg, 'Confirmar', 'Cadastro de usuários')}")
        pg.wait_for_timeout(5_000)
        ev.captura("depois")
        cod = 0
    except Exception as e:  # noqa: BLE001
        print(f"[al] FALHOU: {type(e).__name__}: {e}")
        try:
            for campo in ("M->USR_PSW", "M->USR_PSWCMP"):
                pw.campo_input(pg, campo).fill("")
        except Exception:  # noqa: BLE001
            pass
        ev.captura("falha")
    del senha
    print("[al] saida:", pw.sair_do_sistema(pg))
    sys.exit(cod)
