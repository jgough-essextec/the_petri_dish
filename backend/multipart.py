"""Backend-local compatibility shim for multipart.

This shim is intentionally conditional: it will only register the modern
`python_multipart` module under the legacy name `multipart` when running
under pytest (or when the environment variable `ENABLE_MULTIPART_SHIM=1` is
set). That keeps normal/production imports untouched while preventing the
PendingDeprecationWarning during test runs.
"""
from __future__ import annotations

import importlib
import os
import sys
from typing import Iterable


def _running_under_pytest(env: dict[str, str], argv: Iterable[str]) -> bool:
    # Heuristics: pytest sets PYTEST_CURRENT_TEST per-test; additionally,
    # pytest can appear on sys.argv or in loaded modules. Allow an explicit
    # override via ENABLE_MULTIPART_SHIM=1.
    if os.environ.get("ENABLE_MULTIPART_SHIM") == "1":
        return True
    if "PYTEST_CURRENT_TEST" in env:
        return True
    if any("pytest" in (str(a).lower()) for a in argv):
        return True
    if "pytest" in sys.modules:
        return True
    return False


def _setup_backend_shim() -> None:
    if not _running_under_pytest(os.environ, sys.argv):
        return

    try:
        pm = importlib.import_module("python_multipart")
    except Exception:
        # If python_multipart isn't available, don't attempt to import the
        # legacy `multipart` package here; let normal import machinery handle
        # the fallback (which may raise or emit warnings).
        return

    # Ensure future `import multipart` returns the python_multipart module
    sys.modules.setdefault("multipart", pm)


_setup_backend_shim()

_pm = sys.modules.get("multipart")
if _pm is not None:
    globals().update({k: getattr(_pm, k) for k in dir(_pm) if not k.startswith("__")})
