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
        limpar_login(self.pagina)  # nunca registrar a senha numa imagem
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
    opcoes = pagina.locator("#selectStartProg select option").evaluate_all("o => o.map(x => x.value)")
    if programa in opcoes:
        pagina.locator("#selectStartProg select").select_option(programa)
    else:
        # Programa fora da lista (ex.: SIGACFG): o campo aceita digitacao. Confere o valor final,
        # porque o autocompletar ja embaralhou digitacoes (ver plab_tir_compat).
        campo = pagina.locator("#selectStartProg input")
        campo.fill(programa)
        if campo.input_value() != programa:
            raise AssertionError(f"programa inicial digitado ficou {campo.input_value()!r}")
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
    campo_usuario = login.locator("input[name=login]")
    campo_senha = login.locator("input[name=password]")
    entrar_btn = login.get_by_role("button", name=re.compile(r"^\s*Entrar\s*$"))
    # O formulario pode redesenhar entre os preenchimentos (hidratacao): ja foi visto a senha cair
    # no campo de usuario (02/11/2026). Confere os dois campos e repete; nunca clica com valor errado.
    for _ in range(5):
        campo_usuario.fill(usuario)
        campo_senha.fill(senha)
        pagina.wait_for_timeout(500)
        if (campo_usuario.input_value() == usuario and campo_senha.input_value() == senha
                and entrar_btn.is_enabled()):
            entrar_btn.click()
            return login
        campo_usuario.fill("")
        campo_senha.fill("")
        pagina.wait_for_timeout(2_000)
    raise AssertionError("formulario de login nao manteve usuario e senha apos 5 tentativas")


def limpar_login(pagina):
    """Apaga o conteudo dos campos do login PO UI antes de uma captura de tela: uma captura de falha
    nao pode mostrar a senha, nem digitada no campo errado."""
    for f in pagina.frames:
        if "/login" in f.url:
            try:
                f.evaluate("() => document.querySelectorAll('input').forEach(i => { i.value = ''; })")
            except Exception:  # noqa: BLE001
                pass


def sessao(pagina, modulo, grupo="99", filial="01"):
    """Tela 'Boas-vindas' (iframe /session-settings): grupo, filial e modulo (codigo numerico).
    Os campos de codigo sao os po-lookup na ordem Grupo, Filial, Ambiente(modulo). A pos-condicao do
    modulo e conferida depois, no menu (modulo_no_menu), onde o nome e inequivoco.
    Devolve a descricao exibida ao lado do codigo do modulo (informativa)."""
    cfg = frame_por_url(pagina, "/session-settings")
    cfg.locator("input[name=environment_description]").wait_for(state="visible")
    codigos = cfg.locator("po-lookup input:not([name$='_description'])")
    desc_modulo = cfg.locator("input[name=environment_description]")
    for indice, valor in ((0, grupo), (1, filial), (2, str(int(modulo)))):
        campo = codigos.nth(indice)
        # Repete ate o codigo ficar: na 2510 o lookup ja devolveu o codigo anterior quando a
        # digitacao chegou antes de ele estar pronto, e a sessao abriu no modulo errado
        # (observado em 02/11/2026: "modulo 5 (Ativo Fixo)").
        for _ in range(5):
            if campo.input_value().strip() == valor:
                break
            anterior = desc_modulo.input_value().strip() if indice == 2 else ""
            campo.fill(valor)
            campo.press("Tab")
            pagina.wait_for_timeout(1_500)  # o lookup valida o codigo e preenche a descricao
            if indice == 2 and campo.input_value().strip() == valor:
                # espera a descricao do modulo acompanhar o codigo novo
                for _ in range(10):
                    if desc_modulo.input_value().strip() not in ("", anterior):
                        break
                    pagina.wait_for_timeout(500)
        if campo.input_value().strip() != valor:
            raise AssertionError(f"campo {indice} da sessao nao aceitou o codigo {valor!r}")
    descricao = desc_modulo.input_value().strip()
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


def fechar_aviso_informativo(pagina, trecho, timeout_ms=10_000):
    """Fecha com Esc um aviso apenas informativo (sem botoes de acao) cujo texto contem 'trecho', p.ex.
    'MV_1DUP' na base de demonstracao. Nao altera parametro nem dado. Devolve True se o aviso existia."""
    js = """(t) => { let achou = false; const deep = (root) => root.querySelectorAll('*').forEach(e => {
        const c = e.getAttribute && (e.getAttribute('caption') || ''); const b = e.getBoundingClientRect ? e.getBoundingClientRect() : {width: 0};
        if (!achou && c.includes(t) && b.width > 0) achou = true; if (!achou && e.shadowRoot) deep(e.shadowRoot); });
        deep(document); return achou; }"""
    try:
        pagina.wait_for_function(js, arg=trecho, timeout=timeout_ms)
    except Exception:  # noqa: BLE001
        return False
    pagina.keyboard.press("Escape")
    pagina.wait_for_function("(t) => !(" + js + ")(t)", arg=trecho, timeout=10_000)
    return True


def abrir_menu(pagina, caminho, timeout_ms=60_000):
    """Clica, em ordem, nos itens de menu do SIGAMDI (ex.: ["Atualizações", "Cadastros", "Produtos"])."""
    for rotulo in caminho:
        por_caption(pagina, "wa-menu-item", rotulo, timeout_ms).click()
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


def fechar_novidades(pagina, timeout_ms=10_000):
    """Dialogo 'Novidades do Produto' (propaganda de recursos) que algumas rotinas mostram ao abrir.
    Fecha com 'Fechar'; NUNCA 'Nao mostrar novamente', que grava preferencia do usuario."""
    if not existe_caption(pagina, "*", "Novidades do Produto", timeout_ms):
        return False
    return clicar_ate_sumir(pagina, "Fechar", ("*", "Novidades do Produto"))


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


def grade_carregada(pagina, timeout_ms=60_000):
    """Pos-condicao de 'browse carregado': uma grade (wa-tgrid) com mais de uma linha que esteja DE FATO
    visivel: o elemento no centro dela (elementFromPoint) precisa ser a propria grade ou um ancestral
    dela na cadeia de shadow hosts. Uma grade que existe no DOM mas esta coberta (tela em branco) nao
    conta — verificado em 02/11/2026, quando a checagem so por tamanho deu falso positivo."""
    try:
        pagina.wait_for_function("""() => {
          const naCadeia = (alvo, topo) => { for (let n = alvo; n; n = n.parentNode || n.host) { if (n === topo) return true; } return false; };
          let ok = false;
          const deep = (root) => root.querySelectorAll('*').forEach(e => {
            if (!ok && e.tagName.toLowerCase() === 'wa-tgrid') {
              const b = e.getBoundingClientRect(); const linhas = (e.shadowRoot || e).querySelectorAll('tr').length;
              if (b.width > 50 && b.height > 50 && linhas > 1) {
                const topo = document.elementFromPoint(b.left + b.width / 2, b.top + Math.min(b.height / 2, 120));
                if (topo && naCadeia(e, topo)) ok = true;
              }
            }
            if (!ok && e.shadowRoot) deep(e.shadowRoot); });
          deep(document); return ok; }""", timeout=timeout_ms)
        return True
    except Exception:  # noqa: BLE001
        return False


_JS_CONTEM = """([tag, trecho]) => {
  // Ultimo <tag> visivel cujo caption (sem tags HTML, sem '&' de atalho) contem o trecho.
  let achado = null;
  const deep = (root) => root.querySelectorAll('*').forEach(e => {
    if ((tag === '*' || e.tagName.toLowerCase() === tag)) {
      const c = (e.getAttribute('caption') || '').replace(/<[^>]+>/g, '').replace(/&/g, '');
      const b = e.getBoundingClientRect();
      if (c.includes(trecho) && b.width > 0 && b.height > 0) achado = e;
    }
    if (e.shadowRoot) deep(e.shadowRoot);
  });
  deep(document);
  return achado;
}"""


_JS_FECHAR_ROTINA = """() => {
  // Botao 'X' do cabecalho da rotina aberta: wa-button sem caption, logo abaixo da barra do topo,
  // no canto direito da janela.
  let achado = null;
  const largura = window.innerWidth;
  const deep = (root) => root.querySelectorAll('wa-button').forEach(e => {
    const b = e.getBoundingClientRect();
    if (b.width > 0 && b.y > 60 && b.y < 90 && b.x > largura - 50 && !(e.getAttribute('caption') || '').trim()) achado = e;
    if (e.shadowRoot) deep(e.shadowRoot);
  });
  deep(document);
  return achado;
}"""


def erro_de_licenca(pagina):
    """Texto do erro do License Server na tela (ex.: 'Erro de servidor de licença:-20'), ou ''.
    Com licencas de desenvolvimento, sessoes encerradas sem 'Finalizar' prendem a licenca."""
    el = pagina.evaluate_handle(_JS_CONTEM, ["*", "servidor de licen"]).as_element()
    return (el.get_attribute("caption") or "").strip() if el else ""


def sair_do_sistema(pagina, timeout_ms=20_000):
    """Encerra a sessao pelo botao 'Log Off' do topo e 'Finalizar' no dialogo, para o AppServer
    devolver a licenca. Fechar o navegador sem isso prende a licenca de desenvolvimento ate o
    License Server reiniciar (verificado em 02/11/2026: '-20 Excedeu numero de licencas' na 3a ou
    4a sessao seguida). Os cliques sao feitos no proprio componente porque a rotina aberta cobre o
    botao. Pos-condicao: a tela 'Parametros Iniciais' volta. Devolve True se saiu."""
    # Laco com pos-condicao: um clique antes da hidratacao do dialogo nao tem efeito.
    # 'Finalizar' so depois de clicar no 'Log Off': formularios de rotina tambem tem botao
    # 'Finalizar' e ele grava (visto em 03/11/2026 na Politica de senhas do SIGACFG).
    parametros = pagina.locator(".startParameters wa-button", has_text="OK")
    pediu_logoff = False
    fim = time.time() + timeout_ms / 1000.0 * 3
    while time.time() < fim:
        try:
            if parametros.is_visible():
                return True
            fechar_novidades(pagina, 1_000)  # dialogo modal na frente do Log Off
            alvo = pediu_logoff and pagina.evaluate_handle(_JS_CONTEM, ["wa-button", "Finalizar"]).as_element()
            if not alvo:
                alvo = pagina.evaluate_handle(_JS_CONTEM, ["wa-button", "Log Off"]).as_element()
                pediu_logoff = pediu_logoff or bool(alvo)
            if not alvo:
                # SmartClient HTML 10 (2510): com rotina aberta o topo mostra 'Sair' desabilitado e
                # nao existe 'Log Off'. Fecha a rotina pelo 'X' do cabecalho dela (canto superior
                # direito, abaixo da barra) e o 'Log Off' volta (verificado em 02/11/2026).
                alvo = pagina.evaluate_handle(_JS_FECHAR_ROTINA).as_element()
            if alvo:
                alvo.evaluate("e => e.click()")
        except Exception:  # noqa: BLE001  (pagina trocando de tela no meio da busca)
            pass
        pagina.wait_for_timeout(3_000)
    return False


def aba_aberta(pagina, titulo, timeout_ms=60_000):
    """Pos-condicao de 'rotina aberta': existe a aba com o titulo da rotina."""
    try:
        pagina.wait_for_function(_JS_ABA, arg=titulo, timeout=timeout_ms)
        return True
    except Exception:  # noqa: BLE001
        return False
