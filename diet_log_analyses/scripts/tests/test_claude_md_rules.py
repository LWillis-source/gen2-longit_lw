"""Every file-locating and join rule in diet_log_analyses/CLAUDE.md, tested against the data.

Run from the repository root (about a minute; reads every input):
    /opt/anaconda3/bin/python -m pytest diet_log_analyses/scripts/tests -q
Rerun after any input changes (CLAUDE.md workflow step 0) and after editing CLAUDE.md.
Each check lives in rules_unchanged.py or rules_edited.py; this file turns each into one test.
"""
import contextlib
import importlib
import io
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

# checks of the earlier wording, replaced by rules_edited.py (E2, E6, E6b, E11, E12, E4, E5)
SUPERSEDED = {"5", "8", "9", "16", "34", "36", "37"}


def _results(module):
    with contextlib.redirect_stdout(io.StringIO()):  # the modules print a full report when run directly
        return importlib.import_module(module).RESULTS


CASES = [(m, r) for m in ("rules_unchanged", "rules_edited") for r in _results(m) if str(r[0]) not in SUPERSEDED]


@pytest.mark.parametrize("module,result", CASES, ids=[f"{m}:{r[0]}" for m, r in CASES])
def test_rule(module, result):
    n, status, claim, expected, found = result
    assert status in ("PASS", "NOTE"), f"{claim}\n expected: {expected}\n found: {found}"
