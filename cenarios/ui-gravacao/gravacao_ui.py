"""Cenario de gravacao (Playwright): inclui um registro de teste pela rotina padrao, confere no
browse, exclui pela propria rotina e confere que sumiu. GRAVA no banco do lab.

So roda com autorizacao do dono (PLAB_GRAVACAO_AUTORIZADA=sim) e depois de 'plab snapshot <rel>'.
Uso (dentro do container lab): lab gravacoes <2610|2510> [nome]
Variaveis: PLAB_GRAV_NOME (cenario de gravacoes.json), PLAB_EVID_DIR (capturas).
author: daniel.montagna
"""
import json
import os
import sys

import plab_pw as pw

rel = sys.argv[1] if len(sys.argv) > 1 else ""
if rel not in ("2610", "2510"):
    sys.exit("uso: gravacao_ui.py <2610|2510>")
if os.environ.get("PLAB_GRAVACAO_AUTORIZADA", "") != "sim":
    sys.exit("gravacao_ui: sem PLAB_GRAVACAO_AUTORIZADA=sim (exige autorizacao do dono e plab snapshot antes)")

cfg_arq = os.path.join(os.environ.get("PLAB_HOME", "/opt/plab"), "cenarios", "ui-gravacao", "gravacoes.json")
with open(cfg_arq, encoding="utf-8") as f:
    cenarios = {c["nome"]: c for c in json.load(f)["cenarios"]}
cen = cenarios[os.environ["PLAB_GRAV_NOME"]]
chave = cen.get("chave", "")
host = os.environ[f"PLAB_{rel}_HOST"]
pasta = os.environ.get("PLAB_EVID_DIR", f"/tmp/plab-grav-{rel}")


def localizar(pg):
    """Linhas do browse com a chave: pela pesquisa (lupa) ou, com "pesquisa": false (browse sem
    indice pela chave, ex.: inventario), direto nas linhas visiveis da grade."""
    if cen.get("pesquisa", True):
        return pw.pesquisar(pg, chave)
    pg.wait_for_timeout(3_000)
    return [linha for linha in pw.linhas_grade(pg) if chave.upper() in linha.upper()]


def browse_pronto(pg, timeout_ms=60_000):
    if cen.get("titulo"):
        return pw.existe_caption(pg, "wa-text-view", cen["titulo"], timeout_ms)
    return pw.grade_carregada(pg, timeout_ms)


def abrir_formulario(pg, acao, primeiro_campo):
    pw.acao_browse(pg, acao)
    pw.campo_input(pg, primeiro_campo).wait_for(state="visible", timeout=60_000)
    pg.wait_for_timeout(3_000)  # hidratacao do formulario


with pw.navegador() as pg:
    ev = pw.Passos(pg, pasta)
    try:
        pw.entrar(pg, f"http://{host}:1234/webapp/", os.environ[f"PLAB_{rel}_ENV"],
                  os.environ.get("PLAB_ADMIN_USER", "Admin"), pw.senha_admin(rel))
        descricao = pw.sessao(pg, cen["modulo"])
        print(f"[grav] login ok; modulo {cen['modulo']} ({descricao})")
        pw.fechar_avisos(pg)
        if not pw.modulo_no_menu(pg, descricao):
            raise AssertionError(f"menu nao mostra o modulo '{descricao}'")
        pw.abrir_menu(pg, cen["menu"])
        print(f"[grav] menu: {' > '.join(cen['menu'])}")
        pw.confirmar_ambiente(pg)
        pw.cancelar_moedas(pg)
        if cen.get("aviso") and pw.fechar_aviso_informativo(pg, cen["aviso"]):
            print(f"[grav] aviso da base com '{cen['aviso']}' fechado com Esc")
        if cen.get("parametros") == "ok" and not pw.confirmar_parametros(pg):
            raise AssertionError("tela 'Parametros' esperada nao apareceu")
        pw.fechar_novidades(pg)
        if not browse_pronto(pg):
            raise AssertionError("browse nao carregou")

        # Pre-condicao: o registro de teste nao pode existir (senao a base nao esta limpa). Com
        # "chave_campo" (numero automatico, ex.: SC) a chave so e conhecida no formulario.
        if chave and localizar(pg):
            raise AssertionError(f"'{chave}' ja existe no browse: restaure a copia da base (plab restore)")
        if chave:
            print(f"[grav] pre-condicao: '{chave}' nao existe")
        ev.captura("antes")

        # Inclusao
        botao = cen.get("botao", "Confirmar")
        campos = cen["campos"]
        abrir_formulario(pg, "Incluir", campos[0]["campo"])
        if cen.get("chave_campo"):
            chave = pw.campo_input(pg, cen["chave_campo"]).input_value().strip()
            if not chave:
                raise AssertionError(f"campo {cen['chave_campo']} sem numero")
            print(f"[grav] numero do formulario ({cen['chave_campo']}): {chave}")
        for c in campos:
            if "opcao" in c:
                pw.escolher(pg, c["campo"], c["opcao"])
            elif "valor" in c:
                pw.preencher(pg, c["campo"], c["valor"])
        for item in cen.get("itens", []):
            pw.preencher_celula(pg, item["coluna"], item["valor"])
        print(f"[grav] preenchidos: {', '.join([c['campo'] for c in campos if 'valor' in c or 'opcao' in c] + [i['coluna'] for i in cen.get('itens', [])])}")
        ev.captura("incluir")
        print(f"[grav] incluir: {pw.confirmar_formulario(pg, botao, cen.get('form_incluir', ''), cen.get('campo_reabre', ''))}")
        if not browse_pronto(pg, 30_000):
            raise AssertionError("browse nao voltou depois da inclusao")
        achadas = localizar(pg)
        if len(achadas) != 1:
            raise AssertionError(f"esperada 1 linha com '{chave}' depois da inclusao; achadas {len(achadas)}")
        print(f"[grav] browse mostra: {achadas[0][:80]}")
        ev.captura("incluido")

        # Exclusao (reversao pela propria rotina)
        pw.acao_browse(pg, "Excluir")
        titulo = pg.wait_for_function(pw._JS_MENSAGEM, arg=["- EXCLUIR", "confirmação da exclusão"], timeout=60_000).json_value()
        pg.wait_for_timeout(3_000)
        print(f"[grav] formulario: {titulo}")
        ev.captura("excluir")
        print(f"[grav] excluir: {pw.confirmar_formulario(pg, cen.get('botao_excluir', 'Confirmar'), titulo)}")
        restantes = localizar(pg)
        if restantes:
            raise AssertionError(f"'{chave}' continua no browse depois da exclusao")
        print(f"[grav] pos-condicao: '{chave}' nao existe mais")
        ev.captura("excluido")
        resultado, codigo = f"OK: '{chave}' incluido e excluido pela {cen['rotina']}", 0
    except Exception as erro:  # noqa: BLE001
        ev.captura("falha")
        resultado, codigo = f"FALHOU: {type(erro).__name__}: {erro}", 1
    print(f"[grav] saida do sistema: {'Finalizar ok' if pw.sair_do_sistema(pg) else 'NAO confirmada'}")
    print(f"[grav] {resultado}")
    sys.exit(codigo)
