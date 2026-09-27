"""
Multi-Language Test Runner

Dispatches test execution to language-specific adapters.  Each adapter
performs real compilation/execution — no simulation, no auto-pass.

Supported languages and their requirements:
  python      — Python interpreter (sys.executable) + pytest
  javascript  — Node.js  (node)
  java        — Java compiler (javac) + runtime (java)
  cpp / c++   — GCC C++ compiler (g++)

If the required runtime/compiler is missing the adapter returns a
TestRunResult with every test marked as failed and a clear error message.
"""
import tempfile
from pathlib import Path

from app.core.logging import logger
from .adapters import CppAdapter, JavaAdapter, JavaScriptAdapter, PythonAdapter
from .models import TestAgentResult, TestRunResult


class MultiLanguageTestRunner:
    """
    Orchestrates test execution across languages.

    Selects the correct adapter for *language*, sandboxes the run inside a
    temporary directory, and returns a TestRunResult.  The orchestrator's
    interface is unchanged.
    """

    _ADAPTERS = {
        "python":     PythonAdapter,
        "javascript": JavaScriptAdapter,
        "typescript": JavaScriptAdapter,  # TS tests are transpiled-free JS-style assertions
        "java":       JavaAdapter,
        "cpp":        CppAdapter,
        "c++":        CppAdapter,
        "c":          CppAdapter,         # basic C can compile with g++ -x c
    }

    async def run(self, test_result: TestAgentResult, language: str) -> TestRunResult:
        """
        Execute *test_result.tests* for *language*.

        :param test_result: TestAgentResult from the Test Agent.
        :param language:    Programming language string (case-insensitive).
        :returns:           TestRunResult with real pass/fail/skip counts.
        """
        if not test_result.tests:
            return TestRunResult(
                total=0,
                passed=0,
                failed=0,
                skipped=0,
                execution_output="No tests to run.",
            )

        lang = language.lower()
        adapter_cls = self._ADAPTERS.get(lang)

        if adapter_cls is None:
            n = len(test_result.tests)
            msg = (
                f"UNSUPPORTED_LANGUAGE: No execution adapter for '{language}'. "
                f"Supported: {', '.join(sorted(set(self._ADAPTERS)))}."
            )
            logger.warning(f"[TestRunner] {msg}")
            return TestRunResult(
                total=n,
                passed=0,
                failed=n,
                skipped=0,
                execution_output=msg,
            )

        adapter = adapter_cls()

        with tempfile.TemporaryDirectory(prefix="codetrust_run_") as tmpdir:
            logger.info(
                f"[TestRunner] Running {len(test_result.tests)} test(s) "
                f"for language={language} in {tmpdir}"
            )
            result = await adapter.run(test_result.tests, Path(tmpdir))

        logger.info(
            f"[TestRunner] Finished: {result.passed} passed, "
            f"{result.failed} failed, {result.skipped} skipped"
        )
        return result
