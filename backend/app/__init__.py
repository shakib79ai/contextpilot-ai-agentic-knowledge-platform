"""ContextPilot AI backend package.

Ensures the repository root (which contains the top-level `agents/`,
`rag_pipeline/`, `evals/`, and `context_learning/` packages) is importable
regardless of the working directory the app is launched from.
"""
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
