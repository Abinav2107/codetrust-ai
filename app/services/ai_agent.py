import time
import uuid
from app.core.logging import logger
from app.schemas.analyze import (
    AnalyzeRequest,
    AnalyzeResponseData,
    BugReport,
    BugSeverity,
    TestCase,
    VerificationReport,
)
from app.services.codetrust import CodeTrustOrchestrator, OrchestratorResult


def _map_severity(severity: str) -> BugSeverity:
    """Map a CodeTrust severity string to the BugSeverity enum."""
    mapping = {
        "critical": BugSeverity.CRITICAL,
        "high": BugSeverity.HIGH,
        "medium": BugSeverity.MEDIUM,
        "low": BugSeverity.LOW,
    }
    return mapping.get(severity.lower(), BugSeverity.LOW)


def _orchestrator_result_to_response(
    result: OrchestratorResult,
    request: AnalyzeRequest,
) -> AnalyzeResponseData:
    """
    Convert a CodeTrust OrchestratorResult into the existing AnalyzeResponseData
    contract that the API layer and frontend expect.
    """
    # ── Bugs ──────────────────────────────────────────────────────────────────
    bugs = [
        BugReport(
            bug_id=b.bug_id,
            title=b.title,
            severity=_map_severity(b.severity),
            line_number=b.line_number,
            description=b.description,
            root_cause=b.root_cause,
            suggested_fix=b.suggested_fix,
            fixed_code_snippet=b.fixed_code_snippet,
        )
        for b in result.fix.bugs
    ]

    # ── Test cases ────────────────────────────────────────────────────────────
    test_cases = [
        TestCase(
            test_id=t.test_id,
            name=t.name,
            description=t.description,
            test_code=t.test_code,
            expected_output=t.expected_output,
            test_type=t.test_type,
        )
        for t in result.tests.tests
    ]

    # ── Verification report ───────────────────────────────────────────────────
    v = result.verification
    verification_report = VerificationReport(
        verified=v.verified,
        status=v.status,
        confidence=v.confidence,
        passed_tests=v.passed_tests,
        failed_tests=v.failed_tests,
        regressions=v.regressions,
        remaining_risks=v.remaining_risks,
        evidence=v.evidence,
    )

    # ── Summary ───────────────────────────────────────────────────────────────
    summary = (
        f"CodeTrust analysis completed. "
        f"Detected {len(bugs)} issue(s), generated {len(test_cases)} test(s). "
        f"Verification: {v.status} (confidence: {v.confidence:.0%})."
    )

    return AnalyzeResponseData(
        session_id=result.session_id,
        language=request.language,
        summary=summary,
        total_bugs_detected=len(bugs),
        bugs=bugs,
        fixed_code=result.fix.fixed_code or request.code,
        test_cases=test_cases,
        analysis_time_ms=result.analysis_time_ms,
        status="completed",
        verification_report=verification_report,
    )


class AIAgentService:
    def __init__(self):
        self._orchestrator = CodeTrustOrchestrator()

    async def analyze_code(self, request: AnalyzeRequest) -> AnalyzeResponseData:
        """
        Delegates to the CodeTrust Orchestrator which runs the full pipeline:
        RCA Agent → Fix Agent → Test Agent → Test Runner → Verification Agent.
        """
        session_id = str(uuid.uuid4())
        logger.info(
            f"[AIAgentService] Delegating to CodeTrust Orchestrator — "
            f"session={session_id}, lang={request.language.value}"
        )

        result: OrchestratorResult = await self._orchestrator.run(
            source_code=request.code,
            language=request.language.value,
            bug_description=request.context_description or "",
            file_name=request.file_name or "unknown",
            session_id=session_id,
        )

        return _orchestrator_result_to_response(result, request)


ai_agent_service = AIAgentService()
