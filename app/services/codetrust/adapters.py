"""
Language execution adapters for the CodeTrust Test Runner.

Each adapter handles a single language:
  - Probes for required runtime/compiler binaries
  - Writes test source to a temporary sandbox directory
  - Compiles (if required)
  - Executes
  - Parses stdout/stderr into a TestRunResult

Contract:
  - Never simulate a successful test
  - If a runtime is unavailable → return error TestRunResult with failed=total
  - If compilation fails → return error TestRunResult with failed=total
  - If a single test function raises → count it as 1 failed, continue the rest
  - No shell=True anywhere
"""
from __future__ import annotations

import asyncio
import hashlib
import re
import shutil
import sys
import textwrap
import uuid
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List

from app.core.config import settings
from app.core.logging import logger
from .models import GeneratedTest, TestRunResult


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

async def _run_subprocess(
    cmd: List[str],
    cwd: str,
    timeout: float,
) -> tuple[int, str]:
    """
    Run *cmd* in *cwd* with *timeout* seconds.
    Returns (returncode, combined_stdout_stderr).
    Never uses shell=True.
    """
    try:
        proc = await asyncio.wait_for(
            asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                cwd=cwd,
            ),
            timeout=timeout,
        )
        stdout, _ = await asyncio.wait_for(
            proc.communicate(),
            timeout=timeout,
        )
        return proc.returncode, stdout.decode("utf-8", errors="replace")
    except asyncio.TimeoutError:
        return -1, "TIMEOUT: execution exceeded the allowed time limit."
    except FileNotFoundError as e:
        return -1, f"RUNTIME_NOT_FOUND: {e}"
    except Exception as e:
        return -1, f"RUNNER_ERROR: {e}"


def _error_result(tests: List[GeneratedTest], message: str) -> TestRunResult:
    """Build a TestRunResult where every test counts as failed with *message*."""
    n = len(tests)
    return TestRunResult(
        total=n,
        passed=0,
        failed=n,
        skipped=0,
        execution_output=message[:4096],
        test_details=[
            {"test_id": t.test_id, "name": t.name, "status": "error", "message": message}
            for t in tests
        ],
    )


# ──────────────────────────────────────────────────────────────────────────────
# Base
# ──────────────────────────────────────────────────────────────────────────────

class BaseAdapter(ABC):
    """Abstract base for a language-specific execution adapter."""

    @abstractmethod
    async def run(self, tests: List[GeneratedTest], tmpdir: Path) -> TestRunResult:
        """Execute *tests* inside *tmpdir* and return the aggregate result."""


# ──────────────────────────────────────────────────────────────────────────────
# Python adapter
# ──────────────────────────────────────────────────────────────────────────────

def _safe_id(test_id: str) -> str:
    """
    Convert a test_id into a collision-safe Python filename stem.

    Two steps:
    1. Replace every non-alphanumeric character with ``_`` to produce a
       human-readable prefix (e.g. ``TC-A-B`` → ``TC_A_B``).
    2. Append ``_`` and the first 8 hex digits of the SHA-256 of the *original*
       test_id.  This suffix makes the stem globally unique: two IDs that differ
       only in punctuation (e.g. ``TC-A_B`` vs ``TC-A-B``) yield the same
       sanitised prefix but different hashes, so their filenames never collide.

    The stem is used only as a filesystem key; the original test_id is always
    preserved in ``test_details`` via the ``stem_to_test`` mapping built in
    ``PythonAdapter.run()``.
    """
    sanitised = re.sub(r"[^a-zA-Z0-9]", "_", test_id)
    digest = hashlib.sha256(test_id.encode()).hexdigest()[:8]
    return f"{sanitised}_{digest}"


class PythonAdapter(BaseAdapter):
    """
    Executes Python tests via pytest.

    Each GeneratedTest is written to its own file named after its test_id so
    that per-test pass/fail evidence can be traced back to the originating
    GeneratedTest.  Pytest is run with -v so each function emits an explicit
    PASSED / FAILED line; those lines are parsed back into test_details entries.

    Populates TestRunResult.test_details with one entry per GeneratedTest:
        {"test_id": str, "name": str, "status": "passed" | "failed" | "error"}

    Any test whose file produced no result line from pytest is treated as
    "error" — never fabricated as passed.
    """

    async def run(self, tests: List[GeneratedTest], tmpdir: Path) -> TestRunResult:
        if not tests:
            return TestRunResult(total=0, passed=0, failed=0, skipped=0,
                                 execution_output="No tests to run.")

        # Write one file per test, named by safe test_id so we can reverse-map.
        # stem_to_test maps  safe_id(test.test_id) → GeneratedTest
        stem_to_test: dict[str, GeneratedTest] = {}
        for test in tests:
            stem = _safe_id(test.test_id)
            code = self._normalise(test.test_code)
            (tmpdir / f"test_{stem}.py").write_text(code, encoding="utf-8")
            stem_to_test[stem] = test

        cmd = [
            sys.executable, "-m", "pytest",
            str(tmpdir),
            "--tb=short", "--no-header", "-v",
        ]
        rc, output = await _run_subprocess(cmd, str(tmpdir), settings.SANDBOX_EXECUTION_TIMEOUT)

        if "RUNTIME_NOT_FOUND" in output:
            return _error_result(tests, output)
        if "TIMEOUT" in output:
            return _error_result(tests, output)

        return self._parse(output, tests, stem_to_test)

    @staticmethod
    def _normalise(code: str) -> str:
        code = textwrap.dedent(code)
        if "def test_" not in code:
            inner = textwrap.indent(code.strip(), "    ")
            code = f"def test_generated():\n{inner}\n"
        return code

    @staticmethod
    def _parse(
        output: str,
        tests: List[GeneratedTest],
        stem_to_test: dict[str, GeneratedTest],
    ) -> TestRunResult:
        """
        Parse verbose pytest output into per-test details and aggregate counts.

        Verbose pytest emits lines like:
            test_TC_ABC123.py::test_foo PASSED
            test_TC_ABC123.py::test_bar FAILED
            test_TC_ABC123.py::test_baz ERROR

        The filename stem (``TC_ABC123`` from ``test_TC_ABC123.py``) maps back
        to the originating GeneratedTest via *stem_to_test*.

        Any GeneratedTest that produced no result line is recorded as "error"
        and counts as failed — never as passed.
        """
        # stem → final status (last line wins if a stem appears more than once)
        stem_status: dict[str, str] = {}

        # Matches: "test_<stem>.py[::anything] PASSED|FAILED|ERROR"
        # The node id part after "::" is optional (collection errors may omit it).
        line_re = re.compile(
            r"test_([A-Za-z0-9_]+)\.py(?:::[^\s]+)?\s+(PASSED|FAILED|ERROR)",
            re.IGNORECASE,
        )
        for m in line_re.finditer(output):
            stem, raw_status = m.group(1), m.group(2).lower()
            # Within a single file: failed/error always overrides an earlier passed.
            # This handles files that contain multiple def test_ functions.
            prev = stem_status.get(stem)
            if prev is None or prev == "passed":
                stem_status[stem] = raw_status

        # Build test_details — one entry per generated test.
        test_details: list[dict] = []
        passed = failed = 0

        for test in tests:
            stem = _safe_id(test.test_id)
            status = stem_status.get(stem)
            if status == "passed":
                detail_status = "passed"
                passed += 1
            elif status in ("failed", "error"):
                detail_status = status  # preserve "error" vs "failed" distinction
                failed += 1
            else:
                # No result line found — treat as error, never as passed.
                detail_status = "error"
                failed += 1

            test_details.append({
                "test_id": test.test_id,
                "name": test.name,
                "status": detail_status,
            })

        return TestRunResult(
            total=passed + failed,
            passed=passed,
            failed=failed,
            skipped=0,
            execution_output=output[:4096],
            test_details=test_details,
        )


# ──────────────────────────────────────────────────────────────────────────────
# JavaScript (Node.js) adapter
# ──────────────────────────────────────────────────────────────────────────────

_NODE_HARNESS = """\
// Minimal test harness — no external dependencies required.
// Runs each test_ function, catches errors, and prints TAP-like output.
const tests = [];
function test(name, fn) {{ tests.push({{ name, fn }}); }}

{test_body}

(async () => {{
  let passed = 0, failed = 0;
  for (const t of tests) {{
    try {{
      await t.fn();
      console.log(`ok - ${{t.name}}`);
      passed++;
    }} catch(e) {{
      console.log(`not ok - ${{t.name}}: ${{e.message || e}}`);
      failed++;
    }}
  }}
  console.log(`\\n# passed: ${{passed}}, failed: ${{failed}}`);
  process.exit(failed > 0 ? 1 : 0);
}})();
"""


class JavaScriptAdapter(BaseAdapter):
    """
    Executes JavaScript tests via Node.js using a minimal built-in harness.
    No Jest or other external framework required.
    """

    _NODE_BIN: str | None = shutil.which("node")

    async def run(self, tests: List[GeneratedTest], tmpdir: Path) -> TestRunResult:
        if not tests:
            return TestRunResult(total=0, passed=0, failed=0, skipped=0,
                                 execution_output="No tests to run.")

        if not self._NODE_BIN:
            return _error_result(
                tests,
                "RUNTIME_NOT_FOUND: 'node' executable not found. "
                "Install Node.js to run JavaScript tests.",
            )

        # Combine all tests into one file driven by the harness
        body_parts: List[str] = []
        for t in tests:
            # Wrap each test block in a test() call if not already
            code = self._normalise(t.test_code, t.name)
            body_parts.append(code)

        harness_code = _NODE_HARNESS.format(test_body="\n\n".join(body_parts))
        test_file = tmpdir / "tests.js"
        test_file.write_text(harness_code, encoding="utf-8")

        cmd = [self._NODE_BIN, str(test_file)]
        rc, output = await _run_subprocess(cmd, str(tmpdir), settings.SANDBOX_EXECUTION_TIMEOUT)

        return self._parse(output, rc, len(tests))

    @staticmethod
    def _normalise(code: str, test_name: str) -> str:
        """
        Wrap raw JS code in a test() call if it isn't already.
        Remove any Jest-style describe/expect usage for the plain harness.
        """
        code = textwrap.dedent(code)
        # Already wrapped in test()
        if re.search(r"^test\s*\(", code, re.MULTILINE):
            return code
        # Has function declarations — wrap each
        safe_name = re.sub(r"[^a-zA-Z0-9_ ]", "", test_name)[:60]
        return f'test("{safe_name}", () => {{\n{textwrap.indent(code, "  ")}\n}});\n'

    @staticmethod
    def _parse(output: str, returncode: int, total: int) -> TestRunResult:
        passed = failed = 0
        m = re.search(r"# passed:\s*(\d+),\s*failed:\s*(\d+)", output)
        if m:
            passed, failed = int(m.group(1)), int(m.group(2))
        elif "RUNTIME_NOT_FOUND" in output or "TIMEOUT" in output or "RUNNER_ERROR" in output:
            return TestRunResult(
                total=total, passed=0, failed=total, skipped=0,
                execution_output=output[:4096],
            )
        elif returncode != 0 and passed == 0 and failed == 0:
            failed = total

        return TestRunResult(
            total=passed + failed,
            passed=passed,
            failed=failed,
            skipped=0,
            execution_output=output[:4096],
        )


# ──────────────────────────────────────────────────────────────────────────────
# Java adapter
# ──────────────────────────────────────────────────────────────────────────────

_JAVA_RUNNER_TEMPLATE = """\
public class TestRunner {{
    private static int passed = 0;
    private static int failed = 0;

    public static void main(String[] args) throws Exception {{
        {test_calls}
        System.out.println();
        System.out.println("# passed: " + passed + ", failed: " + failed);
        System.exit(failed > 0 ? 1 : 0);
    }}

    private static void runTest(String name, Runnable fn) {{
        try {{
            fn.run();
            System.out.println("ok - " + name);
            passed++;
        }} catch (Throwable e) {{
            System.out.println("not ok - " + name + ": " + e.getMessage());
            failed++;
        }}
    }}

{test_methods}
}}
"""


class JavaAdapter(BaseAdapter):
    """
    Compiles and executes Java test code using javac + java.
    If javac is not available, returns an error result.
    """

    _JAVAC_BIN: str | None = shutil.which("javac")
    _JAVA_BIN: str | None = shutil.which("java")

    async def run(self, tests: List[GeneratedTest], tmpdir: Path) -> TestRunResult:
        if not tests:
            return TestRunResult(total=0, passed=0, failed=0, skipped=0,
                                 execution_output="No tests to run.")

        if not self._JAVAC_BIN:
            return _error_result(
                tests,
                "RUNTIME_NOT_FOUND: 'javac' compiler not found. "
                "Install a Java JDK (not just JRE) to compile and run Java tests.",
            )
        if not self._JAVA_BIN:
            return _error_result(
                tests,
                "RUNTIME_NOT_FOUND: 'java' runtime not found. Install a Java JDK.",
            )

        # Build a single TestRunner.java from all test snippets
        test_methods: List[str] = []
        test_calls: List[str] = []
        for i, t in enumerate(tests):
            method_name = f"test_{i}"
            method_body = self._extract_body(t.test_code)
            test_methods.append(
                f"    private static void {method_name}() throws Exception {{\n"
                f"{textwrap.indent(method_body, '        ')}\n"
                f"    }}"
            )
            safe_label = t.name.replace('"', '\\"')[:80]
            test_calls.append(f'runTest("{safe_label}", () -> {{ try {{ {method_name}(); }} catch(Exception e) {{ throw new RuntimeException(e); }} }});')

        src = _JAVA_RUNNER_TEMPLATE.format(
            test_methods="\n\n".join(test_methods),
            test_calls="\n        ".join(test_calls),
        )
        src_file = tmpdir / "TestRunner.java"
        src_file.write_text(src, encoding="utf-8")

        # Compile
        rc, compile_out = await _run_subprocess(
            [self._JAVAC_BIN, str(src_file)], str(tmpdir), settings.SANDBOX_EXECUTION_TIMEOUT
        )
        if rc != 0:
            return _error_result(
                tests,
                f"COMPILATION_ERROR:\n{compile_out[:2048]}",
            )

        # Execute
        rc, run_out = await _run_subprocess(
            [self._JAVA_BIN, "-cp", str(tmpdir), "TestRunner"],
            str(tmpdir),
            settings.SANDBOX_EXECUTION_TIMEOUT,
        )
        return self._parse(run_out, rc, len(tests))

    @staticmethod
    def _extract_body(code: str) -> str:
        """
        Extract the body suitable for embedding inside a method.
        Handles three cases:
          1. Code is already a bare statement block
          2. Code is wrapped in a void method  → extract body
          3. Code is a class                   → extract first method body
        """
        code = textwrap.dedent(code)
        # Remove public/private/static method wrappers, keep body
        m = re.search(r"\{([\s\S]+)\}\s*$", code)
        if m:
            return m.group(1).strip()
        return code.strip()

    @staticmethod
    def _parse(output: str, returncode: int, total: int) -> TestRunResult:
        passed = failed = 0
        m = re.search(r"# passed:\s*(\d+),\s*failed:\s*(\d+)", output)
        if m:
            passed, failed = int(m.group(1)), int(m.group(2))
        elif returncode != 0:
            failed = total
        return TestRunResult(
            total=passed + failed,
            passed=passed,
            failed=failed,
            skipped=0,
            execution_output=output[:4096],
        )


# ──────────────────────────────────────────────────────────────────────────────
# C++ adapter
# ──────────────────────────────────────────────────────────────────────────────

_CPP_RUNNER_TEMPLATE = """\
#include <iostream>
#include <stdexcept>
#include <string>
#include <functional>
#include <vector>

static int g_passed = 0;
static int g_failed = 0;

void run_test(const std::string& name, std::function<void()> fn) {{
    try {{
        fn();
        std::cout << "ok - " << name << std::endl;
        ++g_passed;
    }} catch (const std::exception& e) {{
        std::cout << "not ok - " << name << ": " << e.what() << std::endl;
        ++g_failed;
    }} catch (...) {{
        std::cout << "not ok - " << name << ": unknown exception" << std::endl;
        ++g_failed;
    }}
}}

// ── test functions ─────────────────────────────────────────────────────────
{test_functions}

// ── main ───────────────────────────────────────────────────────────────────
int main() {{
    {test_calls}
    std::cout << std::endl
              << "# passed: " << g_passed
              << ", failed: " << g_failed << std::endl;
    return (g_failed > 0) ? 1 : 0;
}}
"""


class CppAdapter(BaseAdapter):
    """
    Compiles and executes C++ test code using g++ and runs the binary.
    If g++ is not available, returns an error result.
    """

    _GPP_BIN: str | None = shutil.which("g++")

    async def run(self, tests: List[GeneratedTest], tmpdir: Path) -> TestRunResult:
        if not tests:
            return TestRunResult(total=0, passed=0, failed=0, skipped=0,
                                 execution_output="No tests to run.")

        if not self._GPP_BIN:
            return _error_result(
                tests,
                "RUNTIME_NOT_FOUND: 'g++' compiler not found. "
                "Install GCC/MinGW to compile and run C++ tests.",
            )

        # Build a single test runner
        test_functions: List[str] = []
        test_calls: List[str] = []
        for i, t in enumerate(tests):
            fn_name = f"test_{i}"
            body = textwrap.indent(textwrap.dedent(t.test_code).strip(), "    ")
            test_functions.append(f"void {fn_name}() {{\n{body}\n}}")
            safe_label = t.name.replace('"', '\\"')[:80]
            test_calls.append(f'run_test("{safe_label}", {fn_name});')

        src = _CPP_RUNNER_TEMPLATE.format(
            test_functions="\n\n".join(test_functions),
            test_calls="\n    ".join(test_calls),
        )
        src_file = tmpdir / "test_runner.cpp"
        src_file.write_text(src, encoding="utf-8")
        bin_file = tmpdir / "test_runner_bin"

        # Compile
        rc, compile_out = await _run_subprocess(
            [self._GPP_BIN, "-std=c++17", "-o", str(bin_file), str(src_file)],
            str(tmpdir),
            settings.SANDBOX_EXECUTION_TIMEOUT,
        )
        if rc != 0:
            return _error_result(
                tests,
                f"COMPILATION_ERROR:\n{compile_out[:2048]}",
            )

        # Execute
        rc, run_out = await _run_subprocess(
            [str(bin_file)],
            str(tmpdir),
            settings.SANDBOX_EXECUTION_TIMEOUT,
        )
        return self._parse(run_out, rc, len(tests))

    @staticmethod
    def _parse(output: str, returncode: int, total: int) -> TestRunResult:
        passed = failed = 0
        m = re.search(r"# passed:\s*(\d+),\s*failed:\s*(\d+)", output)
        if m:
            passed, failed = int(m.group(1)), int(m.group(2))
        elif returncode != 0:
            failed = total
        return TestRunResult(
            total=passed + failed,
            passed=passed,
            failed=failed,
            skipped=0,
            execution_output=output[:4096],
        )
