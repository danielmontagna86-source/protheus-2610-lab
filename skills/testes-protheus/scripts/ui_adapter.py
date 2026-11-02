"""Gates puros e leitura condicionada; não detecta DOM. author: daniel.montagna."""
import re


def choose_adapter(transport, renderer, *, verified, support_verified):
    if verified is not True or support_verified is not True:
        raise ValueError("Superfície ou compatibilidade ainda não comprovada")
    if transport != "browser":
        raise ValueError("Desktop não é Webapp; requer ferramenta de automação confirmada")
    if renderer == "legacy":
        return "TIR_WEBAPP"
    if renderer == "poui":
        return "ADAPTER_POUI_VERSIONADO"
    raise ValueError("Renderer misto/incerto requer mapear cada superfície e transição")


def format_username(username, domain=None):
    """Não autentica; domínio deve vir de regra confirmada do ambiente."""
    if not isinstance(username, str) or not username or username.strip() != username:
        raise ValueError("Usuário inválido")
    if domain in (None, ""):
        return username
    if not isinstance(domain, str) or not re.fullmatch(r"[A-Za-z0-9_.-]+", domain):
        raise ValueError("Domínio inválido")
    if "\\" in username:
        prefix, local_user = username.split("\\", 1)
        if prefix != domain or not local_user or "\\" in local_user:
            raise ValueError("Domínio existente diverge da configuração")
        return username
    return domain + "\\" + username


def resolve_login_username(username, *, environment, policy, configured_domain=None, form="as_provided"):
    """Aplica política confirmada do projeto; não autentica nem lê configuração.

    environment é chave explícita de policy.rules, não inferida do layout.
    QA pode permitir simples/prefixado; produção pode exigir domínio. Isso
    é exemplo de política empresarial configurável, não regra da TOTVS.
    """
    if not isinstance(policy, dict) or policy.get("confirmed") is not True:
        raise ValueError("Política de login precisa de confirmação explícita")
    rules = policy.get("rules")
    if not isinstance(environment, str) or not isinstance(rules, dict) or environment not in rules:
        raise ValueError("Ambiente não mapeado na política")
    rule = rules[environment]
    fields = ("allow_simple", "allow_domain", "require_confirmed_domain")
    if not isinstance(rule, dict) or any(type(rule.get(field)) is not bool for field in fields):
        raise ValueError("Regra incompleta ou inválida")
    if form not in {"as_provided", "simple", "domain"}:
        raise ValueError("Forma de usuário desconhecida")
    if configured_domain not in (None, "") and not isinstance(configured_domain, str):
        raise ValueError("Configuração de domínio inválida")
    format_username(username)
    prefixed = "\\" in username
    if prefixed:
        pieces = username.split("\\")
        if len(pieces) != 2 or not re.fullmatch(r"[A-Za-z0-9_.-]+", pieces[0]) or not pieces[1]:
            raise ValueError("Prefixo existente inválido ou duplicado")
    if rule["require_confirmed_domain"] and not configured_domain:
        raise ValueError("Domínio configurado e confirmado é obrigatório antes de autenticar")
    if configured_domain:
        format_username(username, configured_domain)
    if form == "simple":
        if prefixed or not rule["allow_simple"] or rule["require_confirmed_domain"]:
            raise ValueError("Forma simples não permitida neste contexto")
        return username
    use_domain = prefixed or form == "domain" or rule["require_confirmed_domain"] or not rule["allow_simple"]
    if use_domain:
        if not rule["allow_domain"]:
            raise ValueError("Forma com domínio não permitida pela política")
        if prefixed:
            return format_username(username, configured_domain or pieces[0])
        if not configured_domain:
            raise ValueError("Não adivinhar domínio para compor usuário")
        return format_username(username, configured_domain)
    if not rule["allow_simple"]:
        raise ValueError("Forma simples não permitida")
    return username


def read_verified_field(helper, field, expected, *, matches, context_verified, sensitive=False):
    """Adapter só chama Webapp.GetValue após gates fornecidos pelo responsável.

    matches é número de controles visíveis/alvo comprovado; não o resultado
    de uma busca inventada. Não lê senha/token/campo sensível nem ecoa dados.
    """
    if sensitive is not False:
        raise ValueError("Campo sensível não pode ser lido para evidência")
    if context_verified is not True or type(matches) is not int or matches != 1:
        raise ValueError("Contexto e controle único precisam ser comprovados")
    if not isinstance(field, str) or not field or not isinstance(expected, str):
        raise ValueError("Mapeamento de campo inválido")
    if field.strip().casefold() in {"senha", "password", "token", "api_key"}:
        raise ValueError("Identificador de segredo não pode ser lido")
    actual = helper.GetValue(field)
    if actual != expected:
        raise AssertionError("Conteúdo divergente; avaliar foco, máscara ou truncamento")
    return actual
