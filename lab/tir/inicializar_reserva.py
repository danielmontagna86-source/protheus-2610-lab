"""Inicializa a base VAZIA da fonte reserva (imagens feliperaposo/*, issue #3). O plab chama as
etapas nesta ordem, com a importacao do Admin (feita no host) entre a 1a e a 2a:
  python inicializar_reserva.py <2610|2510> assistente
  python inicializar_reserva.py <2610|2510> configurador
  python inicializar_reserva.py <2610|2510> primeiro-acesso [modulo ...]

Etapa "configurador": primeira entrada no SIGACFG. A empresa 99 nasce sem dicionario (SX2, SX3...);
escolhe "Criar a partir do systemload" (pacote da imagem, cerca de 3 min), o tipo de ambiente
"3 - Desenvolvimento" e trata os dialogos do primeiro uso (tratar_dialogo). Sai pelo Log Off.

Etapa "assistente" (padrao): abre o WebApp e segue o assistente do Protheus ate a tela de login, sem
fazer login.

Telas tratadas (vistas na 2610 em 05/11/2026):
  1. "Criacao de empresa": confere que a opcao marcada e a empresa TESTE 99/01 e clica Selecionar.
  2. "Selecione a localizacao": confere que o pais e Brasil e clica OK.
  3. "Aguarde, inicializando o sistema" e "Verificando atualizacoes": so espera (cerca de 3 min).
  4. Tela de login (iframe /login): fim, codigo 0.
Base ja inicializada: o login aparece direto, codigo 0 (pode rodar de novo sem efeito).
"Inconsistencia" (base iniciada pela metade, por exemplo por uma chamada ao /app-root/ antes deste
passo): codigo 3; a base da reserva precisa ser recriada. Tempo esgotado: 124. Erro: 1.

Etapa "primeiro-acesso": entra com o Admin em cada modulo (padrao: 5 2 4 6, os do smoke e dos
cenarios) e trata o que so aparece no primeiro uso da base ("Escolha a Localizacao" vem com Angola
marcada: escolhe Brasil, confere e clica Ok; aviso de base de Desenvolvimento; Moedas com Cancelar,
que nao grava). Com o aviso da issue #21 na tela de sessao, refaz desde o login (ate 5 vezes).
Sai de cada sessao pelo Log Off (licenca). Dialogo desconhecido: captura e codigo 4.
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

# Escolhe "Brasil" no <select> visivel que tem essa opcao (combobox do dialogo classico), avisando o
# componente pelos eventos input/change. Devolve o texto da opcao marcada depois da troca.
ESCOLHER_BRASIL = """() => { let feito = null; const ver = (r) => r.querySelectorAll('*').forEach(e => {
  if (feito !== null) return;
  if (e.tagName === 'SELECT' && e.getBoundingClientRect().width > 0) {
    const i = Array.from(e.options).findIndex(o => o.text.trim() === 'Brasil');
    if (i >= 0) { e.selectedIndex = i; e.dispatchEvent(new Event('input', {bubbles: true}));
      e.dispatchEvent(new Event('change', {bubbles: true})); feito = e.options[e.selectedIndex].text.trim(); }
    return; }
  if (e.shadowRoot) ver(e.shadowRoot); }); ver(document); return feito; }"""


# Escolhe no <select> visivel a primeira opcao cujo texto contem `trecho` (combobox do dialogo
# classico), avisando o componente pelos eventos input/change. Devolve o texto marcado ou null.
ESCOLHER_OPCAO = """(trecho) => { let feito = null; const ver = (r) => r.querySelectorAll('*').forEach(e => {
  if (feito !== null) return;
  if (e.tagName === 'SELECT' && e.getBoundingClientRect().width > 0) {
    const i = Array.from(e.options).findIndex(o => o.text.includes(trecho));
    if (i >= 0) { e.selectedIndex = i; e.dispatchEvent(new Event('input', {bubbles: true}));
      e.dispatchEvent(new Event('change', {bubbles: true})); feito = e.options[e.selectedIndex].text.trim(); }
    return; }
  if (e.shadowRoot) ver(e.shadowRoot); }); ver(document); return feito; }"""


def _pagina_de_erro(pagina):
    """True se algum frame (o login fica num iframe do /app-root) mostra pagina de erro: 502 do HAProxy
    ou erro do navegador. O iframe nao tenta de novo sozinho."""
    for frame in pagina.frames:
        if frame.url.startswith("chrome-error:"):
            return True
        try:
            if "Bad Gateway" in frame.locator("body").inner_text(timeout=2_000):
                return True
        except Exception:  # noqa: BLE001  (frame desanexado ou sem body)
            continue
    return False


def clicar(pagina, caption):
    botao = pagina.locator(f"wa-button[caption='{caption}']:visible")
    if not botao.count():
        raise AssertionError(f"botao {caption!r} nao encontrado")
    botao.last.click()


# Botoes que indicam um dialogo esperando resposta (captions dos wa-button).
BOTOES_DIALOGO = ("[Ok]", "[OK]", "[Sim]", "[Não]", "[&Sim]", "[&Não]", "[Finalizar]", "[<u>F</u>inalizar]",
                  "[Selecionar]", "[Confirmar]", "[Avançar]", "[Cancelar]", "[Fechar]", "[Concluir]")


def localizacao_brasil(pagina, passos, texto):
    """Dialogos de pais do primeiro uso: 'Escolha a Localizacao' (vem com Angola, botao Ok) e
    'Selecione a localizacao' (vem com Brasil, botao OK). Marca Brasil, confere e confirma."""
    marcado = pagina.evaluate(ESCOLHER_BRASIL)
    pagina.wait_for_timeout(1_000)
    if marcado != "Brasil" or pagina.evaluate(PAIS) != "Brasil":
        passos.captura("localizacao-falhou")
        raise AssertionError(f"nao consegui marcar Brasil (marcado: {marcado!r})")
    passos.captura("localizacao-brasil")
    clicar(pagina, "OK" if "[OK]" in texto else "Ok")


def clicar_texto(pagina, texto):
    """Clica no elemento visivel cujo texto e exatamente `texto` (rotulo de radio do dialogo classico)."""
    alvo = pagina.get_by_text(texto, exact=True)
    for i in range(alvo.count()):
        if alvo.nth(i).is_visible():
            alvo.nth(i).click()
            return
    raise AssertionError(f"texto {texto!r} nao encontrado na tela")


def tratar_dialogo(pagina, passos, texto, quem):
    """Dialogos do primeiro uso da base vazia (vistos na 2610 em 06/11/2026). Devolve True se tratou."""
    if "Criar a partir do systemload" in texto and "[Selecionar]" in texto:
        # A empresa 99 nasce sem dicionario (SX2, SX3...): carga a partir do pacote da imagem.
        clicar_texto(pagina, "Criar a partir do systemload.")
        pagina.wait_for_timeout(1_000)
        if "Finaliza o sistema" in pagina.evaluate(TEXTO):
            passos.captura("systemload-nao-marcado")
            raise AssertionError("a opcao 'Criar a partir do systemload' nao ficou marcada")
        passos.captura("dicionario-systemload")
        print(f"  {quem}: dicionario ausente -> Criar a partir do systemload (cerca de 3 min)")
        clicar(pagina, "Selecionar")
        return True
    if "Escolha a Localização" in texto or "Selecione a localização" in texto:
        localizacao_brasil(pagina, passos, texto)
        print(f"  {quem}: localizacao Brasil -> OK")
        return True
    if "Definição de tipo de ambiente" in texto and "[Confirmar]" in texto:
        # Lab de desenvolvimento: o mesmo tipo da base principal das imagens.
        marcado = pagina.evaluate(ESCOLHER_OPCAO, "Desenvolvimento")
        pagina.wait_for_timeout(1_000)
        if not marcado or "Desenvolvimento" not in (pagina.evaluate(PAIS) or ""):
            passos.captura("tipo-ambiente-falhou")
            raise AssertionError(f"nao consegui marcar o tipo Desenvolvimento (marcado: {marcado!r})")
        passos.captura("tipo-ambiente")
        print(f"  {quem}: tipo de ambiente {marcado} -> Confirmar")
        clicar(pagina, "Confirmar")
        return True
    if "[Moedas]" in texto and "[Confirmar]" in texto:
        # Cotacoes do dia: Confirmar GRAVA; o lab sempre cancela (plab_pw.cancelar_moedas).
        if not pw.cancelar_moedas(pagina):
            passos.captura("moedas-falhou")
            raise AssertionError("dialogo Moedas nao fechou com Cancelar")
        print(f"  {quem}: Moedas -> Cancelar (nao grava cotacoes)")
        return True
    if "utiliza base de Desenvolvimento" in texto and "[Fechar]" in texto:
        print(f"  {quem}: aviso de base de Desenvolvimento -> Fechar")
        clicar(pagina, "Fechar")
        return True
    return False


def configurador(rel, url, amb, pasta):
    """Primeira entrada no SIGACFG: a empresa 99 nasce sem dicionario (SX2, SX3...) e o Configurador
    oferece 'Criar a partir do systemload' (pacote da imagem). Espera a carga e trata as telas
    conhecidas; tela desconhecida: captura e codigo 4."""
    usuario = os.environ.get("PLAB_ADMIN_USER", "Admin")
    limite = time.time() + int(os.environ.get("PLAB_SYSTEMLOAD_TEMPO", "5400"))
    with pw.navegador() as pagina:
        passos = pw.Passos(pagina, os.path.join(pasta, "configurador"))
        saiu = False
        try:
            pw.parametros_iniciais(pagina, url, amb, "SIGACFG")
            pw.login_po_ui(pagina, usuario, pw.senha_admin(rel))
            cfg = pw.frame_por_url(pagina, "/session-settings")
            cfg.locator("input[name=environment_description]").wait_for(state="visible")
            pw.entrar_sessao(pagina, cfg)
            ultimo, desde = None, time.time()
            while time.time() < limite:
                pagina.wait_for_timeout(5_000)
                if pagina.evaluate(pw._JS_MENU_VISIVEL):  # noqa: SLF001
                    pw.fechar_avisos(pagina)
                    passos.captura("menu")
                    print(f"  configurador: menu aberto ({int(time.time() - desde)} s)")
                    return 0
                texto = pagina.evaluate(TEXTO)
                if texto == ultimo:
                    continue
                ultimo = texto
                if tratar_dialogo(pagina, passos, texto, "configurador"):
                    ultimo = None
                elif not any(b in texto for b in BOTOES_DIALOGO):
                    # Sem botao de dialogo na tela: processamento em andamento. A tela de sessao ao
                    # fundo mostra "Carregando..." o tempo todo, por isso nao serve de sinal.
                    passos.captura("andamento")
                    print(f"  configurador: aguardando ({int(time.time() - desde)} s): {texto[-200:]}", flush=True)
                else:
                    passos.captura("tela-desconhecida")
                    print(f"inicializar {rel}: PAROU - tela nao tratada no configurador: {texto[-600:]}")
                    return 4
            passos.captura("tempo-esgotado")
            print(f"inicializar {rel}: FALHOU - configurador sem menu no tempo limite")
            return 124
        finally:
            saiu = pw.sair_do_sistema(pagina)
            print(f"  configurador: saida do sistema {'ok' if saiu else 'NAO confirmada'}")


def _aviso_requisicao(pagina):
    """Aviso da issue #21 (WebApp 26) visivel com a tela de sessao ainda aberta."""
    if not any("/session-settings" in f.url for f in pagina.frames):
        return False
    for frame in pagina.frames:
        try:
            if frame.get_by_text(pw.AVISO_REQUISICAO).first.is_visible():
                return True
        except Exception:  # noqa: BLE001  (frame desanexado durante a busca)
            continue
    return False


def _um_modulo(rel, url, amb, passos, usuario, senha, modulo):
    """Uma sessao no modulo. Devolve 0 (menu aberto e saida confirmada), "repetir" (aviso da issue
    #21: nenhuma sessao aberta, refazer desde o login) ou um codigo de erro."""
    with pw.navegador() as pagina:
        passos.pagina = pagina
        sessao_aberta = False
        try:
            try:
                pw.entrar(pagina, url, amb, usuario, senha)
            except Exception as erro:  # noqa: BLE001  (pagina de erro passageira, ex.: 502 apos compilar)
                print(f"  modulo {modulo}: WebApp/login nao abriu ({type(erro).__name__}); refazendo", flush=True)
                pagina.wait_for_timeout(10_000)
                return "repetir"
            try:
                descricao = pw.sessao(pagina, modulo)
            except AssertionError as erro:
                descricao = ""
                print(f"  modulo {modulo}: sessao sem menu ainda ({erro}); conferindo dialogos")
            if _aviso_requisicao(pagina):
                print(f"  modulo {modulo}: aviso de requisicao (issue #21); refazendo desde o login")
                return "repetir"
            sessao_aberta = True
            fim = time.time() + 180
            menu = False
            while time.time() < fim:
                if pagina.evaluate(pw._JS_MENU_VISIVEL):  # noqa: SLF001 (mesma conferencia do plab_pw)
                    menu = True
                    break
                texto = pagina.evaluate(TEXTO)
                if tratar_dialogo(pagina, passos, texto, f"modulo {modulo}"):
                    pagina.wait_for_timeout(3_000)
                elif any(b in texto for b in BOTOES_DIALOGO):
                    passos.captura("tela-desconhecida")
                    print(f"inicializar {rel}: PAROU - tela nao tratada no modulo {modulo}: {texto[-600:]}")
                    return 4
                pagina.wait_for_timeout(2_000)
            if not menu:
                passos.captura("sem-menu")
                print(f"inicializar {rel}: FALHOU - modulo {modulo} nao abriu o menu; ultimo texto: "
                      f"{pagina.evaluate(TEXTO)[-300:]}")
                return 4
            pw.fechar_avisos(pagina)
            passos.captura("menu")
            print(f"  modulo {modulo}: menu aberto ({descricao or 'sem descricao'})")
        finally:
            saiu = pw.sair_do_sistema(pagina)
            if sessao_aberta or saiu:
                print(f"  modulo {modulo}: saida do sistema {'ok' if saiu else 'NAO confirmada'}")
        return 0 if saiu else 5


def primeiro_acesso(rel, url, amb, pasta, modulos):
    """Entra com o Admin em cada modulo e trata os dialogos do primeiro uso (tratar_dialogo)."""
    usuario = os.environ.get("PLAB_ADMIN_USER", "Admin")
    senha = pw.senha_admin(rel)
    for modulo in modulos:
        rc = "repetir"
        for tentativa in range(1, 6):
            passos = pw.Passos(None, os.path.join(pasta, f"modulo-{modulo}-t{tentativa}"))
            rc = _um_modulo(rel, url, amb, passos, usuario, senha, modulo)
            if rc != "repetir":
                break
        if rc == "repetir":
            print(f"inicializar {rel}: FALHOU - modulo {modulo}: sessao nao abriu em 5 tentativas (aviso da issue #21 ou WebApp fora do ar)")
            return 4
        if rc != 0:
            return rc
    print(f"inicializar {rel}: primeiro acesso ok (modulos {' '.join(map(str, modulos))})")
    return 0


def main(argv):
    if len(argv) < 2 or argv[1] not in ("2610", "2510"):
        print(__doc__, file=sys.stderr)
        return 2
    rel = argv[1]
    etapa = argv[2] if len(argv) > 2 else "assistente"
    host, amb = os.environ[f"PLAB_{rel}_HOST"], os.environ[f"PLAB_{rel}_ENV"]
    url = f"http://{host}:1234/webapp/"
    pasta = os.path.join(os.environ.get("PLAB_HOME", "/opt/plab"), "evidencias", rel,
                         time.strftime("%Y%m%d-%H%M%S") + "-inicializar-reserva")
    if etapa == "configurador":
        return configurador(rel, url, amb, pasta)
    if etapa == "primeiro-acesso":
        modulos = [int(m) for m in argv[3:]] or [5, 2, 4, 6]
        return primeiro_acesso(rel, url, amb, pasta, modulos)
    if etapa != "assistente":
        print(__doc__, file=sys.stderr)
        return 2
    limite = time.time() + int(os.environ.get("PLAB_INICIALIZAR_TEMPO", "1200"))
    with pw.navegador() as pagina:
        passos = pw.Passos(pagina, pasta)
        pw.parametros_iniciais(pagina, url, amb, "SIGAMDI")
        ultimo, recargas = None, 0
        while time.time() < limite:
            pagina.wait_for_timeout(5_000)
            if any("/login" in f.url for f in pagina.frames):
                passos.captura("login")
                print(f"inicializar {rel}: base pronta (tela de login)")
                return 0
            texto = pagina.evaluate(TEXTO)
            # Pagina de erro passageira (ex.: 502 do HAProxy logo depois de uma compilacao, visto na
            # 2610 em 06/11/2026): abre o WebApp de novo.
            if _pagina_de_erro(pagina) and recargas < 5:
                recargas += 1
                print(f"  pagina de erro ({texto[:60]!r}); abrindo o WebApp de novo ({recargas} de 5)", flush=True)
                pagina.wait_for_timeout(10_000)
                pw.parametros_iniciais(pagina, url, amb, "SIGAMDI")
                ultimo = None
                continue
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
