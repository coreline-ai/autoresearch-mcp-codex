"""AutoResearch Orchestrator"""
__version__ = "0.1.0"

# Force UTF-8 stdout/stderr on Windows to prevent cp949 encoding crashes.
# This runs once at import time before any print() call in the package.
import sys as _sys
import io as _io

if _sys.stdout and hasattr(_sys.stdout, "buffer"):
    try:
        if _sys.stdout.encoding and _sys.stdout.encoding.lower().replace("-", "") != "utf8":
            _sys.stdout = _io.TextIOWrapper(
                _sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True,
            )
    except Exception:
        pass

if _sys.stderr and hasattr(_sys.stderr, "buffer"):
    try:
        if _sys.stderr.encoding and _sys.stderr.encoding.lower().replace("-", "") != "utf8":
            _sys.stderr = _io.TextIOWrapper(
                _sys.stderr.buffer, encoding="utf-8", errors="replace", line_buffering=True,
            )
    except Exception:
        pass
