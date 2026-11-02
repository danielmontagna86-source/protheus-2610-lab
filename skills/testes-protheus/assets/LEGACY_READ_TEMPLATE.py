"""Fragmento adaptável de leitura GET não sensível. author: daniel.montagna.

Não abre sessão ou autentica. helper deve pertencer à sessão TIR autorizada.
Confirmar source/matches/context antes de fornecer flags. Nenhum DOM inventado.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from ui_adapter import choose_adapter, read_verified_field


def validate_legacy_get(helper, field, expected, *, runtime_verified, support_verified,
                        visible_matches, context_verified):
    choose_adapter("browser", "legacy", verified=runtime_verified,
                   support_verified=support_verified)
    return read_verified_field(helper, field, expected, matches=visible_matches,
                               context_verified=context_verified, sensitive=False)
