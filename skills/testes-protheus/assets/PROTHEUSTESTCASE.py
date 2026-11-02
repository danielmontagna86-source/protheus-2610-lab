"""Smoke TIR de leitura adaptável; não executado no ERP. author: daniel.montagna.

Config de caso não é config TIR. Credencial privada existe fora do pacote,
é fornecida pelo responsável e não é criada/lida em prints por este template.
"""
import json
import os
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from ui_adapter import resolve_login_username


class PROTHEUS(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.helper = None
        if os.environ.get("PROTHEUS_TEST_EXECUTION_AUTHORIZED") != "YES":
            raise unittest.SkipTest("Template não autorizado/adaptado: nenhuma sessão aberta")
        case_path = os.environ.get("PROTHEUS_CASE_CONFIG")
        private_path = os.environ.get("PROTHEUS_TIR_PRIVATE_CONFIG")
        if not case_path or not private_path:
            raise unittest.SkipTest("Faltam configuração local do caso e config privada TIR")
        cls.case = json.loads(Path(case_path).read_text(encoding="utf-8"))
        if cls.case.get("ReadOnlyRoutineVerified") is not True:
            raise ValueError("A rotina de leitura precisa ser comprovada no projeto")
        for field in ("InitialProgram", "Date", "Group", "Branch", "Routine", "CheckField", "ExpectedValue"):
            if not isinstance(cls.case.get(field), str) or not cls.case[field]:
                raise ValueError(f"Mapear campo do caso: {field}")
        # Gate ANTES de importar/instanciar TIR ou autenticar; não imprime User.
        login_user = resolve_login_username(cls.case.get("Username"),
                                            environment=cls.case.get("LoginEnvironment"),
                                            policy=cls.case.get("LoginPolicy"),
                                            configured_domain=cls.case.get("ConfiguredDomain"),
                                            form=cls.case.get("LoginForm", "as_provided"))
        private_config = json.loads(Path(private_path).read_text(encoding="utf-8"))
        if private_config.get("User") != login_user:
            raise ValueError("User da configuração privada diverge da política confirmada")
        del private_config
        from tir import Webapp
        cls.helper = Webapp(config_path=private_path)
        # addClassCleanup executa mesmo se Setup falhar; não presumir tearDownClass nesse caso.
        cls.addClassCleanup(cls.helper.TearDown)
        cls.helper.Setup(initial_program=cls.case["InitialProgram"], date=cls.case["Date"],
                         group=cls.case["Group"], branch=cls.case["Branch"])
        cls.helper.Program(cls.case["Routine"])

    def test_CT001_read_field(self):
        """Verifica campo específico, sem certificar etapa financeira."""
        self.helper.Screenshot(filename="CT001_contexto_real")
        self.helper.CheckResult(self.case["CheckField"], self.case["ExpectedValue"])
        self.helper.AssertTrue()
