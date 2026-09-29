"""
Tests for direct integration of codetrust_ai agent package into backend AIAgentService.
"""
import pytest
from unittest.mock import MagicMock, patch

from app.schemas.analyze import AnalyzeRequest, SupportedLanguage
from app.services.ai_agent import AIAgentService
from codetrust_ai.agent.models import (
    BugDetail,
    FixChange,
    FixResponse,
    GeneratedTest,
    OrchestratorResult as RealOrchestratorResult,
    RCAResponse,
    TestExecutionResult,
    TestGenResponse,
    VerificationResponse,
)


@pytest.mark.asyncio
async def test_direct_codetrust_ai_orchestrator_integration(monkeypatch):
    """Verify that AIAgentService directly delegates to codetrust_ai Orchestrator when MOCK_AI_AGENT=False."""
    # Ensure OPENAI_API_KEY is recognized or pass injected orchestrator
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key-12345")
    mock_real = MagicMock()
    service = AIAgentService(real_orchestrator=mock_real)
    assert service._real_orchestrator is not None, "Real CodeTrust AI orchestrator must be loaded"

    stub_rca = RCAResponse(
        summary="Found 1 critical bug: zero division.",
        root_cause="Denominator can be zero.",
        bugs=[
            BugDetail(
                bug_id=1,
                title="Zero Division",
                description="List length can be zero",
                severity="critical",
                affected_lines=[5],
                suggestion="Add empty check guard",
            )
        ],
        affected_lines=[5],
        confidence=0.98,
    )

    stub_fix = FixResponse(
        summary="Added guard clause for empty collection.",
        fixed_code="def avg(l):\n    if not l: return 0.0\n    return sum(l)/len(l)\n",
        changes=[
            FixChange(
                bug_id=1,
                affected_lines=[5],
                original_behavior="raises ZeroDivisionError",
                new_behavior="returns 0.0",
                explanation="Guard clause handles empty list",
            )
        ],
        assumptions=[],
        confidence=0.95,
    )

    stub_tests = TestGenResponse(
        summary="Generated 2 adversarial test cases.",
        tests=[
            GeneratedTest(
                test_id=1,
                description="Test empty list input",
                category="original_bug",
                test_code="assert avg([]) == 0.0",
                expected_behavior="Return 0.0",
                risk_level="high",
            ),
            GeneratedTest(
                test_id=2,
                description="Test regular list input",
                category="regression",
                test_code="assert avg([10, 20]) == 15.0",
                expected_behavior="Return 15.0",
                risk_level="medium",
            ),
        ],
        total_tests=2,
        confidence=0.92,
    )

    stub_exec = [
        TestExecutionResult(test_id=1, status="passed", output="OK"),
        TestExecutionResult(test_id=2, status="passed", output="OK"),
    ]

    stub_verification = VerificationResponse(
        verification_status="verified",
        summary="All tests passed successfully with zero regressions.",
        confidence=0.96,
        passed_tests=[1, 2],
        failed_tests=[],
        errored_tests=[],
        regressions=[],
        remaining_risks=[],
        evidence=["Executed 2 tests: 2 passed, 0 failed."],
        explanation="The proposed fix properly resolves the bug without breaking existing behavior.",
    )

    real_result = RealOrchestratorResult(
        workflow_status="completed",
        failed_stage=None,
        error=None,
        rca_response=stub_rca,
        fix_response=stub_fix,
        test_gen_response=stub_tests,
        execution_results=stub_exec,
        verification_response=stub_verification,
    )

    # Patch the real orchestrator.run method and set MOCK_AI_AGENT to False
    with patch.object(service._real_orchestrator, "run", return_value=real_result):
        with patch("app.services.ai_agent.settings.MOCK_AI_AGENT", False):
            req = AnalyzeRequest(
                code="def avg(l):\n    return sum(l)/len(l)\n",
                language=SupportedLanguage.PYTHON,
                file_name="calc.py",
                context_description="ZeroDivisionError on empty list",
            )
            response_data = await service.analyze_code(req)

    assert response_data.status == "completed"
    assert response_data.total_bugs_detected == 1
    assert response_data.bugs[0].bug_id == "BUG-001"
    assert response_data.bugs[0].title == "Zero Division"
    assert response_data.bugs[0].severity.value == "critical"
    assert response_data.bugs[0].fixed_code_snippet == "returns 0.0"

    assert len(response_data.test_cases) == 2
    assert response_data.test_cases[0].test_id == "TEST-001"
    assert response_data.test_cases[0].test_type == "original_bug"

    assert response_data.verification_report is not None
    assert response_data.verification_report.verified is True
    assert response_data.verification_report.status == "verified"
    assert response_data.verification_report.passed_tests == 2
    assert response_data.verification_report.failed_tests == 0
    assert response_data.analysis_time_ms >= 0
