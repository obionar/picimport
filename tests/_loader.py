"""Shared test helper — load picimport as a module without installing it."""

import importlib.util
import sys
from importlib.machinery import SourceFileLoader
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "picimport"

if "picimport_mod" not in sys.modules:
    _loader = SourceFileLoader("picimport_mod", str(SCRIPT))
    _spec = importlib.util.spec_from_loader("picimport_mod", _loader)
    picimport = importlib.util.module_from_spec(_spec)
    sys.modules["picimport_mod"] = picimport
    _loader.exec_module(picimport)