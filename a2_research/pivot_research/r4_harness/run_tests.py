"""One-command Phase 3 harness validation."""
from pathlib import Path
from contextlib import redirect_stdout, redirect_stderr
from io import StringIO
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
suite=unittest.defaultTestLoader.discover(str(Path(__file__).parent/'tests'),top_level_dir=str(ROOT))
status=StringIO(); details=StringIO()
with redirect_stdout(details), redirect_stderr(details):
    result=unittest.TextTestRunner(stream=status,verbosity=2).run(suite)
output=status.getvalue()+details.getvalue()
(Path(__file__).parent/'TEST_OUTPUT.txt').write_text(output,encoding='utf-8')
print(output,end='')
raise SystemExit(0 if result.wasSuccessful() else 1)
