"""Helpers Playwright do Protheus 2610 Lab: complemento do TIR para o WebApp 26 / SmartClient HTML 10.

Por que existe: em 02/11/2026 o TIR 2.14.12 nao conclui o Setup nestes WebApps (campo de ambiente
com autocompletar e clique no wa-button OK sem efeito). O Playwright atravessa shadow DOM aberto,
espera acionabilidade (https://playwright.dev/python/docs/navigations) e localiza o iframe do login
PO UI. Estes helpers fazem somente leitura: login, entrada no modulo, abrir rotina, conferir titulo.

Regras: senha so do secret /run/secrets; nunca em log, captura com campo preenchido ou argumento.
Seletores observados nas telas reais (ver evidencias/diag); se a tela mudar, falhar com captura.
Os componentes do WebApp (wa-*) guardam o rotulo no atributo "caption" (com atalho <u>x</u>):
por isso os elementos sao localizados por caption normalizado, nao pelo texto visivel.
author: daniel.montagna
"""
import os
import re
import time
from contextlib import contextmanager

from playwright.sync_api import sync_playwright

TEMPO_PADRAO_MS = int(os.environ.get("PLAB_PW_TIMEOUT_MS", "60000"))

# Procura (inclusive dentro de shadow roots) o ULTIMO elemento visivel <tag> cujo caption, sem tags
# HTML e sem contador "(N)" no fim, seja igual ao rotulo (sem diferenciar caixa). O ultimo e o do
# dialogo do topo: com dialogos empilhados, o primeiro "Cancelar" pertence ao de baixo e nao reage.
_JS_POR_CAPTION = """([tag, rotulo]) => {
  const norm = (s) => (s || '').replace(/<[^>]+>/g, '').replace(/\\s*\\(\\d+\\)\\s*$/, '').trim().toLowerCase();
  const alvo = rotulo.trim().toLowerCase();
  // Visivel = tem area na tela e nao esta oculto. (offsetParent e null dentro de dialogos com
  // position:fixed, entao nao serve para os componentes do WebApp.)
  const visivel = (e) => { const r = e.getBoundingClientRect(); const s = getComputedStyle(e);
    return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none'; };
  let achado = null;
  const deep = (root) => root.querySelectorAll('*').forEach(e => {
    if ((tag === '*' || e.tagName.toLowerCase() === tag) && norm(e.getAttribute('caption')) === alvo && visivel(e)) { achado = e; }
    if (e.shadowRoot) deep(e.shadowRoot);
  });
  deep(document);
  return achado;
}"""


def senha_admin(release):
    with open(f"/run/secrets/plab_{release}_admin_password", encoding="utf-8") as f:
        senha = f.read().strip("\r\n")
    if not senha:
        raise RuntimeError(f"senha do Admin da {release} vazia no secret")
    return senha


@contextmanager
def navegador(headless=True):
    with sync_playwright() as p:
        nav = p.chromium.launch(executable_path=os.environ.get("PLAB_CHROME_BIN", "/opt/chrome/chrome"),
                                headless=headless)
        try:
            pagina = nav.new_page(viewport={"width": 1367, "height": 769}, locale="pt-BR")
            pagina.set_default_timeout(TEMPO_PADRAO_MS)
            yield pagina
        finally:
            nav.close()


class Passos:
    """Registra capturas numeradas em uma pasta de evidencias."""

    def __init__(self, pagina, pasta):
        self.pagina, self.pasta, self.n = pagina, pasta, 0
        os.makedirs(pasta, exist_ok=True)

    def captura(self, nome):
        self.n += 1
        caminho = os.path.join(self.pasta, f"{self.n:02d}-{nome}.png")
        self.pagina.screenshot(path=caminho)
        print(f"  [captura] {os.path.basename(caminho)}")
        return caminho


def por_caption(pagina, tag, rotulo, timeout_ms=30_000):
    """Espera e devolve o elemento <tag> visivel com o caption informado."""
    return pagina.wait_for_function(_JS_POR_CAPTION, arg=[tag, rotulo], timeout=timeout_ms).as_element()


def existe_caption(pagina, tag, rotulo, timeout_ms):
    try:
        por_caption(pagina, tag, rotulo, timeout_ms)
        return True
    except Exception:  # noqa: BLE001
        return False


def sumiu_caption(pagina, tag, rotulo, timeout_ms):
    """Espera o elemento <tag> com o caption deixar de existir/estar visivel."""
    try:
        pagina.wait_for_function("(a) => !(" + _JS_POR_CAPTION + ")(a)", arg=[tag, rotulo], timeout=timeout_ms)
        return True
    except Exception:  # noqa: BLE001
        return False


def clicar_ate_sumir(pagina, botao, alvo, tentativas=5):
    """Clica no wa-button 'botao' ate o elemento 'alvo' (tag, rotulo) sumir.
    Necessario porque controles do WebApp aparecem antes de os listeners estarem prontos
    (hidratacao: o clique 'acontece' mas nao tem efeito). Falha se nao sumir."""
    for _ in range(tentativas):
        if existe_caption(pagina, "wa-button", botao, 5_000):
            por_caption(pagina, "wa-button", botao).click()
        if sumiu_caption(pagina, alvo[0], alvo[1], 5_000):
            return True
    raise AssertionError(f"'{alvo[1]}' continuou visivel apos {tentativas} cliques em '{botao}'")


def frame_por_url(pagina, trecho, timeout_ms=TEMPO_PADRAO_MS):
    """Espera um frame cuja URL contenha o trecho (o login PO UI roda num iframe /app-root/...)."""
    fim = time.time() + timeout_ms / 1000.0
    while time.time() < fim:
        for f in pagina.frames:
            if trecho in f.url:
                return f
        pagina.wait_for_timeout(250)
    raise TimeoutError(f"frame com '{trecho}' nao apareceu; frames={[f.url for f in pagina.frames]}")


def parametros_iniciais(pagina, url, ambiente, programa="SIGAMDI"):
    """Tela 'Parametros Iniciais': seleciona programa e ambiente pelos <select> internos
    (digitar embaralha o valor por causa do autocompletar) e confirma com OK."""
    pagina.goto(url, wait_until="load")
    ok = pagina.locator(".startParameters wa-button", has_text="OK")
    ok.wait_for(state="visible")
    pagina.locator("#selectStartProg select").select_option(programa)
    pagina.locator("#selectEnv select").select_option(ambiente)
    atual = pagina.locator("#selectEnv input").input_value()
    if atual != ambiente:
        raise AssertionError(f"ambiente selecionado {atual!r} != {ambiente!r}")
    ok.click()


def entrar(pagina, url, ambiente, usuario, senha, tentativas=3):
    """Parametros iniciais + login PO UI, repetindo se o iframe do login vier como pagina de erro
    (observado logo apos uma compilacao: o /app-root demora a responder)."""
    for tentativa in range(1, tentativas + 1):
        parametros_iniciais(pagina, url, ambiente)
        try:
            return login_po_ui(pagina, usuario, senha)
        except TimeoutError:
            # Repete se o iframe deu erro ou ficou preso no pre-carregamento (/preindex_...).
            presos = [f.url for f in pagina.frames if f.url.startswith("chrome-error:") or "/preindex_" in f.url]
            if tentativa == tentativas or not presos:
                raise
            pagina.wait_for_timeout(5_000 * tentativa)
    return None


def login_po_ui(pagina, usuario, senha, timeout_ms=120_000):
    """Tela de login PO UI (iframe /app-root/.../login). Logo apos uma compilacao o /app-root pode
    levar mais de um minuto para responder (observado em 2610 e 2510)."""
    login = frame_por_url(pagina, "/login", timeout_ms=timeout_ms)
    login.locator("input[name=login]").fill(usuario)
    login.locator("input[name=password]").fill(senha)
    login.get_by_role("button", name=re.compile(r"^\s*Entrar\s*$")).click()
    return login


def sessao(pagina, modulo, grupo="99", filial="01"):
    """Tela 'Boas-vindas' (iframe /session-settings): grupo, filial e modulo (codigo numerico).
    Os campos de codigo sao os po-lookup na ordem Grupo, Filial, Ambiente(modulo). A pos-condicao do
    modulo e conferida depois, no menu (modulo_no_menu), onde o nome e inequivoco.
    Devolve a descricao exibida ao lado do codigo do modulo (informativa)."""
    cfg = frame_por_url(pagina, "/session-settings")
    cfg.locator("input[name=environment_description]").wait_for(state="visible")
    codigos = cfg.locator("po-lookup input:not([name$='_description'])")
    for indice, valor in ((0, grupo), (1, filial), (2, str(int(modulo)))):
        campo = codigos.nth(indice)
        if campo.input_value().strip() != valor:
            campo.fill(valor)
            campo.press("Tab")
            pagina.wait_for_timeout(1_500)  # o lookup valida o codigo e preenche a descricao
    descricao = cfg.locator("input[name=environment_description]").input_value().strip()
    cfg.get_by_role("button", name=re.compile(r"^\s*Entrar\s*$")).click()
    return descricao


def modulo_no_menu(pagina, nome, timeout_ms=60_000):
    """Pos-condicao da entrada: o menu mostra o nome do modulo (wa-text-view com o caption)."""
    return existe_caption(pagina, "wa-text-view", nome, timeout_ms)


def fechar_avisos(pagina, tentativas=3, timeout_ms=15_000):
    """Fecha avisos modais do WebApp (ex.: 'base de Desenvolvimento') pelo botao Fechar,
    conferindo que cada aviso realmente fechou."""
    fechados = 0
    for _ in range(tentativas):
        if not existe_caption(pagina, "wa-button", "Fechar", timeout_ms):
            break
        clicar_ate_sumir(pagina, "Fechar", ("wa-button", "Fechar"))
        fechados += 1
    return fechados


def abrir_menu(pagina, caminho):
    """Clica, em ordem, nos itens de menu do SIGAMDI (ex.: ["Atualizações", "Cadastros", "Produtos"])."""
    for rotulo in caminho:
        por_caption(pagina, "wa-menu-item", rotulo).click()
        pagina.wait_for_timeout(700)


def confirmar_ambiente(pagina, timeout_ms=15_000):
    """Modal 'TOTVS Linha Protheus.' (Data base, Grupo, Filial, Ambiente) que alguns fluxos mostram ao
    abrir uma rotina pelo menu (o mesmo tratado no TIR, PR #2155). Ele so confirma os parametros da
    sessao. Para nao confundir com o 'Confirmar' do dialogo Moedas (que grava cotacoes), exige o
    titulo do modal E o campo 'Data base'."""
    if not existe_caption(pagina, "*", "TOTVS Linha Protheus.", timeout_ms):
        return False
    if not (existe_caption(pagina, "*", "Data base*", 2_000) or existe_caption(pagina, "*", "Data base", 1_000)):
        return False
    return clicar_ate_sumir(pagina, "Confirmar", ("*", "TOTVS Linha Protheus."))


def cancelar_moedas(pagina, timeout_ms=20_000):
    """Dialogo 'Moedas' (cotacoes do dia) aparece no 1o acesso do dia a rotinas de cadastro.
    'Confirmar' GRAVA cotacoes; para manter o teste somente leitura, usa-se 'Cancelar'."""
    if not existe_caption(pagina, "wa-text-view", "Moedas", timeout_ms):
        return False
    return clicar_ate_sumir(pagina, "Cancelar", ("wa-text-view", "Moedas"))


_JS_ABA = """(titulo) => {
  // Aba da rotina: caption == titulo, ou titulo seguido de "[versao]" (SmartClient HTML 10:
  // "Produtos [02.9.0005]").
  const norm = (s) => (s || '').replace(/<[^>]+>/g, '').trim().toLowerCase();
  const alvo = titulo.trim().toLowerCase();
  let achado = null;
  const deep = (root) => root.querySelectorAll('*').forEach(e => {
    const t = e.tagName.toLowerCase();
    if ((t === 'wa-tab-page' || t === 'wa-tab-button') && e.getAttribute('caption') !== null) {
      const c = norm(e.getAttribute('caption'));
      if (c === alvo || c.startsWith(alvo + ' [')) { achado = e; }
    }
    if (e.shadowRoot) deep(e.shadowRoot);
  });
  deep(document);
  return achado;
}"""


def aba_aberta(pagina, titulo, timeout_ms=60_000):
    """Pos-condicao de 'rotina aberta': existe a aba com o titulo da rotina."""
    try:
        pagina.wait_for_function(_JS_ABA, arg=titulo, timeout=timeout_ms)
        return True
    except Exception:  # noqa: BLE001
        return False
