"""Verificadores puros, sem acesso ao ERP. author: daniel.montagna.

Não provam que as entradas refletem o banco: o adaptador é responsável por
chaves, snapshot, escopo e significado financeiro dos dados fornecidos.
"""
from collections import Counter
from decimal import Decimal, InvalidOperation


def _amount(value):
    if not isinstance(value, (str, int, Decimal)) or isinstance(value, bool):
        raise ValueError("amount exige string decimal, inteiro ou Decimal; float não aceito")
    try:
        result = Decimal(value)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError("amount inválido") from exc
    if not result.is_finite():
        raise ValueError("amount não finito")
    return result


def _keys(values, name):
    if not all(isinstance(value, str) and value.strip() for value in values):
        raise ValueError(f"{name}: chaves precisam ser strings não vazias")
    if len(set(values)) != len(values):
        raise ValueError(f"{name}: chave duplicada; use a chave de negócio completa")
    return set(values)


def reconcile(expected, actual, *, allow_empty=False):
    """Compara chave única de negócio e valor exato, sem tolerância implícita.

    expected deve conter todas as linhas esperadas no escopo. actual deve
    incluir todos os efeitos alcançados, inclusive extras. A chave pode ser
    serialização canônica de uma tupla; não use concatenação ambígua.
    """
    expected = list(expected)
    actual = list(actual)
    _keys([row["key"] for row in expected], "expected")
    if not all(isinstance(row["key"], str) and row["key"].strip() for row in actual):
        raise ValueError("actual: chave inválida")
    e = {row["key"]: _amount(row["amount"]) for row in expected}
    a = [(row["key"], _amount(row["amount"])) for row in actual]
    counts = Counter(key for key, _ in a)
    missing = sorted(set(e) - set(counts))
    extra = sorted(set(counts) - set(e))
    duplicates = sorted(key for key, count in counts.items() if count > 1)
    differences = [{"key": key, "expected": str(e[key]), "actual": str(amount)}
                   for key, amount in a if key in e and amount != e[key]]
    return {"ok": bool(expected or allow_empty) and not any((missing, extra, duplicates, differences)),
            "expected_count": len(expected), "actual_count": len(actual),
            "expected_total": str(sum(e.values(), Decimal("0"))),
            "actual_total": str(sum((value for _, value in a), Decimal("0"))),
            "missing": missing, "extra": extra, "duplicates": duplicates,
            "differences": differences}


def resume_decision(process_tree_state, committed, observed, planned, systemic_failure):
    """Decisão apenas: nunca executa, desbloqueia lock ou reenvia operação.

    process_tree_state cobre runner E filhos, com PID+hora de criação.
    observed precisa de delimitação integral dos efeitos novos da campanha,
    com atribuição comprovada (contrato sozinho não identifica a execução).
    Falha dessa atribuição deve ser expressa como estado unknown pelo chamador.
    """
    if process_tree_state not in {"alive", "dead", "unknown"}:
        raise ValueError("process_tree_state inválido")
    if not isinstance(systemic_failure, bool):
        raise ValueError("systemic_failure exige estado conhecido booleano")
    c = _keys(list(committed), "committed")
    o = _keys(list(observed), "observed")
    p = _keys(list(planned), "planned")
    reasons = []
    if process_tree_state != "dead":
        reasons.append("PROCESSO_ATIVO_OU_INCERTO")
    if systemic_failure:
        reasons.append("FALHA_SISTEMICA_PERSISTIDA")
    if c != o:
        reasons.append("JOURNAL_DIVERGE_DOS_EFEITOS")
    if not o <= p:
        reasons.append("EFEITO_FORA_DO_PLANO")
    return {"may_resume": not reasons, "reasons": reasons,
            "pending": sorted(p - o) if not reasons else []}


def stage_status(executed, job_ok, business_evidence_complete, errors):
    """Critério mínimo; booleanos devem vir de verificações documentadas.

    Para pagamento, business_evidence_complete NÃO pode significar HTTP 200,
    saldo zero ou data de baixa isolados. Retorno sem job usa job_ok=True só
    após declarar explicitamente que monitor de job não se aplica.
    """
    if not executed:
        return "NAO_EXECUTADO"
    if errors or job_ok is False:
        return "REPROVADO"
    if job_ok is not True or business_evidence_complete is not True:
        return "BLOQUEADO"
    return "APROVADO"
