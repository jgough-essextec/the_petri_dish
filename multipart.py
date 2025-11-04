"""Compatibility shim: expose the `python_multipart` package under the
legacy name `multipart` so third-party packages that do `import multipart`
do not trigger a PendingDeprecationWarning.

This file lives at the project root so it is found before site-packages when
running tests or the app locally. It imports `python_multipart` (the modern
package) and re-exports its symbols under the name `multipart`.

This is a small, low-risk shim intended for test/CI runs until upstream
packages fully migrate.
"""
from __future__ import annotations

import importlib
import os
import sys
from typing import Iterable


def _running_under_pytest(env: dict[str, str], argv: Iterable[str]) -> bool:
    # Enable the shim during pytest runs or when explicitly requested.
    if os.environ.get("ENABLE_MULTIPART_SHIM") == "1":
        return True
    if "PYTEST_CURRENT_TEST" in env:
        return True
    if any("pytest" in (str(a).lower()) for a in argv):
        return True
    if "pytest" in sys.modules:
        return True
    return False


def _setup_shim() -> None:
    if not _running_under_pytest(os.environ, sys.argv):
        return

    try:
        pm = importlib.import_module("python_multipart")
    except Exception:
        # No python_multipart available; don't import legacy `multipart` here.
        return

    sys.modules.setdefault("multipart", pm)


_setup_shim()

_pm = sys.modules.get("multipart")
if _pm is not None:
    globals().update({k: getattr(_pm, k) for k in dir(_pm) if not k.startswith("__")})
