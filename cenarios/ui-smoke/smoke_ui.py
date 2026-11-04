"""Smoke de interface (Playwright) somente leitura: login PO UI, modulo, abrir rotina padrao, conferir
titulo do browse, sair pelo 'Log Off' > 'Finalizar' (devolve a licenca). Complementa o TIR nos WebApps em que o Setup do TIR 2.14.12 nao conclui.

Uso (dentro do container lab):  lab ui <2610|2510>
Variaveis opcionais: PLAB_UI_MODULO (codigo, padrao 5 = Faturamento),
PLAB_UI_MENU ("Atualizações>Cadastros>Produtos"), PLAB_UI_ABA ("Produtos"),
PLAB_UI_TITULO ("Atualizacao de Produtos"), PLAB_UI_PARAMETROS ("ok" = confirmar a tela
'Parametros' com os valores padrao), PLAB_UI_HELP (codigo de Help esperado no lugar do browse,
ex.: "RECNO"), PLAB_UI_VISUALIZAR ("1" = abrir o 1o registro em Visualizar, capturar e fechar
com Cancelar/Fechar), PLAB_EVID_DIR (pasta de capturas).
author: daniel.montagna
"""
import os
import sys

import plab_pw as pw

class _Concluido(Exception):
    """Encerra o fluxo com sucesso antes do browse (ex.: Help esperado conferido)."""


rel = sys.argv[1] if len(sys.argv) > 1 else ""
if rel not in ("2610", "2510"):
    sys.exit("uso: smoke_ui.py <2610|2510>")

host = os.environ[f"PLAB_{rel}_HOST"]
ambiente = os.environ[f"PLAB_{rel}_ENV"]
modulo = int(os.environ.get("PLAB_UI_MODULO", "5"))
menu = os.environ.get("PLAB_UI_MENU", "Atualizações>Cadastros>Produtos").split(">")
aba = os.environ.get("PLAB_UI_ABA", "Produtos")
titulo = os.environ.get("PLAB_UI_TITULO", "Atualizacao de Produtos")  # vazio = conferir a grade
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
        aviso = os.environ.get("PLAB_UI_AVISO", "")
        if aviso and pw.fechar_aviso_informativo(pg, aviso):
            print(f"[ui] aviso da base com '{aviso}' registrado e fechado com Esc (nada alterado)")
            ev.captura("aviso")
        if os.environ.get("PLAB_UI_PARAMETROS", "") == "ok":
            if not pw.confirmar_parametros(pg):
                raise AssertionError("tela 'Parametros' esperada nao apareceu")
            print("[ui] tela 'Parametros': OK com os valores padrao (nenhum campo alterado)")
        if pw.fechar_novidades(pg):
            print("[ui] dialogo 'Novidades do Produto': Fechar (nada gravado)")
        ajuda = os.environ.get("PLAB_UI_HELP", "")
        if ajuda:
            # Resultado esperado de rotinas que, na base de demonstracao, nao tem o que mostrar
            # (ex.: Help RECNO "Nao existem registros no arquivo em pauta").
            if not pw.help_visivel(pg, ajuda):
                raise AssertionError(f"Help '{ajuda}' esperado nao apareceu")
            ev.captura("help")
            pw.fechar_help(pg, ajuda)
            print(f"[ui] Help '{ajuda}' exibido e fechado com 'Fechar' (nada gravado)")
            raise _Concluido(f"OK: rotina '{aba}' exibiu o Help esperado '{ajuda}'")
        if not pw.aba_aberta(pg, aba):
            raise AssertionError(f"aba '{aba}' nao abriu")
        if titulo:
            # O titulo do browse vem com ':' no fim ("Atualizacao de Produtos:"); compara sem ele.
            if not (pw.existe_caption(pg, "wa-text-view", titulo, 60_000)
                    or pw.existe_caption(pg, "wa-text-view", titulo + ":", 1_000)):
                raise AssertionError(f"titulo '{titulo}' nao encontrado no browse")
            confirmado = f"titulo '{titulo}'"
        else:
            # Browses MVC nao exibem titulo com ':'; a pos-condicao e a grade de dados carregada.
            if not pw.grade_carregada(pg):
                raise AssertionError("grade do browse nao carregou")
            confirmado = "grade de dados carregada"
        ev.captura("rotina")
        if os.environ.get("PLAB_UI_VISUALIZAR", "") == "1":
            formulario = pw.visualizar_registro(pg)
            print(f"[ui] Visualizar: formulario '{formulario}' aberto")
            ev.captura("visualizar")
            pw.fechar_visualizacao(pg)
            print("[ui] formulario fechado com Cancelar/Fechar (nada gravado)")
            if not pw.grade_carregada(pg, 30_000):
                raise AssertionError("browse nao voltou depois de fechar a visualizacao")
            confirmado += f"; '{formulario}' aberto e fechado"
        resultado = f"OK: aba '{aba}' aberta com {confirmado}"
        codigo = 0
    except _Concluido as fim:
        resultado, codigo = str(fim), 0
    except Exception as erro:  # noqa: BLE001
        ev.captura("falha")
        licenca = pw.erro_de_licenca(pg)
        if licenca:
            resultado = (f"FALHOU: licenca esgotada ({licenca}). Sessoes anteriores nao devolveram a "
                         f"licenca; rode 'plab restart {rel}' e repita")
        else:
            resultado = f"FALHOU: {type(erro).__name__}: {erro}"
        codigo = 1
    # Sai pelo 'Finalizar' mesmo na falha: sem isso a licenca de desenvolvimento fica presa.
    print(f"[ui] saida do sistema: {'Finalizar ok' if pw.sair_do_sistema(pg) else 'NAO confirmada'}")
    print(f"[ui] {resultado}")
    sys.exit(codigo)
