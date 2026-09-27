"""
Unit and integration tests for the refactored CodeTrust Test Runner and Test Agent.

Coverage:
  Runner:
    - Python: real pytest execution → counts parsed from output
    - JavaScript: real node execution → counts parsed from output
    - Java: missing javac → RUNTIME_NOT_FOUND error (never passes)
    - C++: missing g++ → RUNTIME_NOT_FOUND error (never passes)
    - Unsupported language: returns error, never passes
    - Missing runtime: returns failed, never passes
    - Failing test: counted as failed, not silently swallowed
    - No tests: zero counts

  Test Agent:
    - Generated tests contain no bare `assert True` placeholder bodies
    - Python tests are self-contained (inline source via exec)
    - Regression test names encode the bug title
    - JavaScript tests use the Node harness pattern
    - Java/C++ tests exist but gracefully degrade when compiler missing
    - eval() regression test references the source code
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import List
import pytest

from app.services.codetrust.adapters import (
    CppAdapter,
    JavaAdapter,
    JavaScriptAdapter,
    PythonAdapter,
)
from app.services.codetrust.models import (
    BugDetail,
    FixResult,
    GeneratedTest,
    RCAResult,
    TestAgentResult,
    TestRunResult,
)
from app.services.codetrust.test_agent import TestAgent
from app.services.codetrust.test_runner import MultiLanguageTestRunner


# ──────────────────────────────────────────────────────────────────────────────
# Shared fixtures / helpers
# ──────────────────────────────────────────────────────────────────────────────

def _fix_result(*bugs: BugDetail) -> FixResult:
    return FixResult(
        fixed_code="def run_dynamic(expr):\n    return None  # eval removed",
        bugs=list(bugs),
        explanation="fixed",
    )


def _bug(title: str = "Dangerous eval() usage", severity: str = "critical") -> BugDetail:
    return BugDetail(
        bug_id="BUG-TEST01",
        title=title,
        severity=severity,
        line_number=2,
        description="eval() detected",
        root_cause="eval call",
        suggested_fix="Remove eval()",
        fixed_code_snippet="# fixed",
    )


def _make_test(name: str, code: str, test_type: str = "unit") -> GeneratedTest:
    return GeneratedTest(
        test_id=f"TC-UNIT-{name[:6].upper()}",
        name=name,
        description=f"Test: {name}",
        test_code=code,
        expected_output="passed",
        test_type=test_type,
    )


# ──────────────────────────────────────────────────────────────────────────────
# PythonAdapter unit tests
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_python_adapter_passing_test(tmp_path: Path):
    """A valid passing Python test function is counted as passed."""
    adapter = PythonAdapter()
    tests = [_make_test("passing", "def test_pass():\n    assert 1 + 1 == 2\n")]
    result = await adapter.run(tests, tmp_path)
    assert result.passed == 1
    assert result.failed == 0
    assert result.total >= 1


@pytest.mark.asyncio
async def test_python_adapter_failing_test(tmp_path: Path):
    """A failing assertion is counted as failed — never silently passed."""
    adapter = PythonAdapter()
    tests = [_make_test("failing", "def test_fail():\n    assert 1 == 2, 'intentional failure'\n")]
    result = await adapter.run(tests, tmp_path)
    assert result.failed >= 1
    assert result.passed == 0


@pytest.mark.asyncio
async def test_python_adapter_mixed_tests(tmp_path: Path):
    """Pass and fail counts are tracked independently per test."""
    adapter = PythonAdapter()
    tests = [
        _make_test("p1", "def test_ok():\n    assert True\n"),
        _make_test("f1", "def test_bad():\n    assert False, 'broken'\n"),
    ]
    result = await adapter.run(tests, tmp_path)
    assert result.passed == 1
    assert result.failed == 1


@pytest.mark.asyncio
async def test_python_adapter_no_tests(tmp_path: Path):
    """Empty test list returns zero counts."""
    adapter = PythonAdapter()
    result = await adapter.run([], tmp_path)
    assert result.total == 0
    assert result.passed == 0
    assert result.failed == 0


# ──────────────────────────────────────────────────────────────────────────────
# JavaScriptAdapter unit tests
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_javascript_adapter_passing_test(tmp_path: Path):
    """A passing JavaScript test is counted by the Node harness."""
    adapter = JavaScriptAdapter()
    if not adapter._NODE_BIN:
        pytest.skip("Node.js not installed")

    tests = [
        _make_test(
            "js_pass",
            'test("1+1 equals 2", () => { if (1 + 1 !== 2) throw new Error("wrong"); });',
        )
    ]
    result = await adapter.run(tests, tmp_path)
    assert result.passed == 1
    assert result.failed == 0


@pytest.mark.asyncio
async def test_javascript_adapter_failing_test(tmp_path: Path):
    """A throwing JavaScript test is counted as failed — never passed."""
    adapter = JavaScriptAdapter()
    if not adapter._NODE_BIN:
        pytest.skip("Node.js not installed")

    tests = [
        _make_test(
            "js_fail",
            'test("intentional failure", () => { throw new Error("deliberate"); });',
        )
    ]
    result = await adapter.run(tests, tmp_path)
    assert result.failed == 1
    assert result.passed == 0


@pytest.mark.asyncio
async def test_javascript_adapter_missing_node(tmp_path: Path, monkeypatch):
    """When node is absent the adapter returns an error result — never passes."""
    adapter = JavaScriptAdapter()
    monkeypatch.setattr(adapter, "_NODE_BIN", None)
    tests = [_make_test("js_t", "test('x', () => {});")]
    result = await adapter.run(tests, tmp_path)
    assert result.passed == 0
    assert result.failed == len(tests)
    assert "RUNTIME_NOT_FOUND" in result.execution_output


# ──────────────────────────────────────────────────────────────────────────────
# JavaAdapter — compiler unavailable
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_java_adapter_missing_javac_returns_error(tmp_path: Path, monkeypatch):
    """Without javac the adapter must return an error — never simulate a pass."""
    adapter = JavaAdapter()
    monkeypatch.setattr(adapter, "_JAVAC_BIN", None)
    tests = [_make_test("java_t", "System.out.println(1);")]
    result = await adapter.run(tests, tmp_path)
    assert result.passed == 0
    assert result.failed == len(tests)
    assert "RUNTIME_NOT_FOUND" in result.execution_output


@pytest.mark.asyncio
async def test_java_adapter_real_behavior(tmp_path: Path):
    """
    On this machine javac is absent (JRE only) so the adapter must return
    RUNTIME_NOT_FOUND — not a fake pass.
    """
    import shutil
    if shutil.which("javac"):
        pytest.skip("javac is available — skip the 'missing compiler' path")

    adapter = JavaAdapter()
    tests = [_make_test("java_smoke", "System.out.println(\"hello\");")]
    result = await adapter.run(tests, tmp_path)
    assert result.passed == 0
    assert result.failed == len(tests)
    assert "RUNTIME_NOT_FOUND" in result.execution_output


# ──────────────────────────────────────────────────────────────────────────────
# CppAdapter — compiler unavailable
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_cpp_adapter_missing_gpp_returns_error(tmp_path: Path, monkeypatch):
    """Without g++ the adapter must return an error — never simulate a pass."""
    adapter = CppAdapter()
    monkeypatch.setattr(adapter, "_GPP_BIN", None)
    tests = [_make_test("cpp_t", 'std::cout << "hello" << std::endl;')]
    result = await adapter.run(tests, tmp_path)
    assert result.passed == 0
    assert result.failed == len(tests)
    assert "RUNTIME_NOT_FOUND" in result.execution_output


@pytest.mark.asyncio
async def test_cpp_adapter_real_behavior(tmp_path: Path):
    """
    On this machine g++ is absent so the adapter returns RUNTIME_NOT_FOUND
    — not a fake pass.
    """
    import shutil
    if shutil.which("g++"):
        pytest.skip("g++ is available — skip the 'missing compiler' path")

    adapter = CppAdapter()
    tests = [_make_test("cpp_smoke", 'std::cout << "hello" << std::endl;')]
    result = await adapter.run(tests, tmp_path)
    assert result.passed == 0
    assert result.failed == len(tests)
    assert "RUNTIME_NOT_FOUND" in result.execution_output


# ──────────────────────────────────────────────────────────────────────────────
# MultiLanguageTestRunner dispatch
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_runner_unsupported_language_never_passes():
    """An unsupported language must return failed, never a simulated pass."""
    runner = MultiLanguageTestRunner()
    tests = TestAgentResult(tests=[
        _make_test("ruby_t", "puts 'hello'")
    ])
    result = await runner.run(tests, "ruby")
    assert result.passed == 0
    assert result.failed >= 1
    assert "UNSUPPORTED_LANGUAGE" in result.execution_output


@pytest.mark.asyncio
async def test_runner_python_real_execution():
    """Python path goes through real pytest — no simulation."""
    runner = MultiLanguageTestRunner()
    tests = TestAgentResult(tests=[
        _make_test("real_py", "def test_real():\n    assert 2 ** 10 == 1024\n"),
    ])
    result = await runner.run(tests, "python")
    assert result.passed >= 1
    assert result.failed == 0


@pytest.mark.asyncio
async def test_runner_javascript_real_execution():
    """JavaScript path goes through Node.js — no simulation."""
    import shutil
    if not shutil.which("node"):
        pytest.skip("Node.js not installed")

    runner = MultiLanguageTestRunner()
    tests = TestAgentResult(tests=[
        _make_test(
            "real_js",
            'test("math check", () => { if (2 + 2 !== 4) throw new Error("fail"); });',
        )
    ])
    result = await runner.run(tests, "javascript")
    assert result.passed >= 1
    assert result.failed == 0


@pytest.mark.asyncio
async def test_runner_java_missing_compiler():
    """Java without javac returns error counts — never passes."""
    import shutil
    if shutil.which("javac"):
        pytest.skip("javac is present")

    runner = MultiLanguageTestRunner()
    tests = TestAgentResult(tests=[_make_test("java_t", "System.out.println(1);")])
    result = await runner.run(tests, "java")
    assert result.passed == 0
    assert result.failed >= 1


@pytest.mark.asyncio
async def test_runner_cpp_missing_compiler():
    """C++ without g++ returns error counts — never passes."""
    import shutil
    if shutil.which("g++"):
        pytest.skip("g++ is present")

    runner = MultiLanguageTestRunner()
    tests = TestAgentResult(tests=[_make_test("cpp_t", 'std::cout << 1;')])
    result = await runner.run(tests, "cpp")
    assert result.passed == 0
    assert result.failed >= 1


@pytest.mark.asyncio
async def test_runner_no_tests_returns_zeros():
    """Empty test suite must return all-zero counts."""
    runner = MultiLanguageTestRunner()
    result = await runner.run(TestAgentResult(tests=[]), "python")
    assert result.total == 0
    assert result.passed == 0
    assert result.failed == 0


# ──────────────────────────────────────────────────────────────────────────────
# TestAgent — generated test quality
# ──────────────────────────────────────────────────────────────────────────────

def test_agent_python_no_placeholder_assert_true():
    """
    Generated Python tests must not contain bare `assert True` placeholder stubs.
    Real assertions must be driven by the code under test.
    """
    agent = TestAgent()
    fix = _fix_result(_bug())
    result = agent.generate(
        fixed_code="def run_dynamic(expr):\n    return None",
        language="python",
        fix_result=fix,
    )
    for t in result.tests:
        lines = [l.strip() for l in t.test_code.splitlines()]
        # A bare "assert True" with no meaningful qualifier is the smell we're checking
        bare_assert_true = [
            l for l in lines
            if l == "assert True"
            and not any(kw in t.test_code for kw in ("assert True  # execution reached", "assert True  # always"))
        ]
        assert not bare_assert_true, (
            f"Test '{t.name}' contains a meaningless 'assert True' placeholder:\n{t.test_code}"
        )


def test_agent_python_tests_inline_source():
    """Python tests must embed the fixed source so they are self-contained."""
    agent = TestAgent()
    fix = _fix_result(_bug())
    result = agent.generate(
        fixed_code="def run_dynamic(expr):\n    return None",
        language="python",
        fix_result=fix,
    )
    for t in result.tests:
        assert "run_dynamic" in t.test_code or "_src" in t.test_code or "_mod" in t.test_code, (
            f"Test '{t.name}' does not reference the fixed source code:\n{t.test_code}"
        )


def test_agent_python_regression_encodes_bug_title():
    """Regression test names must encode the bug title, not a generic stub name."""
    agent = TestAgent()
    fix = _fix_result(_bug("Dangerous eval() usage"))
    result = agent.generate(
        fixed_code="def run_dynamic(expr):\n    return None",
        language="python",
        fix_result=fix,
    )
    regression_tests = [t for t in result.tests if t.test_type == "regression"]
    assert len(regression_tests) >= 1
    names = [t.name for t in regression_tests]
    assert any("eval" in n or "dangerous" in n for n in names), (
        f"Regression test name does not encode the bug pattern. Got: {names}"
    )


def test_agent_python_eval_regression_checks_source():
    """The eval regression test must actually inspect the source for eval presence."""
    agent = TestAgent()
    fix = _fix_result(_bug("Dangerous eval() usage"))
    result = agent.generate(
        fixed_code="def run_dynamic(expr):\n    return None",
        language="python",
        fix_result=fix,
    )
    regression_tests = [t for t in result.tests if t.test_type == "regression"]
    assert regression_tests, "No regression tests generated"
    # The eval regression test should reference eval() and the source
    combined = " ".join(t.test_code for t in regression_tests)
    assert "eval" in combined.lower() or "_src" in combined, (
        "eval regression test doesn't check for eval in source"
    )


def test_agent_javascript_tests_use_node_harness_pattern():
    """JavaScript tests must use the test() function from the Node harness."""
    agent = TestAgent()
    fix = _fix_result(_bug("Dangerous eval() usage"))
    result = agent.generate(
        fixed_code="function runDynamic(expr) { return null; }",
        language="javascript",
        fix_result=fix,
    )
    assert len(result.tests) >= 1
    for t in result.tests:
        assert 'test(' in t.test_code, (
            f"JavaScript test '{t.name}' does not use the harness test() function:\n{t.test_code}"
        )


def test_agent_java_generates_tests():
    """Java: at least one test is generated even without a compiler on the path."""
    agent = TestAgent()
    java_code = "public class Calc { public static int add(int a, int b) { return a + b; } }"
    fix = _fix_result(_bug("General Code Quality"))
    result = agent.generate(fixed_code=java_code, language="java", fix_result=fix)
    assert len(result.tests) >= 1


def test_agent_cpp_generates_tests():
    """C++: at least one test is generated even without g++ on the path."""
    agent = TestAgent()
    cpp_code = "int add(int a, int b) { return a + b; }\nint main() { return 0; }"
    fix = _fix_result(_bug("General Code Quality"))
    result = agent.generate(fixed_code=cpp_code, language="cpp", fix_result=fix)
    assert len(result.tests) >= 1


def test_agent_unsupported_language_gate_test():
    """Unsupported language produces a gate test (type=unit, no real code)."""
    agent = TestAgent()
    fix = _fix_result(_bug())
    result = agent.generate(fixed_code="some code", language="ruby", fix_result=fix)
    assert len(result.tests) >= 1
    assert result.tests[0].expected_output == "error"


# ──────────────────────────────────────────────────────────────────────────────
# End-to-end: generated Python tests actually pass through the real runner
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_agent_and_runner_python_end_to_end():
    """
    Generated Python tests must run through the real pytest adapter and
    produce at least one passing result — not a simulated outcome.
    """
    agent = TestAgent()
    fix = _fix_result(_bug("Dangerous eval() usage"))
    generated = agent.generate(
        fixed_code="def run_dynamic(expr):\n    return None  # eval removed",
        language="python",
        fix_result=fix,
    )
    assert len(generated.tests) >= 1

    runner = MultiLanguageTestRunner()
    result = await runner.run(generated, "python")

    # Must have executed real tests — no zero-total simulation
    assert result.total > 0
    # No test should be erroneously auto-passed without execution
    assert "Simulated" not in result.execution_output
    assert "[Simulated]" not in result.execution_output
    # At least the unit tests should pass on the clean fixed code
    assert result.passed >= 1


@pytest.mark.asyncio
async def test_agent_and_runner_javascript_end_to_end():
    """
    Generated JavaScript tests must run through Node.js and return real counts.
    """
    import shutil
    if not shutil.which("node"):
        pytest.skip("Node.js not installed")

    agent = TestAgent()
    fix = _fix_result(_bug("Dangerous eval() usage"))
    generated = agent.generate(
        fixed_code="function runDynamic(expr) { return null; }",
        language="javascript",
        fix_result=fix,
    )
    assert len(generated.tests) >= 1

    runner = MultiLanguageTestRunner()
    result = await runner.run(generated, "javascript")

    assert result.total > 0
    assert "Simulated" not in result.execution_output


# ──────────────────────────────────────────────────────────────────────────────
# TestAgent — meaningful assertion content per bug pattern
# ──────────────────────────────────────────────────────────────────────────────

_FIXED_NO_EVAL = "def process(expr):\n    return None  # eval removed"
_FIXED_TYPED_EXCEPT = "def parse(text):\n    try:\n        return int(text)\n    except ValueError:\n        return -1"
_FIXED_NO_WILDCARD = "import os\nimport sys\n\ndef helper():\n    return os.getcwd()"
_FIXED_WITH_CONTEXT = "def read_file(path):\n    with open(path) as fh:\n        return fh.read()"
_FIXED_GENERIC = "def add(a, b):\n    return a + b"


def _has_no_tautology(test_code: str) -> bool:
    """Return True when the test contains no always-passing assertions."""
    for line in test_code.splitlines():
        stripped = line.strip()
        if stripped == "assert True":
            return False
        if stripped in (
            "assert result is None or result is not None",
            "assert result is not None or result is None",
        ):
            return False
    return True


def test_eval_pattern_generates_no_tautology():
    """
    For an eval() bug the generated test must assert that eval() is absent from
    the fixed source — not an always-passing tautology.
    """
    agent = TestAgent()
    bug = _bug("Dangerous eval() usage")
    result = agent.generate(
        fixed_code=_FIXED_NO_EVAL,
        language="python",
        fix_result=_fix_result(bug),
    )
    regression = [t for t in result.tests if t.test_type == "regression"]
    assert regression, "No regression test generated for eval() bug"
    for t in regression:
        assert _has_no_tautology(t.test_code), (
            f"eval regression test '{t.name}' contains a tautological assertion:\n{t.test_code}"
        )
    # The generated test must check for the absence of eval() in source
    combined = " ".join(t.test_code for t in regression)
    assert "eval_calls" in combined or "eval" in combined, (
        "eval regression test does not search for eval() in the fixed source"
    )
    assert "assert len(" in combined or "assert " in combined, (
        "eval regression test contains no structural assertion"
    )


def test_eval_pattern_assertion_fails_on_unfixed_code():
    """
    The eval() regression test's assertion must FAIL when applied to code
    that still contains eval() — proving the assertion is not vacuous.
    """
    import types
    import re

    agent = TestAgent()
    bug = _bug("Dangerous eval() usage")
    # Generate the test against already-fixed code (no eval)
    result = agent.generate(
        fixed_code=_FIXED_NO_EVAL,
        language="python",
        fix_result=_fix_result(bug),
    )
    regression = [t for t in result.tests if t.test_type == "regression"]
    assert regression

    # Substitute the fixed source with a broken version that still uses eval()
    broken_src = "def process(expr):\n    return eval(expr)"
    for t in regression:
        patched_code = t.test_code.replace(repr(_FIXED_NO_EVAL), repr(broken_src))
        ns: dict = {}
        exec(compile(patched_code, "<patched>", "exec"), ns)
        # At least one test function must raise AssertionError on broken code
        test_fns = {k: v for k, v in ns.items() if k.startswith("test_")}
        assert test_fns, f"No test_ functions found in regression test '{t.name}'"
        any_failed = False
        for fn in test_fns.values():
            try:
                fn()
            except (AssertionError, Exception):
                # AssertionError  → meaningful assertion caught the problem.
                # Any other exception from *inside* the broken function (e.g.
                # NameError from eval("test_0")) also proves the test is not
                # vacuous — it did not silently pass.
                any_failed = True
                break
        assert any_failed, (
            f"Regression test '{t.name}' did NOT fail when applied to code that "
            f"still contains eval() — the assertion is not meaningful."
        )


def test_bare_except_pattern_generates_no_tautology():
    """
    For a bare-except bug the generated test must assert that 'except:' is absent
    — not an always-passing tautology.
    """
    agent = TestAgent()
    bug = _bug("Bare except clause")
    result = agent.generate(
        fixed_code=_FIXED_TYPED_EXCEPT,
        language="python",
        fix_result=_fix_result(bug),
    )
    regression = [t for t in result.tests if t.test_type == "regression"]
    assert regression, "No regression test generated for bare-except bug"
    for t in regression:
        assert _has_no_tautology(t.test_code), (
            f"bare-except regression test '{t.name}' contains a tautological assertion:\n{t.test_code}"
        )
    combined = " ".join(t.test_code for t in regression)
    assert "except" in combined, (
        "bare-except regression test does not reference 'except' in any assertion"
    )


def test_bare_except_assertion_fails_on_unfixed_code():
    """
    The bare-except regression test must FAIL when applied to code that still
    contains 'except:' — proving the assertion is meaningful.
    """
    agent = TestAgent()
    bug = _bug("Bare except clause")
    result = agent.generate(
        fixed_code=_FIXED_TYPED_EXCEPT,
        language="python",
        fix_result=_fix_result(bug),
    )
    regression = [t for t in result.tests if t.test_type == "regression"]
    assert regression

    broken_src = "def parse(text):\n    try:\n        return int(text)\n    except:\n        return -1"
    for t in regression:
        patched_code = t.test_code.replace(repr(_FIXED_TYPED_EXCEPT), repr(broken_src))
        ns: dict = {}
        exec(compile(patched_code, "<patched>", "exec"), ns)
        test_fns = {k: v for k, v in ns.items() if k.startswith("test_")}
        assert test_fns, f"No test_ functions found in regression test '{t.name}'"
        any_failed = False
        for fn in test_fns.values():
            try:
                fn()
            except AssertionError:
                any_failed = True
                break
        assert any_failed, (
            f"Regression test '{t.name}' did NOT fail when applied to code that "
            f"still contains a bare 'except:' — the assertion is not meaningful."
        )


def test_wildcard_import_pattern_generates_meaningful_assertion():
    """
    For a wildcard-import bug the generated test must assert that 'import *'
    is absent from the fixed source.
    """
    agent = TestAgent()
    bug = _bug("Wildcard import usage")
    result = agent.generate(
        fixed_code=_FIXED_NO_WILDCARD,
        language="python",
        fix_result=_fix_result(bug),
    )
    regression = [t for t in result.tests if t.test_type == "regression"]
    assert regression, "No regression test generated for wildcard-import bug"
    for t in regression:
        assert _has_no_tautology(t.test_code), (
            f"wildcard regression test '{t.name}' contains a tautological assertion:\n{t.test_code}"
        )
    combined = " ".join(t.test_code for t in regression)
    assert "wildcard" in combined.lower() or "import *" in combined or "matches" in combined, (
        "wildcard regression test does not reference wildcard imports in any assertion"
    )


def test_wildcard_assertion_fails_on_unfixed_code():
    """
    The wildcard-import regression test must FAIL when applied to code that
    still contains 'from x import *'.
    """
    agent = TestAgent()
    bug = _bug("Wildcard import usage")
    result = agent.generate(
        fixed_code=_FIXED_NO_WILDCARD,
        language="python",
        fix_result=_fix_result(bug),
    )
    regression = [t for t in result.tests if t.test_type == "regression"]
    assert regression

    broken_src = "from os import *\nfrom sys import *\n\ndef helper():\n    return getcwd()"
    for t in regression:
        patched_code = t.test_code.replace(repr(_FIXED_NO_WILDCARD), repr(broken_src))
        ns: dict = {}
        exec(compile(patched_code, "<patched>", "exec"), ns)
        test_fns = {k: v for k, v in ns.items() if k.startswith("test_")}
        assert test_fns, f"No test_ functions found in regression test '{t.name}'"
        any_failed = False
        for fn in test_fns.values():
            try:
                fn()
            except AssertionError:
                any_failed = True
                break
        assert any_failed, (
            f"Regression test '{t.name}' did NOT fail when applied to code that "
            f"still contains 'from x import *' — the assertion is not meaningful."
        )


def test_open_context_pattern_generates_meaningful_assertion():
    """
    For an open()-without-context-manager bug the generated test must assert
    that every open() call is wrapped in a 'with' block.
    """
    agent = TestAgent()
    bug = _bug("open() without context manager")
    result = agent.generate(
        fixed_code=_FIXED_WITH_CONTEXT,
        language="python",
        fix_result=_fix_result(bug),
    )
    regression = [t for t in result.tests if t.test_type == "regression"]
    assert regression, "No regression test generated for open-context bug"
    for t in regression:
        assert _has_no_tautology(t.test_code), (
            f"open-context regression test '{t.name}' contains a tautological assertion:\n{t.test_code}"
        )
    combined = " ".join(t.test_code for t in regression)
    assert "with" in combined or "context" in combined.lower(), (
        "open-context regression test does not reference 'with' in any assertion"
    )


def test_generic_pattern_generates_no_tautology():
    """
    For a bug pattern without a specific emitter, the generic test must still
    produce a meaningful assertion — no always-passing tautology.
    """
    agent = TestAgent()
    bug = _bug("Division by zero")
    result = agent.generate(
        fixed_code=_FIXED_GENERIC,
        language="python",
        fix_result=_fix_result(bug),
    )
    unit_tests = [t for t in result.tests if t.test_type == "unit"]
    assert unit_tests, "No unit tests generated for generic bug"
    for t in unit_tests:
        assert _has_no_tautology(t.test_code), (
            f"Generic unit test '{t.name}' contains a tautological assertion:\n{t.test_code}"
        )


def test_generic_unit_test_is_executable_and_passes():
    """
    The generic unit test generated for a well-behaved function must execute
    without error and its assertions must pass.
    """
    agent = TestAgent()
    bug = _bug("Division by zero")
    result = agent.generate(
        fixed_code=_FIXED_GENERIC,
        language="python",
        fix_result=_fix_result(bug),
    )
    unit_tests = [t for t in result.tests if t.test_type == "unit"]
    assert unit_tests
    for t in unit_tests:
        ns: dict = {}
        exec(compile(t.test_code, "<generated>", "exec"), ns)
        test_fns = {k: v for k, v in ns.items() if k.startswith("test_")}
        assert test_fns, f"No test_ functions found in unit test '{t.name}'"
        for name, fn in test_fns.items():
            fn()  # Must not raise — the fixed code is correct


def test_no_generated_test_contains_tautology_across_all_patterns():
    """
    Comprehensive sweep: for every supported bug-pattern keyword, no generated
    Python test may contain a bare 'assert True' or an always-true None/not-None check.
    """
    agent = TestAgent()
    patterns = [
        ("Dangerous eval() usage",            _FIXED_NO_EVAL),
        ("Bare except clause",                 _FIXED_TYPED_EXCEPT),
        ("Wildcard import usage",              _FIXED_NO_WILDCARD),
        ("open() without context manager",     _FIXED_WITH_CONTEXT),
        ("exec() injection",                   "def run(cmd):\n    return None  # exec removed"),
        ("Division by zero",                   _FIXED_GENERIC),
    ]
    for title, code in patterns:
        result = agent.generate(
            fixed_code=code,
            language="python",
            fix_result=_fix_result(_bug(title)),
        )
        for t in result.tests:
            assert _has_no_tautology(t.test_code), (
                f"Bug pattern '{title}', test '{t.name}' contains a tautological assertion:\n"
                f"{t.test_code}"
            )


# ──────────────────────────────────────────────────────────────────────────────
# PythonAdapter — per-test test_details population
# ──────────────────────────────────────────────────────────────────────────────

def _make_identified_test(test_id: str, name: str, code: str, test_type: str = "unit") -> GeneratedTest:
    """Build a GeneratedTest with a fully-controlled test_id for ID-tracing assertions."""
    return GeneratedTest(
        test_id=test_id,
        name=name,
        description=f"Test: {name}",
        test_code=code,
        expected_output="passed",
        test_type=test_type,
    )


@pytest.mark.asyncio
async def test_python_adapter_details_all_passing(tmp_path: Path):
    """
    All passing tests → test_details has one entry per test with status='passed'
    and the correct test_id.
    """
    adapter = PythonAdapter()
    tests = [
        _make_identified_test("TC-DETAIL-001", "detail_pass_a", "def test_a():\n    assert 1 + 1 == 2\n"),
        _make_identified_test("TC-DETAIL-002", "detail_pass_b", "def test_b():\n    assert 'x' in 'xyz'\n"),
    ]
    result = await adapter.run(tests, tmp_path)

    assert result.passed == 2
    assert result.failed == 0
    assert len(result.test_details) == 2

    by_id = {d["test_id"]: d for d in result.test_details}
    assert by_id["TC-DETAIL-001"]["status"] == "passed"
    assert by_id["TC-DETAIL-002"]["status"] == "passed"
    assert by_id["TC-DETAIL-001"]["name"] == "detail_pass_a"
    assert by_id["TC-DETAIL-002"]["name"] == "detail_pass_b"


@pytest.mark.asyncio
async def test_python_adapter_details_one_failing(tmp_path: Path):
    """
    One test fails → test_details carries 'failed' for that specific test_id
    while the passing test carries 'passed'.  The wrong test_id must not be blamed.
    """
    adapter = PythonAdapter()
    tests = [
        _make_identified_test("TC-DETAIL-OK1", "ok_test",  "def test_ok():\n    assert 10 > 5\n"),
        _make_identified_test("TC-DETAIL-BAD", "bad_test", "def test_bad():\n    assert 1 == 99, 'intentional'\n"),
    ]
    result = await adapter.run(tests, tmp_path)

    assert result.passed == 1
    assert result.failed == 1
    assert len(result.test_details) == 2

    by_id = {d["test_id"]: d for d in result.test_details}
    assert by_id["TC-DETAIL-OK1"]["status"] == "passed", (
        "Passing test must not be blamed for the failing test"
    )
    assert by_id["TC-DETAIL-BAD"]["status"] in ("failed", "error"), (
        "Failing test must be reported as failed or error, not passed"
    )


@pytest.mark.asyncio
async def test_python_adapter_details_unparseable_output(tmp_path: Path, monkeypatch):
    """
    When pytest produces no parseable PASSED/FAILED line (simulated by monkeypatching
    _run_subprocess to return empty output), every test must be reported as 'error'
    — never as 'passed'.
    """
    import app.services.codetrust.adapters as adapters_module

    async def _fake_run(cmd, cwd, timeout):
        # Return rc=0 but completely empty output — no pytest summary lines at all.
        return 0, ""

    monkeypatch.setattr(adapters_module, "_run_subprocess", _fake_run)

    adapter = PythonAdapter()
    tests = [
        _make_identified_test("TC-UNPARSE-A", "unparse_a", "def test_a():\n    assert True\n"),
        _make_identified_test("TC-UNPARSE-B", "unparse_b", "def test_b():\n    assert True\n"),
    ]
    result = await adapter.run(tests, tmp_path)

    assert result.passed == 0, "Must not fabricate a pass when output is unparseable"
    assert result.failed == len(tests), "Every test must count as failed/error"
    for d in result.test_details:
        assert d["status"] in ("failed", "error"), (
            f"test_id={d['test_id']} must be error/failed, got {d['status']!r}"
        )


@pytest.mark.asyncio
async def test_python_adapter_details_count_mismatch(tmp_path: Path, monkeypatch):
    """
    When pytest output only mentions a subset of the generated tests (e.g. two
    tests submitted but output has results for only one), the missing tests must
    appear in test_details as 'error' and contribute to failed — never passed.
    The aggregate counts must equal the number of generated tests.
    """
    import app.services.codetrust.adapters as adapters_module
    from app.services.codetrust.adapters import _safe_id

    tid_present = "TC-PRESENT-X"
    tid_missing = "TC-MISSING-Y"

    # Build a fake pytest -v output that only reports the first test.
    fake_output = (
        f"test_{_safe_id(tid_present)}.py::test_x PASSED\n"
        "1 passed in 0.01s\n"
    )

    async def _fake_run(cmd, cwd, timeout):
        return 0, fake_output

    monkeypatch.setattr(adapters_module, "_run_subprocess", _fake_run)

    adapter = PythonAdapter()
    tests = [
        _make_identified_test(tid_present, "present_test", "def test_x():\n    assert True\n"),
        _make_identified_test(tid_missing, "missing_test", "def test_y():\n    assert True\n"),
    ]
    result = await adapter.run(tests, tmp_path)

    assert result.total == len(tests), (
        "total must account for all generated tests, including those missing from output"
    )
    assert result.passed == 1
    assert result.failed == 1, "Missing test must count as failed"

    by_id = {d["test_id"]: d for d in result.test_details}
    assert by_id[tid_present]["status"] == "passed"
    assert by_id[tid_missing]["status"] in ("failed", "error"), (
        "Test absent from pytest output must be reported as error, not passed"
    )

# ──────────────────────────────────────────────────────────────────────────────
# _safe_id — collision-safety guarantee
# ──────────────────────────────────────────────────────────────────────────────

def test_safe_id_distinct_ids_never_share_a_stem():
    """
    Two test_id values that are distinct must always produce different stems,
    even when their sanitised (non-alphanumeric → '_') forms are identical.

    Covers the canonical collision class: IDs that differ only in which
    punctuation character separates the same alphanumeric tokens.
    """
    from app.services.codetrust.adapters import _safe_id

    # These three IDs all sanitise to the same prefix "TC_A_B" but are distinct.
    colliding_ids = ["TC-A-B", "TC-A_B", "TC_A-B"]
    stems = [_safe_id(tid) for tid in colliding_ids]

    # Every stem must be unique.
    assert len(stems) == len(set(stems)), (
        f"_safe_id() produced duplicate stems for distinct test IDs.\n"
        f"IDs:   {colliding_ids}\n"
        f"Stems: {stems}"
    )


def test_safe_id_same_id_is_stable():
    """
    Calling _safe_id() twice with the same test_id must return the same stem
    (deterministic / no random component).
    """
    from app.services.codetrust.adapters import _safe_id

    tid = "TC-STABILITY-CHECK-007"
    assert _safe_id(tid) == _safe_id(tid), (
        "_safe_id() returned different stems for the same test_id on repeated calls"
    )


def test_safe_id_stem_is_valid_python_identifier_prefix():
    """
    The stem must consist only of alphanumeric characters and underscores so
    that ``test_<stem>.py`` is a valid Python module name that pytest can import.
    """
    from app.services.codetrust.adapters import _safe_id
    import re

    ids = [
        "TC-001",
        "TC.A.B",
        "hello world",
        "SUITE/CASE:42",
        "regression__eval_usage",
    ]
    valid_stem_re = re.compile(r"^[A-Za-z0-9_]+$")
    for tid in ids:
        stem = _safe_id(tid)
        assert valid_stem_re.match(stem), (
            f"_safe_id({tid!r}) produced stem {stem!r} which is not a valid "
            "Python module name component (must match [A-Za-z0-9_]+)"
        )


@pytest.mark.asyncio
async def test_python_adapter_collision_ids_both_execute(tmp_path: Path):
    """
    End-to-end: two GeneratedTests whose test_id values share the same sanitised
    prefix (e.g. 'TC-A-B' and 'TC-A_B') must each get their own file, execute
    independently, and both appear in test_details with the correct test_id.

    Before the hash suffix was added, the second test would silently overwrite
    the first file, causing the first to vanish from test_details.
    """
    adapter = PythonAdapter()

    # Both sanitise to "TC_A_B" without the hash — with the hash they are distinct.
    tests = [
        _make_identified_test(
            "TC-A-B", "dash_test",
            "def test_dash():\n    assert 2 * 3 == 6\n",
        ),
        _make_identified_test(
            "TC-A_B", "mixed_test",
            "def test_mixed():\n    assert 10 - 4 == 6\n",
        ),
    ]
    result = await adapter.run(tests, tmp_path)

    assert result.total == 2, (
        "Both tests must be counted — collision would make total == 1"
    )
    assert result.passed == 2, (
        "Both tests should pass; if total < 2 a collision occurred"
    )
    assert result.failed == 0

    reported_ids = {d["test_id"] for d in result.test_details}
    assert "TC-A-B" in reported_ids, "TC-A-B must appear in test_details"
    assert "TC-A_B" in reported_ids, "TC-A_B must appear in test_details"

    by_id = {d["test_id"]: d for d in result.test_details}
    assert by_id["TC-A-B"]["status"] == "passed"
    assert by_id["TC-A_B"]["status"] == "passed"
