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


_WEBSOCKETS = {}  # id(pagina) -> lista de contadores por websocket (diagnostico da issue #21)


def observar_websockets(pagina):
    """Conta quadros enviados/recebidos de cada websocket da pagina, desde antes do login. Guarda so
    quantidade e bytes, nunca o conteudo (os quadros levam usuario e senha)."""
    if id(pagina) in _WEBSOCKETS:
        return
    sockets = _WEBSOCKETS[id(pagina)] = []

    def _novo(ws):
        cont = {"url": ws.url.split("?", 1)[0], "env": 0, "env_b": 0, "rec": 0, "rec_b": 0, "fechado": False}
        sockets.append(cont)

        def _enviado(dado):
            cont["env"] += 1
            cont["env_b"] += len(dado)

        def _recebido(dado):
            cont["rec"] += 1
            cont["rec_b"] += len(dado)

        ws.on("framesent", _enviado)
        ws.on("framereceived", _recebido)
        ws.on("close", lambda _ws: cont.update(fechado=True))

    pagina.on("websocket", _novo)


def _quadros(pagina):
    return [dict(c) for c in _WEBSOCKETS.get(id(pagina), [])]


def _delta_quadros(antes, depois):
    linhas = []
    for i, d in enumerate(depois):
        a = antes[i] if i < len(antes) else {"env": 0, "env_b": 0, "rec": 0, "rec_b": 0}
        linhas.append(f"websocket {d['url']}: enviados {d['env'] - a['env']} ({d['env_b'] - a['env_b']} B), "
                      f"recebidos {d['rec'] - a['rec']} ({d['rec_b'] - a['rec_b']} B); "
                      f"antes do clique: enviados {a['env']}, recebidos {a['rec']}"
                      f"{', fechado' if d['fechado'] else ''}")
    return linhas or ["nenhum websocket observado na pagina"]


def entrar(pagina, url, ambiente, usuario, senha, tentativas=3):
    """Parametros iniciais + login PO UI, repetindo se o iframe do login vier como pagina de erro
    (observado logo apos uma compilacao: o /app-root demora a responder)."""
    observar_websockets(pagina)
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
    entrar_sessao(pagina, cfg)
    return descricao


AVISO_REQUISICAO = "Não foi possível enviar a requisição"

# Algum wa-menu-item visivel na pagina (o menu do modulo ja foi desenhado).
_JS_MENU_VISIVEL = """() => { let achou = false; const deep = (root) => root.querySelectorAll('*').forEach(e => {
  if (achou) return;
  if (e.tagName.toLowerCase() === 'wa-menu-item' && e.getBoundingClientRect().width > 0) { achou = true; return; }
  if (e.shadowRoot) deep(e.shadowRoot); }); deep(document); return achou; }"""


def entrar_sessao(pagina, cfg, tentativas=1, espera_ms=60_000):
    """Clica 'Entrar' na tela de sessao e repete quando a interface nova mostra o aviso
    'Nao foi possivel enviar a requisicao' com a tela ainda aberta. Visto na 2610 em 03 e
    04/11/2026, de 1 a 2 sessoes em 6; causa nao confirmada. No lab, repetir o clique nunca abriu a
    sessao (3 de 3 falharam): por isso o padrao e 1 tentativa, e quem resolve e o 'lab cenarios' ou o
    'lab smoke', que refazem desde o login ao ver "aviso de requisicao" na saida.
    Diagnostico (issue #21, 05/11/2026): o 'Entrar' vai pelo websocket do WebApp, nao por HTTP. Com
    o aviso, 0 quadros enviados e 0 recebidos (5 de 5); sem aviso, 12 a 20 em cada sentido (29 de 29).
    O WebApp desiste no navegador, antes de enviar. PLAB_DIAG_SESSAO=sim imprime tambem os logins bons."""
    botao = cfg.get_by_role("button", name=re.compile(r"^\s*Entrar\s*$"))

    def aviso_visivel():
        # O aviso (po-toaster) aparece no topo da pagina, fora do iframe da sessao (visto em
        # 04/11/2026): procura em todos os frames.
        for frame in pagina.frames:
            try:
                if frame.get_by_text(AVISO_REQUISICAO).first.is_visible():
                    return True
            except Exception:  # noqa: BLE001  (frame desanexado durante a busca)
                continue
        return False

    # Diagnostico da issue #21, impresso so quando o aviso aparece: o que aconteceu na rede e no
    # console durante o "Entrar". Guarda metodo, caminho (sem query, que pode levar token), codigo,
    # eventos de websocket e erros do console (cortados), nunca corpo de requisicao ou mensagem.
    falhas = []

    def _caminho(url):
        return url.split("?", 1)[0].split("#", 1)[0]

    def _falhou(req):
        falhas.append(f"{req.method} {_caminho(req.url)} -> falhou: {req.failure}")

    def _resposta(resp):
        falhas.append(f"{resp.request.method} {_caminho(resp.url)} -> HTTP {resp.status}")

    def _console(msg):
        if msg.type in ("error", "warning"):
            falhas.append(f"console {msg.type}: {' '.join(msg.text.split())[:200]}")

    def _websocket(ws):
        falhas.append(f"websocket aberto {_caminho(ws.url)}")
        ws.on("close", lambda _ws: falhas.append(f"websocket fechado {_caminho(ws.url)}"))
        ws.on("socketerror", lambda erro: falhas.append(f"websocket erro {_caminho(ws.url)}: {erro}"))

    eventos = (("requestfailed", _falhou), ("response", _resposta), ("console", _console),
               ("websocket", _websocket))
    for nome_ev, func in eventos:
        pagina.on(nome_ev, func)
    try:
        _entrar_sessao(pagina, cfg, botao, aviso_visivel, falhas, tentativas, espera_ms)
    finally:
        for nome_ev, func in eventos:
            pagina.remove_listener(nome_ev, func)
        if os.environ.get("PLAB_DIAG_SESSAO") == "sim":  # para comparar com uma entrada que deu certo
            for item in falhas[:40]:
                print(f"[ui] rede/console no Entrar: {item}", flush=True)


def _entrar_sessao(pagina, cfg, botao, aviso_visivel, falhas, tentativas, espera_ms):
    for tentativa in range(1, tentativas + 1):
        falhas.clear()
        antes = _quadros(pagina)
        botao.click()
        fim = time.time() + espera_ms / 1000.0
        aviso = False
        while time.time() < fim:
            try:
                # Sucesso = o menu do WebApp apareceu (ou o iframe da sessao saiu). Nao basta o botao
                # sumir: durante o envio ele vira "Carregando..." e volta a "Entrar" junto com o
                # aviso (04/11/2026). O iframe da sessao nao e removido no sucesso: esperar por isso
                # custava o prazo inteiro em todo login.
                if cfg.is_detached() or pagina.evaluate(_JS_MENU_VISIVEL):
                    break
                if aviso_visivel() and botao.is_visible():
                    aviso = True
                    break
            except Exception:  # noqa: BLE001  (frame trocando ou desanexado: a sessao abriu)
                break
            pagina.wait_for_timeout(500)
        falhas.extend(_delta_quadros(antes, _quadros(pagina)))
        if not aviso:
            return  # sessao aberta, ou sem aviso no prazo: quem chamou confere o menu
        print(f"[ui] aviso de requisicao na tela de sessao (tentativa {tentativa} de {tentativas}): "
              f"'{AVISO_REQUISICAO}'", flush=True)
        for item in falhas[:40]:
            print(f"[ui] rede/console no aviso: {item}", flush=True)
        if tentativa == tentativas:
            return
        # Espera o aviso sumir: senao a proxima tentativa veria o aviso antigo e desistiria na hora.
        fim_aviso = time.time() + 10
        while aviso_visivel() and time.time() < fim_aviso:
            pagina.wait_for_timeout(500)
        pagina.wait_for_timeout(1_000)


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


_JS_HELP = """(codigo) => {
  // Help do Protheus: texto "Help: <CODIGO>" num caption (com tags HTML) visivel.
  const norm = (s) => (s || '').replace(/<[^>]+>/g, ' ').replace(/\\s+/g, ' ').trim().toUpperCase();
  const alvo = ('HELP: ' + codigo).toUpperCase();
  let achou = false;
  const deep = (root) => root.querySelectorAll('*').forEach(e => {
    if (achou) return;
    const r = e.getBoundingClientRect();
    if (r.width > 0 && r.height > 0 && norm(e.getAttribute('caption')).includes(alvo)) { achou = true; return; }
    if (e.shadowRoot) deep(e.shadowRoot);
  });
  deep(document);
  return achou;
}"""


def help_visivel(pagina, codigo, timeout_ms=60_000):
    """Espera o Help com o codigo informado (ex.: 'RECNO') ficar visivel. Devolve True/False."""
    try:
        pagina.wait_for_function(_JS_HELP, arg=codigo, timeout=timeout_ms)
        return True
    except Exception:  # noqa: BLE001
        return False


def fechar_help(pagina, codigo, tentativas=5):
    """Fecha o Help com 'Fechar' (so fecha a mensagem; nada e gravado) e confere que sumiu."""
    for _ in range(tentativas):
        if existe_caption(pagina, "wa-button", "Fechar", 5_000):
            por_caption(pagina, "wa-button", "Fechar").click()
        try:
            pagina.wait_for_function("(c) => !(" + _JS_HELP + ")(c)", arg=codigo, timeout=5_000)
            return True
        except Exception:  # noqa: BLE001
            continue
    raise AssertionError(f"Help '{codigo}' continuou visivel apos {tentativas} cliques em 'Fechar'")


_JS_FORM_VISUALIZAR = """() => {
  // Formulario aberto pelo botao 'Visualizar': titulo terminado em '- VISUALIZAR' (MATA121:
  // 'Pedido de Compra - VISUALIZAR') ou iniciado por 'Visualização de' (MATA080: 'Visualização de
  // TES'), visivel. Devolve o titulo ou null.
  const norm = (s) => (s || '').replace(/<[^>]+>/g, '').replace(/\\s+/g, ' ').trim();
  let achado = null;
  const deep = (root) => root.querySelectorAll('*').forEach(e => {
    if (achado) return;
    const c = norm(e.getAttribute && e.getAttribute('caption'));
    const r = e.getBoundingClientRect ? e.getBoundingClientRect() : {width: 0, height: 0};
    if (r.width > 0 && r.height > 0 && (/-\\s*visualizar$/i.test(c) || /^visualiza[cç][aã]o d[eoa]s? /i.test(c))) {
      achado = c; return; }
    if (e.shadowRoot) deep(e.shadowRoot);
  });
  deep(document);
  return achado;
}"""


def visualizar_registro(pagina, timeout_ms=60_000):
    """Clica em 'Visualizar' no browse (registro posicionado, o primeiro) e espera o formulario em
    modo VISUALIZAR. Devolve o titulo do formulario. Visualizar nao grava nada."""
    por_caption(pagina, "wa-button", "Visualizar").click()
    return pagina.wait_for_function(_JS_FORM_VISUALIZAR, timeout=timeout_ms).json_value()


def fechar_visualizacao(pagina, tentativas=5):
    """Fecha o formulario de visualizacao com 'Cancelar' ou 'Fechar' (nunca 'Confirmar') e confere que
    o titulo '- VISUALIZAR' sumiu."""
    for _ in range(tentativas):
        for botao in ("Cancelar", "Fechar"):
            if existe_caption(pagina, "wa-button", botao, 3_000):
                por_caption(pagina, "wa-button", botao).click()
                break
        try:
            pagina.wait_for_function("() => !(" + _JS_FORM_VISUALIZAR + ")()", timeout=5_000)
            return True
        except Exception:  # noqa: BLE001
            continue
    raise AssertionError(f"formulario de visualizacao continuou aberto apos {tentativas} tentativas")


def confirmar_parametros(pagina, timeout_ms=30_000):
    """Tela 'Parametros' (Pergunte) que algumas rotinas abrem antes do browse (ex.: MATA150, MATA270,
    MATA450, MATA455). Confirma com 'OK' SEM alterar nenhum campo: so registra as respostas padrao no
    perfil de perguntas do usuario; nenhum dado de negocio e gravado. 'Cancelar' fecharia a rotina."""
    if not existe_caption(pagina, "*", "Parametros", timeout_ms):
        return False
    return clicar_ate_sumir(pagina, "OK", ("*", "Parametros"))


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


# ---------------------------------------------------------------------------------------------
# Gravacao (cenarios de lab/bin/lib/gravacoes.sh). So rodam com autorizacao registrada do dono e
# copia da base antes (plab snapshot); cada cenario inclui um registro de teste e o exclui pela
# propria rotina. Seletores observados no WebApp 26 / SmartClient HTML 10 em 04/11/2026.
# ---------------------------------------------------------------------------------------------

def campo_input(pagina, campo):
    """<input> interno do campo do formulario pelo atributo name do componente (ex.: 'M->ED_CODIGO')."""
    return pagina.locator(f'[name="{campo}"] input >> visible=true').first


def _mesmo_numero(atual, esperado):
    """Campo numerico com mascara brasileira: '1.234,50' == '1234.5'."""
    try:
        return float(atual.replace(".", "").replace(",", ".")) == float(esperado.replace(",", "."))
    except ValueError:
        return False


def preencher(pagina, campo, valor, timeout_ms=30_000):
    """Digita o valor no campo e sai com Tab (dispara a validacao do campo no AppServer).
    O <input> vem com espacos ate o tamanho do campo: sem selecionar tudo antes, o 1o caractere
    estoura o maxlength e o foco pula para o campo seguinte (visto em 04/11/2026 na FINA010)."""
    entrada = campo_input(pagina, campo)
    entrada.wait_for(state="visible", timeout=timeout_ms)
    for _ in range(3):
        entrada.click()
        pagina.wait_for_timeout(300)
        entrada.press("Control+a")
        entrada.press_sequentially(valor, delay=60)
        pagina.wait_for_timeout(300)
        pagina.keyboard.press("Tab")
        pagina.wait_for_timeout(1_200)
        atual = entrada.input_value().strip()
        if atual.upper() == valor.strip().upper() or _mesmo_numero(atual, valor):
            return True
    raise AssertionError(f"campo {campo}: valor '{entrada.input_value().strip()}' != '{valor}'")


def escolher(pagina, campo, opcao, timeout_ms=30_000):
    """Seleciona a opcao (texto visivel, ex.: 'D - Despesa') no <select> interno do wa-combobox."""
    lista = pagina.locator(f'[name="{campo}"] select').first
    lista.wait_for(state="attached", timeout=timeout_ms)
    lista.select_option(label=opcao)
    pagina.wait_for_timeout(1_000)
    atual = lista.evaluate("e => e.selectedIndex >= 0 ? e.options[e.selectedIndex].text.trim() : ''")
    if atual != opcao:
        raise AssertionError(f"campo {campo}: opcao '{atual}' != '{opcao}'")
    return True


_JS_LUPA = """() => {
  // Botao da lupa do campo 'Pesquisar' do browse: wa-button visivel dentro da area do
  // wa-text-input que contem o <input placeholder="Pesquisar">.
  const visivel = (e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  let caixa = null; const botoes = [];
  const deep = (root) => root.querySelectorAll('*').forEach(e => {
    const t = e.tagName.toLowerCase();
    if (t === 'wa-text-input' && visivel(e) && e.shadowRoot && e.shadowRoot.querySelector('input[placeholder="Pesquisar"]')) caixa = e.getBoundingClientRect();
    if (t === 'wa-button' && visivel(e)) botoes.push(e);
    if (e.shadowRoot) deep(e.shadowRoot);
  });
  deep(document);
  if (!caixa) return null;
  return botoes.find(b => { const r = b.getBoundingClientRect(); const x = r.left + r.width / 2, y = r.top + r.height / 2;
    return x > caixa.left && x < caixa.right && y > caixa.top && y < caixa.bottom; }) || null;
}"""

_JS_LINHAS = """() => {
  // Linhas de dados da grade visivel do browse (sem o cabecalho), como texto.
  let linhas = null;
  const deep = (root) => root.querySelectorAll('*').forEach(e => {
    if (linhas === null && e.tagName.toLowerCase() === 'wa-tgrid') { const b = e.getBoundingClientRect();
      if (b.width > 50 && b.height > 50) { linhas = [];
        (e.shadowRoot || e).querySelectorAll('tr').forEach((tr, k) => { const t = tr.innerText.replace(/\\s+/g, ' ').trim(); if (k > 0 && t) linhas.push(t); }); } }
    if (e.shadowRoot) deep(e.shadowRoot); });
  deep(document); return linhas || [];
}"""


def linhas_grade(pagina):
    return pagina.evaluate(_JS_LINHAS)


def pesquisar(pagina, texto, timeout_ms=30_000):
    """Pesquisa no campo 'Pesquisar' do browse e clica na lupa (o Enter nao pesquisa). A grade fica
    filtrada pelo texto. Devolve as linhas da grade que contem o texto."""
    entrada = pagina.locator('input[placeholder="Pesquisar"] >> visible=true').first
    entrada.wait_for(state="visible", timeout=timeout_ms)
    # Neste campo o Ctrl+A digita 'a' (visto em 04/11/2026): limpa com fill e digita tecla a tecla.
    # Logo depois de fechar um formulario os primeiros caracteres podem se perder ('000094' virou
    # '094' na MATA110): confere o texto e repete.
    for _ in range(3):
        entrada.click()
        entrada.fill("")
        pagina.wait_for_timeout(500)
        entrada.press_sequentially(texto, delay=60)
        pagina.wait_for_timeout(300)
        if entrada.input_value().strip() == texto:
            break
    else:
        raise AssertionError(f"campo 'Pesquisar' ficou com '{entrada.input_value()}' em vez de '{texto}'")
    lupa = pagina.evaluate_handle(_JS_LUPA).as_element()
    if not lupa:
        raise AssertionError("lupa do campo 'Pesquisar' nao encontrada")
    lupa.click()
    pagina.wait_for_timeout(2_000)
    # Sem resultado, a rotina mostra o Help PESQ01 e a grade fica sem filtro (visto em 04/11/2026).
    if help_visivel(pagina, "PESQ01", 3_000):
        fechar_help(pagina, "PESQ01")
        return []
    return [linha for linha in linhas_grade(pagina) if texto.upper() in linha.upper()]


def acao_browse(pagina, acao, timeout_ms=30_000):
    """Clica na acao do browse: botao visivel com o caption, ou item do menu 'Outras Ações'."""
    if existe_caption(pagina, "wa-button", acao, 3_000):
        por_caption(pagina, "wa-button", acao).click()
        return
    por_caption(pagina, "wa-button", "Outras Ações", timeout_ms).click()
    por_caption(pagina, "wa-menu-popup-item", acao, timeout_ms).click()


_JS_MENSAGEM = """(trechos) => {
  // Texto visivel (caption) que contem algum dos trechos, sem diferenciar caixa; devolve o texto.
  let achado = null;
  const deep = (root) => root.querySelectorAll('*').forEach(e => {
    if (achado) return;
    const c = (e.getAttribute && e.getAttribute('caption') || '').replace(/<[^>]+>/g, ' ').replace(/\\s+/g, ' ').trim();
    const r = e.getBoundingClientRect ? e.getBoundingClientRect() : {width: 0, height: 0};
    if (c && r.width > 0 && r.height > 0 && trechos.some(t => c.toLowerCase().includes(t.toLowerCase()))) { achado = c; return; }
    if (e.shadowRoot) deep(e.shadowRoot);
  });
  deep(document); return achado;
}"""


# Perguntas que a propria rotina faz depois do 'Confirmar' e que o cenario responde com 'Sim'
# (somente estas; qualquer outra pergunta faz o cenario falhar por tempo). FINA010: 'Confirma
# Exclusão?' (04/11/2026).
PERGUNTAS_SIM = ("Confirma Exclusão?",)


def confirmar_formulario(pagina, botao="Confirmar", titulo_form="", campo_reabre="", sucesso=("com sucesso",),
                         perguntas_sim=PERGUNTAS_SIM, timeout_ms=90_000):
    """Clica no botao de confirmacao do formulario ('Confirmar' no MVC, 'Salvar' nas telas antigas)
    e espera o resultado: a mensagem de sucesso (MVC: 'Registro inserido com sucesso.'); ou, se
    titulo_form for informado, o formulario com esse titulo fechar sem mensagem; ou, se
    campo_reabre for informado (telas antigas que reabrem a inclusao depois de salvar, ex.:
    MATA270), o valor desse campo mudar (formulario novo) e entao o formulario novo e cancelado.
    Responde 'Sim' so as perguntas conhecidas (perguntas_sim). Falha se aparecer um Help. Fecha a
    mensagem com 'Fechar' e devolve o texto dela."""
    antes = campo_input(pagina, campo_reabre).input_value() if campo_reabre else None
    por_caption(pagina, "wa-button", botao).click()
    fim = time.time() + timeout_ms / 1000.0
    resposta = None
    while time.time() < fim:
        if campo_reabre:
            try:
                agora = campo_input(pagina, campo_reabre).input_value(timeout=2_000)
            except Exception:  # noqa: BLE001  (formulario sendo redesenhado)
                agora = antes
            if agora != antes and not pagina.evaluate(_JS_MENSAGEM, ["Help:"]):
                clicar_ate_sumir(pagina, "Cancelar", ("*", titulo_form))
                return f"salvo; formulario reaberto ({campo_reabre} '{antes.strip()}' -> '{agora.strip()}') e cancelado"
        texto = pagina.evaluate(_JS_MENSAGEM, list(sucesso) + list(perguntas_sim) + ["Help:"])
        if texto and "help:" in texto.lower():
            raise AssertionError(f"formulario recusado: {texto[:200]}")
        if texto and any(p.lower() in texto.lower() for p in perguntas_sim):
            print(f"  [pergunta] '{texto}': Sim")
            clicar_ate_sumir(pagina, "Sim", ("*", texto))
            continue
        if texto:
            resposta = texto
            break
        if titulo_form and not campo_reabre and not pagina.evaluate(_JS_MENSAGEM, [titulo_form]):
            pagina.wait_for_timeout(2_000)  # da tempo de um Help tardio aparecer
            if not pagina.evaluate(_JS_MENSAGEM, ["Help:"]):
                return f"formulario '{titulo_form}' fechado sem mensagem"
        pagina.wait_for_timeout(1_000)
    if resposta is None:
        raise AssertionError(f"mensagem de sucesso nao apareceu em {timeout_ms // 1000}s")
    for _ in range(5):
        if existe_caption(pagina, "wa-button", "Fechar", 5_000):
            por_caption(pagina, "wa-button", "Fechar").click()
        try:
            pagina.wait_for_function("(t) => !(" + _JS_MENSAGEM + ")(t)", arg=list(sucesso), timeout=5_000)
            return resposta
        except Exception:  # noqa: BLE001
            continue
    raise AssertionError(f"mensagem '{resposta}' continuou visivel")


_JS_CELULA = """([coluna, linha]) => {
  // Centro da celula (coluna pelo titulo do cabecalho, linha 1 = 1o item) da grade de itens
  // (wa-tgetdados nas telas antigas, wa-tgrid no MVC) do formulario em primeiro plano: a ultima
  // visivel no DOM que tenha a coluna.
  let alvo = null;
  const deep = (root) => root.querySelectorAll('*').forEach(e => {
    if (['wa-tgetdados', 'wa-tgrid'].includes(e.tagName.toLowerCase())) { const b = e.getBoundingClientRect();
      if (b.width > 50 && b.height > 20) { const trs = (e.shadowRoot || e).querySelectorAll('tr');
        if (trs.length > linha) { const cab = Array.from(trs[0].children).map(c => c.innerText.trim());
          const k = cab.indexOf(coluna);
          if (k >= 0) { const q = trs[linha].children[k].getBoundingClientRect();
            alvo = {x: q.left + q.width / 2, y: q.top + q.height / 2, texto: trs[linha].children[k].innerText.trim()}; } } } }
    if (e.shadowRoot) deep(e.shadowRoot); });
  deep(document); return alvo;
}"""


def preencher_celula(pagina, coluna, valor, linha=1):
    """Grade de itens (wa-tgetdados nas telas antigas como a MATA110, wa-tgrid no MVC): clica na celula, digita (a
    digitacao abre o editor do campo, ex.: M->C1_PRODUTO) e confirma com Enter. Confere o texto
    da celula depois."""
    for _ in range(3):
        celula = pagina.evaluate(_JS_CELULA, [coluna, linha])
        if not celula:
            raise AssertionError(f"coluna '{coluna}' / linha {linha} nao encontrada na grade de itens")
        pagina.mouse.click(celula["x"], celula["y"])
        pagina.wait_for_timeout(1_500)
        pagina.keyboard.type(valor, delay=80)
        pagina.wait_for_timeout(800)
        pagina.keyboard.press("Enter")
        pagina.wait_for_timeout(2_500)
        texto = pagina.evaluate(_JS_CELULA, [coluna, linha])["texto"]
        if texto.upper() == valor.upper() or _mesmo_numero(texto, valor):
            return True
    raise AssertionError(f"celula '{coluna}': valor '{texto}' != '{valor}'")
