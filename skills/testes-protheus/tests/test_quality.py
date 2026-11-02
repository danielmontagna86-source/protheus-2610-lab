"""Casos sintéticos; author: daniel.montagna."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from quality import reconcile, resume_decision, stage_status


class CoverageTests(unittest.TestCase):
    def row(self, key="A", value="10.00"):
        return {"key": key, "amount": value}

    def test_exact(self):
        self.assertTrue(reconcile([self.row()], [self.row()])["ok"])

    def test_partial(self):
        self.assertFalse(reconcile([self.row(), self.row("B")], [self.row()])["ok"])

    def test_total_equal_different_keys(self):
        self.assertFalse(reconcile([self.row()], [self.row("B")])["ok"])

    def test_duplicate(self):
        self.assertFalse(reconcile([self.row()], [self.row(), self.row()])["ok"])

    def test_expected_duplicate_is_ambiguous(self):
        with self.assertRaises(ValueError):
            reconcile([self.row(), self.row()], [self.row()])

    def test_financial_difference(self):
        self.assertFalse(reconcile([self.row()], [self.row(value="10.01")])["ok"])

    def test_decimal_exact(self):
        expected = [self.row("A", "0.10"), self.row("B", "0.20")]
        self.assertEqual(reconcile(expected, expected)["expected_total"], "0.30")

    def test_empty_is_not_approved_by_default(self):
        self.assertFalse(reconcile([], [])["ok"])

    def test_known_empty_idempotency_is_explicit(self):
        self.assertTrue(reconcile([], [], allow_empty=True)["ok"])

    def test_invalid_amounts(self):
        for value in [float("nan"), "NaN", "Infinity", "1,01", 1.01, None]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                reconcile([self.row(value=value)], [self.row()])

    def test_signed_amounts(self):
        self.assertTrue(reconcile([self.row(value="-10.00")], [self.row(value="-10.00")])["ok"])


class ResumeTests(unittest.TestCase):
    def test_alive_or_unknown_blocks(self):
        for state in ["alive", "unknown"]:
            self.assertFalse(resume_decision(state, ["A"], ["A"], ["A", "B"], False)["may_resume"])

    def test_missing_log_but_commit_blocks(self):
        self.assertFalse(resume_decision("dead", ["A"], ["A", "B"], ["A", "B"], False)["may_resume"])

    def test_checkpoint_without_effect_blocks(self):
        self.assertFalse(resume_decision("dead", ["A"], [], ["A", "B"], False)["may_resume"])

    def test_systemic_failure_survives_resume(self):
        self.assertFalse(resume_decision("dead", ["A"], ["A"], ["A", "B"], True)["may_resume"])

    def test_verified_pending(self):
        result = resume_decision("dead", ["A"], ["A"], ["A", "B"], False)
        self.assertTrue(result["may_resume"])
        self.assertEqual(result["pending"], ["B"])

    def test_invalid_process_state(self):
        with self.assertRaises(ValueError):
            resume_decision("maybe", [], [], [], False)

    def test_unknown_systemic_failure_is_not_false(self):
        with self.assertRaises(ValueError):
            resume_decision("dead", [], [], [], None)

    def test_duplicate_checkpoint(self):
        with self.assertRaises(ValueError):
            resume_decision("dead", ["A", "A"], ["A"], ["A"], False)

    def test_external_operation_same_contract_does_not_get_adopted(self):
        result = resume_decision("dead", ["RUN_A_SEQ"], ["RUN_A_SEQ", "EXTERNAL_SEQ"], ["RUN_A_SEQ", "RUN_B_SEQ"], False)
        self.assertFalse(result["may_resume"])
        self.assertIn("EFEITO_FORA_DO_PLANO", result["reasons"])


class StageTests(unittest.TestCase):
    def test_all_requirements(self):
        self.assertEqual(stage_status(True, True, True, []), "APROVADO")

    def test_job_success_without_business_evidence(self):
        self.assertEqual(stage_status(True, True, False, []), "BLOQUEADO")

    def test_job_error_even_if_payload_matches(self):
        self.assertEqual(stage_status(True, False, True, []), "REPROVADO")

    def test_upload_is_not_payment_evidence(self):
        self.assertEqual(stage_status(True, True, False, ["HTTP 200 apenas"]), "REPROVADO")

    def test_not_executed(self):
        self.assertEqual(stage_status(False, None, False, []), "NAO_EXECUTADO")

    def test_unknown_job_blocks(self):
        self.assertEqual(stage_status(True, None, True, []), "BLOQUEADO")


if __name__ == "__main__":
    unittest.main()
