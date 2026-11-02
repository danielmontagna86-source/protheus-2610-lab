"""Runner: falha=1, não executado/skipped=2. author: daniel.montagna."""
import unittest
from PROTHEUSTESTCASE import PROTHEUS


def main():
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(PROTHEUS)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        return 1
    if result.skipped or result.testsRun == 0:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
