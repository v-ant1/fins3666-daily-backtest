"""Run builder invariance checks without loading outcomes or returns."""
from pathlib import Path
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
suite = unittest.defaultTestLoader.loadTestsFromModule(
    __import__('r4_harness.builders.test_builders', fromlist=['test_builders'])
)
status, details = StringIO(), StringIO()
with redirect_stdout(details), redirect_stderr(details):
    result = unittest.TextTestRunner(stream=status, verbosity=2).run(suite)
output = status.getvalue() + details.getvalue()
(Path(__file__).parent / 'TEST_OUTPUT.txt').write_text(output, encoding='utf-8')
print(output, end='')
raise SystemExit(0 if result.wasSuccessful() else 1)
