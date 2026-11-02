"""Política empresarial sintética e gate anterior ao TIR. author: daniel.montagna."""
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from ui_adapter import resolve_login_username


def policy():
    return {"confirmed": True, "rules": {
        "qa": {"allow_simple": True, "allow_domain": True, "require_confirmed_domain": False},
        "production": {"allow_simple": False, "allow_domain": True, "require_confirmed_domain": True}}}


class LoginPolicyTests(unittest.TestCase):
    def resolve(self, user="qa.user", environment="qa", domain=None, form="as_provided", supplied_policy=None):
        return resolve_login_username(user, environment=environment,
                                      policy=policy() if supplied_policy is None else supplied_policy,
                                      configured_domain=domain, form=form)

    def test_qa_simple(self):
        self.assertEqual(self.resolve(), "qa.user")

    def test_qa_default_domain_does_not_force_prefix(self):
        self.assertEqual(self.resolve(domain="EXEMPLO"), "qa.user")

    def test_qa_choose_domain(self):
        self.assertEqual(self.resolve(domain="EXEMPLO", form="domain"), "EXEMPLO\\qa.user")

    def test_qa_prefixed_not_duplicated(self):
        self.assertEqual(self.resolve("EXEMPLO\\qa.user", domain="EXEMPLO"), "EXEMPLO\\qa.user")

    def test_qa_explicit_prefix_without_default(self):
        self.assertEqual(self.resolve("EXEMPLO\\qa.user"), "EXEMPLO\\qa.user")

    def test_production_composes_confirmed_domain(self):
        self.assertEqual(self.resolve(environment="production", domain="EXEMPLO"), "EXEMPLO\\qa.user")

    def test_production_prefixed_correct(self):
        self.assertEqual(self.resolve("EXEMPLO\\qa.user", "production", "EXEMPLO"), "EXEMPLO\\qa.user")

    def test_production_absent_domain_blocks(self):
        for user in ("qa.user", "EXEMPLO\\qa.user"):
            with self.subTest(user=user), self.assertRaises(ValueError):
                self.resolve(user, "production")

    def test_conflict_blocks_both(self):
        for environment in ("qa", "production"):
            with self.subTest(environment=environment), self.assertRaises(ValueError):
                self.resolve("OUTRO\\qa.user", environment, "EXEMPLO")

    def test_duplicated_prefix_blocks(self):
        with self.assertRaises(ValueError):
            self.resolve("EXEMPLO\\EXEMPLO\\qa.user", domain="EXEMPLO")

    def test_unknown_environment_blocks(self):
        with self.assertRaises(ValueError):
            self.resolve(environment="unknown")

    def test_unconfirmed_policy_blocks(self):
        rules = policy()
        rules["confirmed"] = False
        with self.assertRaises(ValueError):
            self.resolve(supplied_policy=rules)

    def test_production_simple_choice_cannot_bypass_policy(self):
        with self.assertRaises(ValueError):
            self.resolve(environment="production", domain="EXEMPLO", form="simple")

    def test_unknown_form_blocks(self):
        with self.assertRaises(ValueError):
            self.resolve(form="guess")

    def test_missing_policy_rule_blocks(self):
        rules = policy()
        del rules["rules"]["production"]["require_confirmed_domain"]
        with self.assertRaises(ValueError):
            self.resolve(environment="production", domain="EXEMPLO", supplied_policy=rules)


class PreSetupTests(unittest.TestCase):
    def test_production_invalid_never_constructs_webapp(self):
        root = Path(__file__).resolve().parents[1]
        spec = importlib.util.spec_from_file_location("login_template_case", root / "assets" / "PROTHEUSTESTCASE.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as temp:
            case = {"ReadOnlyRoutineVerified": True, "InitialProgram": "SYNTHETIC", "Date": "08/10/2026",
                    "Group": "TEST", "Branch": "TEST", "Routine": "READ_ONLY", "CheckField": "Codigo", "ExpectedValue": "001",
                    "LoginEnvironment": "production", "Username": "qa.user", "ConfiguredDomain": None,
                    "LoginPolicy": policy()}
            case_path = Path(temp) / "case.json"
            case_path.write_text(json.dumps(case), encoding="utf-8")
            private_path = Path(temp) / "private.json"
            private_path.write_text(json.dumps({"User": "qa.user"}), encoding="utf-8")
            webapp = Mock(side_effect=AssertionError("Não pode abrir sessão"))
            with patch.dict(os.environ, {"PROTHEUS_TEST_EXECUTION_AUTHORIZED": "YES",
                                         "PROTHEUS_CASE_CONFIG": str(case_path),
                                         "PROTHEUS_TIR_PRIVATE_CONFIG": str(private_path)}), \
                 patch.dict(sys.modules, {"tir": SimpleNamespace(Webapp=webapp)}):
                with self.assertRaises(ValueError):
                    module.PROTHEUS.setUpClass()
                webapp.assert_not_called()
