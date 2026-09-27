"""
Integration tests for POST /api/v1/analyze — CodeTrust Orchestrator integration.

Test matrix:
  1.  Successful end-to-end analysis
  2.  RCA result reaches the API response
  3.  Proposed fix reaches the API response
  4.  Generated tests reach the API response
  5.  Actual test execution results reach the verification report
  6.  Verification result reaches the API response
  7.  Verification failure is represented correctly
  8.  Invalid input still returns 422
  9.  Existing health endpoint still works (sanity)
  10. Existing history endpoint still works (sanity)

Dependency injection is used to stub the CodeTrust Orchestrator so that
tests are fast, deterministic, and do not require network or subprocess access.
"""
import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient

from app.services.codetrust.models import (
    BugDetail,
    FixResult,
    GeneratedTest,
    OrchestratorResult,
    RCAResult,
    TestAgentResult,
    TestRunResult,
    VerificationResult,
)


# ─── Shared helpers ───────────────────────────────────────────────────────────

def _make_orchestrator_result(
    *,
    verified: bool = True,
    failed_tests: int = 0,
    passed_tests: int = 2,
    regressions: list[str] | None = None,
    remaining_risks: list[str] | None = None,
    rca_summary: str = "RCA completed: 1 pattern(s) found in python code.",
    bugs: list[BugDetail] | None = None,
    tests: list[GeneratedTest] | None = None,
) -> OrchestratorResult:
    """Build a fully-populated OrchestratorResult for stubbing."""
    if bugs is None:
        bugs = [
            BugDetail(
                bug_id="BUG-AAAAAA",
                title="Use of dangerous eval() — arbitrary code execution risk",
                severity="critical",
                line_number=2,
                description="Detected on line 2: 'return eval(expr)'",
                root_cause="Line 2: Use of dangerous eval()",
                suggested_fix="Replace eval() with ast.literal_eval()",
                fixed_code_snippet="import ast\n# Use ast.literal_eval(expr) instead",
            )
        ]
    if tests is None:
        tests = [
            GeneratedTest(
                test_id="TC-000001",
                name="test_run_dynamic_standard_input",
                description="Standard test.",
                test_code="def test_run_dynamic_standard_input():\n    assert True",
                expected_output="Assertion passed",
                test_type="unit",
            ),
            GeneratedTest(
                test_id="TC-000002",
                name="regression__use_of_dangerous_eval",
                description="Regression test.",
                test_code="def test_regression():\n    assert True",
                expected_output="Assertion passed",
                test_type="regression",
            ),
        ]

    vr_status = "verified" if verified else "failed"
    return OrchestratorResult(
        session_id="test-session-123",
        language="python",
        rca=RCAResult(
            summary=rca_summary,
            root_causes=["Line 2: Use of dangerous eval()"],
            affected_lines=[2],
            severity="critical",
            confidence=0.85,
        ),
        fix=FixResult(
            fixed_code="def run_dynamic(expr):\n    # fixed: use ast.literal_eval\n    return None",
            bugs=bugs,
            explanation="Fix Agent produced 1 fix proposal(s).",
        ),
        tests=TestAgentResult(tests=tests),
        test_run=TestRunResult(
            passed=passed_tests,
            failed=failed_tests,
            skipped=0,
            total=passed_tests + failed_tests,
            execution_output=f"{passed_tests} passed" + (f", {failed_tests} failed" if failed_tests else ""),
        ),
        verification=VerificationResult(
            verified=verified,
            confidence=0.80 if verified else 0.30,
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            regressions=regressions or [],
            remaining_risks=remaining_risks or [],
            evidence=[
                f"Test execution: {passed_tests} passed, {failed_tests} failed, 0 skipped.",
                "RCA severity: critical. RCA confidence: 0.85.",
                "Fix Agent produced 1 fix proposal(s).",
            ],
            status=vr_status,
        ),
        analysis_time_ms=42.0,
    )


_VALID_PAYLOAD = {
    "code": "def run_dynamic(expr):\n    return eval(expr)",
    "language": "python",
    "file_name": "unsafe.py",
    "context_description": "eval is being used unsafely",
    "generate_test_cases": True,
}


# ─── 1. Successful end-to-end analysis ───────────────────────────────────────

@pytest.mark.asyncio
async def test_successful_end_to_end_analysis(client: AsyncClient):
    """
    Full pipeline runs without errors and returns a well-formed 200 response.
    The stub returns a verified result so all fields should be populated.
    """
    stub = _make_orchestrator_result()
    with patch(
        "app.services.ai_agent.CodeTrustOrchestrator.run",
        new=AsyncMock(return_value=stub),
    ):
        response = await client.post("/api/v1/analyze", json=_VALID_PAYLOAD)

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["message"] == "Code analyzed successfully"
    data = body["data"]
    assert data["session_id"] == "test-session-123"
    assert data["language"] == "python"
    assert data["status"] == "completed"
    assert data["analysis_time_ms"] == 42.0
    assert isinstance(data["bugs"], list)
    assert isinstance(data["test_cases"], list)
    assert "verification_report" in data


# ─── 2. RCA result reaches the API response ──────────────────────────────────

@pytest.mark.asyncio
async def test_rca_result_in_api_response(client: AsyncClient):
    """
    The summary field in the response should reflect the RCA + verification outcome.
    Bugs detected by the RCA/Fix Agent must appear in bugs[].
    """
    stub = _make_orchestrator_result(rca_summary="RCA completed: 1 pattern(s) found in python code.")
    with patch(
        "app.services.ai_agent.CodeTrustOrchestrator.run",
        new=AsyncMock(return_value=stub),
    ):
        response = await client.post("/api/v1/analyze", json=_VALID_PAYLOAD)

    data = response.json()["data"]
    assert data["total_bugs_detected"] == 1
    assert len(data["bugs"]) == 1
    bug = data["bugs"][0]
    assert bug["bug_id"] == "BUG-AAAAAA"
    assert "eval" in bug["title"].lower()
    assert bug["severity"] == "critical"
    assert bug["line_number"] == 2
    assert "CodeTrust analysis completed" in data["summary"]


# ─── 3. Proposed fix reaches the API response ────────────────────────────────

@pytest.mark.asyncio
async def test_proposed_fix_in_api_response(client: AsyncClient):
    """
    The fixed_code field in the response should contain the Fix Agent's output.
    """
    stub = _make_orchestrator_result()
    with patch(
        "app.services.ai_agent.CodeTrustOrchestrator.run",
        new=AsyncMock(return_value=stub),
    ):
        response = await client.post("/api/v1/analyze", json=_VALID_PAYLOAD)

    data = response.json()["data"]
    assert data["fixed_code"] is not None
    assert "fixed" in data["fixed_code"] or "ast" in data["fixed_code"] or "def" in data["fixed_code"]


# ─── 4. Generated tests reach the API response ───────────────────────────────

@pytest.mark.asyncio
async def test_generated_tests_in_api_response(client: AsyncClient):
    """
    test_cases[] in the response must map exactly to the Test Agent's output.
    """
    stub = _make_orchestrator_result()
    with patch(
        "app.services.ai_agent.CodeTrustOrchestrator.run",
        new=AsyncMock(return_value=stub),
    ):
        response = await client.post("/api/v1/analyze", json=_VALID_PAYLOAD)

    data = response.json()["data"]
    assert len(data["test_cases"]) == 2
    test_ids = [tc["test_id"] for tc in data["test_cases"]]
    assert "TC-000001" in test_ids
    assert "TC-000002" in test_ids
    test_types = {tc["test_type"] for tc in data["test_cases"]}
    assert "unit" in test_types
    assert "regression" in test_types


# ─── 5. Actual test execution results reach verification ─────────────────────

@pytest.mark.asyncio
async def test_test_execution_results_reach_verification(client: AsyncClient):
    """
    The verification_report must reflect the actual pass/fail counts from the
    Test Runner — not zeroed-out or fabricated values.
    """
    stub = _make_orchestrator_result(passed_tests=2, failed_tests=0)
    with patch(
        "app.services.ai_agent.CodeTrustOrchestrator.run",
        new=AsyncMock(return_value=stub),
    ):
        response = await client.post("/api/v1/analyze", json=_VALID_PAYLOAD)

    vr = response.json()["data"]["verification_report"]
    assert vr["passed_tests"] == 2
    assert vr["failed_tests"] == 0
    # Evidence must contain test execution info
    assert any("passed" in ev.lower() for ev in vr["evidence"])


# ─── 6. Verification result reaches the API response ─────────────────────────

@pytest.mark.asyncio
async def test_verification_result_in_api_response(client: AsyncClient):
    """
    verification_report must contain all required verification fields.
    """
    stub = _make_orchestrator_result(verified=True)
    with patch(
        "app.services.ai_agent.CodeTrustOrchestrator.run",
        new=AsyncMock(return_value=stub),
    ):
        response = await client.post("/api/v1/analyze", json=_VALID_PAYLOAD)

    vr = response.json()["data"]["verification_report"]
    assert vr["verified"] is True
    assert vr["status"] == "verified"
    assert 0.0 <= vr["confidence"] <= 1.0
    assert isinstance(vr["passed_tests"], int)
    assert isinstance(vr["failed_tests"], int)
    assert isinstance(vr["regressions"], list)
    assert isinstance(vr["remaining_risks"], list)
    assert isinstance(vr["evidence"], list)
    assert len(vr["evidence"]) > 0


# ─── 7. Verification failure is represented correctly ────────────────────────

@pytest.mark.asyncio
async def test_verification_failure_represented_correctly(client: AsyncClient):
    """
    When the Verification Agent reports failure the API must surface it
    faithfully — verified=False, status='failed', regressions populated.
    The overall API call should still succeed with HTTP 200.
    """
    stub = _make_orchestrator_result(
        verified=False,
        passed_tests=1,
        failed_tests=1,
        regressions=["1 test(s) failed after applying the fix — investigate before merging."],
        remaining_risks=["Unaddressed: Line 2: Use of dangerous eval()"],
    )
    with patch(
        "app.services.ai_agent.CodeTrustOrchestrator.run",
        new=AsyncMock(return_value=stub),
    ):
        response = await client.post("/api/v1/analyze", json=_VALID_PAYLOAD)

    assert response.status_code == 200
    data = response.json()["data"]
    vr = data["verification_report"]
    assert vr["verified"] is False
    assert vr["status"] == "failed"
    assert vr["failed_tests"] == 1
    assert len(vr["regressions"]) == 1
    assert len(vr["remaining_risks"]) == 1
    # Overall analysis status is still "completed"
    assert data["status"] == "completed"


# ─── 8. Invalid input returns 422 ────────────────────────────────────────────

@pytest.mark.asyncio
async def test_invalid_input_returns_422(client: AsyncClient):
    """
    Blank / whitespace-only code must be rejected with HTTP 422 by Pydantic
    validation before any agent is called.
    """
    payload = {"code": "   \n\t  ", "language": "python"}
    response = await client.post("/api/v1/analyze", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_missing_code_field_returns_422(client: AsyncClient):
    """Missing required 'code' field must yield HTTP 422."""
    response = await client.post("/api/v1/analyze", json={"language": "python"})
    assert response.status_code == 422


# ─── 9. Health endpoint still works ──────────────────────────────────────────

@pytest.mark.asyncio
async def test_health_endpoint_still_works(client: AsyncClient):
    """GET /api/v1/health must return 200 with status=healthy."""
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


# ─── 10. History endpoint still works ────────────────────────────────────────

@pytest.mark.asyncio
async def test_history_endpoint_still_works(client: AsyncClient):
    """
    GET /api/v1/history must return 200 with a list payload.
    We first persist at least one record by running an analysis.
    """
    stub = _make_orchestrator_result()
    with patch(
        "app.services.ai_agent.CodeTrustOrchestrator.run",
        new=AsyncMock(return_value=stub),
    ):
        await client.post("/api/v1/analyze", json=_VALID_PAYLOAD)

    response = await client.get("/api/v1/history?limit=10")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert isinstance(body["data"], list)


# ─── Live integration smoke test (no stub) ───────────────────────────────────

@pytest.mark.asyncio
async def test_live_orchestrator_end_to_end(client: AsyncClient):
    """
    End-to-end smoke test that exercises the real CodeTrust Orchestrator
    (no mocks).  Verifies the full pipeline produces a coherent response.
    """
    payload = {
        "code": "def calculate_total(prices):\n    total = 0\n    for p in prices:\n        total += p\n    return total",
        "language": "python",
        "file_name": "calc.py",
        "generate_test_cases": True,
    }
    response = await client.post("/api/v1/analyze", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    data = body["data"]
    assert "session_id" in data
    assert data["language"] == "python"
    assert data["status"] == "completed"
    assert data["analysis_time_ms"] >= 0
    assert isinstance(data["bugs"], list)
    assert len(data["bugs"]) >= 1
    assert isinstance(data["test_cases"], list)
    assert len(data["test_cases"]) >= 1
    # Verification report must be present and complete
    vr = data["verification_report"]
    assert vr is not None
    assert "verified" in vr
    assert "status" in vr
    assert "confidence" in vr
    assert "passed_tests" in vr
    assert "failed_tests" in vr
    assert "regressions" in vr
    assert "remaining_risks" in vr
    assert "evidence" in vr
