"""Inicializa a base VAZIA da fonte reserva (imagens feliperaposo/*, issue #3): abre o WebApp e
segue o assistente do Protheus ate a tela de login, sem fazer login.
  python inicializar_reserva.py <2610|2510>

Telas tratadas (vistas na 2610 em 05/11/2026):
  1. "Criacao de empresa": confere que a opcao marcada e a empresa TESTE 99/01 e clica Selecionar.
  2. "Selecione a localizacao": confere que o pais e Brasil e clica OK.
  3. "Aguarde, inicializando o sistema" e "Verificando atualizacoes": so espera (cerca de 3 min).
  4. Tela de login (iframe /login): fim, codigo 0.
Base ja inicializada: o login aparece direto, codigo 0 (pode rodar de novo sem efeito).
"Inconsistencia" (base iniciada pela metade, por exemplo por uma chamada ao /app-root/ antes deste
passo): codigo 3; a base da reserva precisa ser recriada. Tempo esgotado: 124. Erro: 1.
Capturas em evidencias/<rel>/<data>-inicializar-reserva/.
author: daniel.montagna
"""
import os
import sys
import time

sys.path.insert(0, os.path.join(os.environ.get("PLAB_HOME", "/opt/plab"), "lab", "tir"))
import plab_pw as pw  # noqa: E402

# Texto visivel de toda a pagina, atravessando shadow DOM; os wa-* guardam o texto em "caption" e a
# descricao da opcao marcada fica no valor de um textarea.
TEXTO = """() => { const out = []; const ver = (n) => {
  if (n.nodeType === 3) { const t = n.textContent.trim(); if (t) out.push(t); return; }
  if (n.nodeType !== 1) return; const cs = getComputedStyle(n);
  if (cs.display === 'none' || cs.visibility === 'hidden') return;
  const c = n.getAttribute && n.getAttribute('caption'); if (c) out.push('[' + c + ']');
  if (n.tagName === 'TEXTAREA' && n.value.trim()) out.push(n.value.trim());
  if (n.shadowRoot) n.shadowRoot.childNodes.forEach(ver); n.childNodes.forEach(ver); };
  ver(document.body); return out.join(' / '); }"""

# Valor selecionado do primeiro <select> visivel (o pais), atravessando shadow DOM.
PAIS = """() => { let v = null; const ver = (r) => r.querySelectorAll('*').forEach(e => {
  if (v !== null) return; if (e.tagName === 'SELECT' && e.getBoundingClientRect().width > 0) {
  v = e.options[e.selectedIndex] ? e.options[e.selectedIndex].text.trim() : ''; return; }
  if (e.shadowRoot) ver(e.shadowRoot); }); ver(document); return v; }"""

def clicar(pagina, caption):
    botao = pagina.locator(f"wa-button[caption='{caption}']:visible")
    if not botao.count():
        raise AssertionError(f"botao {caption!r} nao encontrado")
    botao.last.click()


def main(argv):
    if len(argv) != 2 or argv[1] not in ("2610", "2510"):
        print(__doc__, file=sys.stderr)
        return 2
    rel = argv[1]
    host, amb = os.environ[f"PLAB_{rel}_HOST"], os.environ[f"PLAB_{rel}_ENV"]
    url = f"http://{host}:1234/webapp/"
    pasta = os.path.join(os.environ.get("PLAB_HOME", "/opt/plab"), "evidencias", rel,
                         time.strftime("%Y%m%d-%H%M%S") + "-inicializar-reserva")
    limite = time.time() + int(os.environ.get("PLAB_INICIALIZAR_TEMPO", "1200"))
    with pw.navegador() as pagina:
        passos = pw.Passos(pagina, pasta)
        pw.parametros_iniciais(pagina, url, amb, "SIGAMDI")
        ultimo = None
        while time.time() < limite:
            pagina.wait_for_timeout(5_000)
            if any("/login" in f.url for f in pagina.frames):
                passos.captura("login")
                print(f"inicializar {rel}: base pronta (tela de login)")
                return 0
            texto = pagina.evaluate(TEXTO)
            if texto == ultimo:
                continue
            ultimo = texto
            if "Inconsist" in texto:
                passos.captura("inconsistencia")
                print(f"inicializar {rel}: FALHOU - o Protheus acusou inconsistencia: {texto[:300]}")
                print("  a base da reserva foi iniciada pela metade; recrie-a (ver README > Fonte reserva)")
                return 3
            if "Criação de empresa" in texto and "[Selecionar]" in texto:
                # A descricao abaixo das opcoes acompanha a opcao marcada.
                if "empresa teste padrão: 99/01" not in texto:
                    passos.captura("empresa-nao-teste")
                    raise AssertionError("a opcao marcada nao e a empresa TESTE 99/01")
                passos.captura("criacao-de-empresa")
                print("  criacao de empresa: TESTE 99/01 -> Selecionar")
                clicar(pagina, "Selecionar")
            elif "Selecione a localização" in texto and "[OK]" in texto:
                pais = pagina.evaluate(PAIS)
                if pais != "Brasil":
                    passos.captura("pais-errado")
                    raise AssertionError(f"pais selecionado {pais!r} (esperado: Brasil)")
                passos.captura("localizacao")
                print("  localizacao: Brasil -> OK")
                clicar(pagina, "OK")
            else:
                print(f"  aguardando: {texto[:120]}", flush=True)
        passos.captura("tempo-esgotado")
        print(f"inicializar {rel}: FALHOU - tempo esgotado sem chegar a tela de login")
        return 124


if __name__ == "__main__":
    sys.exit(main(sys.argv))
