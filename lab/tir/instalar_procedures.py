"""Instala/atualiza processos de stored procedures pelo Gestor de Procedures (CFGX051M) do
Configurador: SIGACFG > Base de Dados > Dicionario > Stored Procedure.

Uso (dentro do container lab): lab procedures <2610|2510> <processo> [processo...]  ex.: 08
Grava no banco do lab: so rode com autorizacao do dono do ambiente.

Fatos verificados em 02/11/2026 (2610, gestor "002 | 2.9.1 | TPH: OFF"):
- o pacote vem embarcado no RPO (.ZSPS); nada e baixado (TDN "Stored Procedures - Novo gerenciador
  de pacotes"); a instalacao roda em modo exclusivo;
- SIGACFG nao esta na lista de programas iniciais do WebApp, mas aceita digitacao;
- a marcacao nos grids e por duplo clique; empresa e processo sao achados pelo codigo;
- pos-condicao: resumo com "Falhas: 0" e "Sucessos: N" (N = empresas x processos).
author: daniel.montagna
"""
import os
import re
import sys
import time

import plab_pw as pw

rel = sys.argv[1] if len(sys.argv) > 1 else ""
processos = sys.argv[2:]
if rel not in ("2610", "2510") or not processos or not all(re.fullmatch(r"\d{2}", p) for p in processos):
    sys.exit("uso: instalar_procedures.py <2610|2510> <processo de 2 digitos> [...]")
empresa = os.environ.get("PLAB_EMPRESA", "99")
host = os.environ[f"PLAB_{rel}_HOST"]
ambiente = os.environ[f"PLAB_{rel}_ENV"]
pasta = os.environ.get("PLAB_EVID_DIR", f"/tmp/plab-procedures-{rel}")

# Celula de codigo visivel com o texto exato, dentro de uma faixa vertical (grid de empresas ou de
# processos) e na coluna 'Codigo' (x entre 90 e 150 na janela de 1367 px).
_JS_CELULA = """([texto, ymin, ymax]) => {
  let achado = null;
  const deep = (root) => root.querySelectorAll('*').forEach(e => {
    if (!achado && e.children.length === 0 && (e.textContent || '').trim() === texto) {
      const b = e.getBoundingClientRect();
      if (b.width > 0 && b.x > 90 && b.x < 150 && b.y > ymin && b.y < ymax) achado = {x: b.x, y: b.y + b.height / 2};
    }
    if (!achado && e.shadowRoot) deep(e.shadowRoot);
  });
  deep(document);
  return achado;
}"""


def marcar(pagina, codigo, ymin, ymax):
    pos = pagina.evaluate(_JS_CELULA, [codigo, ymin, ymax])
    if not pos:
        raise AssertionError(f"codigo {codigo} nao encontrado no grid (y {ymin}-{ymax})")
    pagina.mouse.dblclick(66, pos["y"])  # coluna 'Marca'
    pagina.wait_for_timeout(1_500)


def texto_contem(pagina, trecho):
    el = pagina.evaluate_handle(pw._JS_CONTEM, ["wa-text-view", trecho]).as_element()
    return (el.get_attribute("caption") or "") if el else ""


with pw.navegador() as pg:
    ev = pw.Passos(pg, pasta)
    codigo = 1
    try:
        pw.parametros_iniciais(pg, f"http://{host}:1234/webapp/", ambiente, programa="SIGACFG")
        pw.login_po_ui(pg, os.environ.get("PLAB_ADMIN_USER", "Admin"), pw.senha_admin(rel))
        cfg = pw.frame_por_url(pg, "/session-settings")
        cfg.locator("po-lookup input").first.wait_for(state="visible")
        pg.wait_for_timeout(3_000)
        cods = cfg.locator("po-lookup input:not([name$='_description'])")
        for i, v in ((0, empresa), (1, os.environ.get("PLAB_FILIAL", "01"))):
            if cods.nth(i).input_value().strip() != v:
                cods.nth(i).fill(v); cods.nth(i).press("Tab"); pg.wait_for_timeout(2_000)
        cfg.get_by_role("button", name=re.compile(r"^\s*Entrar\s*$")).click()
        print(f"[proc] SIGACFG {ambiente}: empresa {empresa}")
        pw.fechar_avisos(pg)
        if pw.cancelar_moedas(pg):
            print("[proc] dialogo Moedas: Cancelar (nada gravado)")
        pw.abrir_menu(pg, ["Base de Dados", "Dicionário", "Stored Procedure"])
        if not pw.existe_caption(pg, "wa-text-view", "PROCESSOS", 120_000):
            raise AssertionError("Gestor de Procedures nao abriu")
        pg.wait_for_timeout(8_000)
        print(f"[proc] gestor: {texto_contem(pg, 'Gestão de Procedures')}")
        marcar(pg, empresa, 220, 370)
        for p in processos:
            marcar(pg, p, 460, 740)
        ev.captura("marcados")
        pg.mouse.click(22, 158)  # botao lateral 'Instalar'
        if not pw.existe_caption(pg, "wa-text-view", "Gestão de Procedures - Instalação", 20_000):
            raise AssertionError(f"confirmacao nao apareceu: {texto_contem(pg, 'selecion') or 'sem mensagem'}")
        pw.por_caption(pg, "wa-button", "Sim").click()
        print(f"[proc] instalando processo(s) {' '.join(processos)} (modo exclusivo)")
        if not pw.existe_caption(pg, "wa-text-view", "Resumo da instalação", 600_000):
            raise AssertionError("resumo da instalacao nao apareceu em 10 min")
        ev.captura("resumo")
        numero = lambda rotulo: int(re.sub(r"\D", "", texto_contem(pg, rotulo)) or -1)  # noqa: E731
        sucessos, ignoradas, falhas = numero("Sucessos:"), numero("Ignoradas:"), numero("Falhas:")
        print(f"[proc] resumo: sucessos={sucessos} ignoradas={ignoradas} falhas={falhas}")
        # 'Ignorada' = processo ja atualizado (reexecucao): conta como sucesso, o comando e idempotente.
        if falhas != 0 or sucessos + ignoradas != len(processos):
            raise AssertionError(f"resumo diferente do esperado ({len(processos)} sem falha)")
        pw.clicar_ate_sumir(pg, "Fechar", ("wa-text-view", "Resumo da instalação"))
        pg.wait_for_timeout(5_000)
        ev.captura("depois")
        print(f"[proc] OK: processo(s) {' '.join(processos)} instalado(s) na empresa {empresa}")
        codigo = 0
    except Exception as erro:  # noqa: BLE001
        ev.captura("falha")
        print(f"[proc] FALHOU: {type(erro).__name__}: {erro}")
    print(f"[proc] saida do sistema: {'Finalizar ok' if pw.sair_do_sistema(pg) else 'NAO confirmada'}")
    sys.exit(codigo)
