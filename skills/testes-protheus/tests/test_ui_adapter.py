"""UI sintética, nenhum browser/login. author: daniel.montagna."""
import sys
from pathlib import Path
import unittest
from unittest.mock import Mock
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from ui_adapter import choose_adapter, format_username, read_verified_field


class SurfaceTests(unittest.TestCase):
    def test_legacy_browser(self):
        self.assertEqual(choose_adapter("browser", "legacy", verified=True, support_verified=True), "TIR_WEBAPP")

    def test_poui_requires_own_support(self):
        with self.assertRaises(ValueError):
            choose_adapter("browser", "poui", verified=True, support_verified=False)
        self.assertEqual(choose_adapter("browser", "poui", verified=True, support_verified=True), "ADAPTER_POUI_VERSIONADO")

    def test_screenshot_is_not_runtime_verification(self):
        with self.assertRaises(ValueError):
            choose_adapter("browser", "legacy", verified=False, support_verified=True)

    def test_desktop_not_webapp(self):
        with self.assertRaises(ValueError):
            choose_adapter("desktop", "legacy", verified=True, support_verified=True)

    def test_mixed_or_unknown_requires_mapping(self):
        for renderer in ("mixed", "unknown"):
            with self.subTest(renderer=renderer), self.assertRaises(ValueError):
                choose_adapter("browser", renderer, verified=True, support_verified=True)


class IdentityTests(unittest.TestCase):
    def test_no_domain(self):
        self.assertEqual(format_username("qa.user"), "qa.user")

    def test_configured_domain(self):
        self.assertEqual(format_username("qa.user", "EXEMPLO"), "EXEMPLO\\qa.user")

    def test_no_double_prefix(self):
        self.assertEqual(format_username("EXEMPLO\\qa.user", "EXEMPLO"), "EXEMPLO\\qa.user")

    def test_conflicting_domain_blocks(self):
        with self.assertRaises(ValueError):
            format_username("OUTRO\\qa.user", "EXEMPLO")


class GetTests(unittest.TestCase):
    def test_unique_context(self):
        helper = Mock()
        helper.GetValue.return_value = "000001"
        self.assertEqual(read_verified_field(helper, "Codigo", "000001", matches=1, context_verified=True), "000001")
        helper.GetValue.assert_called_once_with("Codigo")

    def test_ambiguous_zero_or_unknown_no_read(self):
        for matches in (0, 2, None, True):
            helper = Mock()
            with self.subTest(matches=matches), self.assertRaises(ValueError):
                read_verified_field(helper, "Codigo", "000001", matches=matches, context_verified=True)
            helper.GetValue.assert_not_called()

    def test_sensitive_never_read(self):
        helper = Mock()
        with self.assertRaises(ValueError):
            read_verified_field(helper, "Campo", "synthetic", matches=1, context_verified=True, sensitive=True)
        helper.GetValue.assert_not_called()

    def test_obvious_secret_label_blocked_even_without_flag(self):
        for field in ("Senha", "Password", "TOKEN", "api_key"):
            helper = Mock()
            with self.subTest(field=field), self.assertRaises(ValueError):
                read_verified_field(helper, field, "synthetic", matches=1, context_verified=True)
            helper.GetValue.assert_not_called()

    def test_truncated_value_fails_without_echoing_it(self):
        helper = Mock()
        helper.GetValue.return_value = "0000"
        with self.assertRaisesRegex(AssertionError, "divergente"):
            read_verified_field(helper, "Codigo", "000001", matches=1, context_verified=True)

    def test_wrong_context_no_read(self):
        helper = Mock()
        with self.assertRaises(ValueError):
            read_verified_field(helper, "Codigo", "000001", matches=1, context_verified=False)
        helper.GetValue.assert_not_called()
