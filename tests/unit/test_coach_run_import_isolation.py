"""coach_run must import even when ML dependencies are absent.

This guard keeps the cs_readiness degrade path alive: if sentence-transformers
is missing, the whole coach-run turn still has to land, degrading to
peer-only via cs_readiness.state='missing'. A top-level import of
scripts.learning.rag.searcher / reranker would defeat that.
"""

import importlib
import sys
import unittest


class CoachRunImportIsolationTest(unittest.TestCase):
    def test_import_without_sentence_transformers(self) -> None:
        blocked = {
            "sentence_transformers",
            "torch",
            "numpy",
            "sklearn",
            "scripts.learning.rag.searcher",
            "scripts.learning.rag.reranker",
            "scripts.learning.integration",
        }

        saved = {name: sys.modules.pop(name, None) for name in blocked}
        # Drop any previously-imported coach_run so the import runs fresh.
        saved["scripts.workbench.core.coach_run"] = sys.modules.pop(
            "scripts.workbench.core.coach_run", None
        )

        class _BlockingFinder:
            def find_spec(self, name, path=None, target=None):  # noqa: D401
                if name in blocked or any(name.startswith(b + ".") for b in blocked):
                    raise ImportError(f"blocked for test: {name}")
                return None

        finder = _BlockingFinder()
        sys.meta_path.insert(0, finder)
        try:
            mod = importlib.import_module("scripts.workbench.core.coach_run")
            self.assertTrue(hasattr(mod, "run_coach"))
            self.assertTrue(hasattr(mod, "_check_cs_readiness"))
        finally:
            sys.meta_path.remove(finder)
            for name, prev in saved.items():
                if prev is not None:
                    sys.modules[name] = prev


if __name__ == "__main__":
    unittest.main()
