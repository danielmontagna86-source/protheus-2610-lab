"""Extensao local do Protheus 2610 Lab para o TIR (fragil, documentada; NAO e API garantida do TIR).

Problema (verificado em 2026-11-02, TIR 2.14.12, WebApp 26.0.0 e SmartClient HTML 10.0.2):
o campo "Ambiente no servidor" (#selectEnv, wa-combobox com shadow DOM) autocompleta durante a
digitacao. O TIR preenche o campo tecla a tecla (try_send_keys) e o valor vira, por exemplo,
'P261P2610'; como fill_select_element so sai quando o valor lido == ambiente, o Setup fica preso
ate o TimeOut e reinicia o navegador.

Correcao: antes de digitar, se o <select> interno do #selectEnv tiver a opcao exata do ambiente,
seleciona-a diretamente e confere a pos-condicao (input interno == ambiente). Se a opcao nao existir
ou a pos-condicao falhar, devolve o controle ao metodo original do TIR. Nenhum resultado de teste e
produzido por JavaScript; so a selecao do ambiente na tela de parametros iniciais.

Uso: importar este modulo antes de instanciar Webapp. Remover quando o TIR corrigir o preenchimento.
author: daniel.montagna
"""
from tir.technologies.core.logging_config import logger
from tir.technologies.webapp_internal import WebappInternal

_ORIGINAL = WebappInternal.filling_server_environment

_JS_SELECIONA_AMBIENTE = """
const amb = arguments[0];
const combo = document.querySelector('#selectEnv');
if (!combo || !combo.shadowRoot) { return 'sem-combo'; }
const sel = combo.shadowRoot.querySelector('select');
const inp = combo.shadowRoot.querySelector('input');
if (!sel || ![...sel.options].some(o => o.value === amb)) { return 'sem-opcao'; }
sel.value = amb;
sel.dispatchEvent(new Event('change', {bubbles: true}));
if (inp) { inp.value = amb; inp.dispatchEvent(new Event('input', {bubbles: true})); }
return (inp ? inp.value : sel.value) === amb ? 'ok' : 'divergente';
"""


def _filling_server_environment(self, environment):
    if self.webapp_shadowroot():
        resultado = self.driver.execute_script(_JS_SELECIONA_AMBIENTE, environment.strip())
        if resultado == "ok":
            logger().info(f'[plab_tir_compat] Ambiente "{environment}" selecionado no #selectEnv (sem digitar)')
            return None
        logger().info(f"[plab_tir_compat] selecao direta nao aplicada ({resultado}); usando o TIR original")
    return _ORIGINAL(self, environment)


WebappInternal.filling_server_environment = _filling_server_environment
