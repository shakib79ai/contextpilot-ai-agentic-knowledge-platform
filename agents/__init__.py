"""Multi-agent orchestration package.

Ensures both the repository root (for sibling `rag_pipeline`/`evals`/
`context_learning` packages) and `backend/` (for the `app` package) are on
sys.path, regardless of which top-level package or entrypoint is imported
first.
"""
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_BACKEND_DIR = _REPO_ROOT / "backend"
for _p in (_REPO_ROOT, _BACKEND_DIR):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))
