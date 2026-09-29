import asyncio
import time
import uuid
from typing import Optional

from app.core.config import settings
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

# Direct integration with real CodeTrust AI agent pipeline
try:
    from codetrust_ai.agent.orchestrator import Orchestrator as RealCodeTrustOrchestrator
    from codetrust_ai.agent.models import OrchestratorResult as RealOrchestratorResult
    _REAL_CODETRUST_AVAILABLE = True
except ImportError:
    _REAL_CODETRUST_AVAILABLE = False
    RealCodeTrustOrchestrator = None  # type: ignore[assignment, misc]
    RealOrchestratorResult = None    # type: ignore[assignment, misc]


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


def _map_real_orchestrator_result_to_response(
    result: "RealOrchestratorResult",
    request: AnalyzeRequest,
    session_id: str,
    elapsed_ms: float,
) -> AnalyzeResponseData:
    """
    Convert a real CodeTrust AI OrchestratorResult (from the codetrust_ai package)
    into the AnalyzeResponseData schema for frontend and API consumers.
    """
    bugs: list[BugReport] = []
    if result.rca_response and result.rca_response.bugs:
        # Build lookup for fixed snippets from FixResponse changes
        snippet_by_bug: dict[int, str] = {}
        if result.fix_response and result.fix_response.changes:
            for ch in result.fix_response.changes:
                snippet_by_bug[ch.bug_id] = ch.new_behavior

        for b in result.rca_response.bugs:
            bugs.append(
                BugReport(
                    bug_id=f"BUG-{b.bug_id:03d}",
                    title=b.title,
                    severity=_map_severity(b.severity),
                    line_number=b.affected_lines[0] if b.affected_lines else None,
                    description=b.description,
                    root_cause=result.rca_response.root_cause,
                    suggested_fix=b.suggestion,
                    fixed_code_snippet=snippet_by_bug.get(b.bug_id),
                )
            )

    test_cases: list[TestCase] = []
    if result.test_gen_response and result.test_gen_response.tests:
        for t in result.test_gen_response.tests:
            test_cases.append(
                TestCase(
                    test_id=f"TEST-{t.test_id:03d}",
                    name=f"test_{t.category}_{t.test_id}",
                    description=t.description,
                    test_code=t.test_code,
                    expected_output=t.expected_behavior,
                    test_type=t.category,
                )
            )

    vr: Optional[VerificationReport] = None
    if result.verification_response:
        v = result.verification_response
        vr = VerificationReport(
            verified=(v.verification_status == "verified"),
            status=v.verification_status,
            confidence=v.confidence,
            passed_tests=len(v.passed_tests),
            failed_tests=len(v.failed_tests) + len(v.errored_tests),
            regressions=[f"TEST-{tid:03d}" for tid in v.regressions],
            remaining_risks=v.remaining_risks,
            evidence=v.evidence,
        )

    if result.verification_response:
        summary = (
            f"CodeTrust AI analysis completed. "
            f"Detected {len(bugs)} bug(s), generated {len(test_cases)} test(s). "
            f"Verification: {result.verification_response.verification_status} "
            f"(confidence: {result.verification_response.confidence:.0%})."
        )
    elif result.rca_response:
        summary = result.rca_response.summary
    elif result.error:
        summary = f"CodeTrust AI stage '{result.failed_stage}' failed: {result.error}"
    else:
        summary = "CodeTrust AI analysis completed."

    fixed_code = (
        result.fix_response.fixed_code
        if (result.fix_response and result.fix_response.fixed_code)
        else request.code
    )

    return AnalyzeResponseData(
        session_id=session_id,
        language=request.language,
        summary=summary,
        total_bugs_detected=len(bugs),
        bugs=bugs,
        fixed_code=fixed_code,
        test_cases=test_cases,
        analysis_time_ms=elapsed_ms,
        status="completed" if result.workflow_status == "completed" else "failed",
        verification_report=vr,
    )


class AIAgentService:
    def __init__(
        self,
        mock_orchestrator: Optional[CodeTrustOrchestrator] = None,
        real_orchestrator: Optional[RealCodeTrustOrchestrator] = None,
    ):
        self._orchestrator = mock_orchestrator or CodeTrustOrchestrator()
        self._real_orchestrator: Optional[RealCodeTrustOrchestrator] = real_orchestrator

        if self._real_orchestrator is None and _REAL_CODETRUST_AVAILABLE and RealCodeTrustOrchestrator is not None:
            try:
                self._real_orchestrator = RealCodeTrustOrchestrator()
                logger.info("[AIAgentService] Connected directly to real CodeTrust AI Orchestrator package.")
            except Exception as init_err:
                logger.warning(
                    f"[AIAgentService] Real CodeTrust AI Orchestrator init deferred: {init_err}"
                )

    async def analyze_code(self, request: AnalyzeRequest) -> AnalyzeResponseData:
        """
        Delegates to CodeTrust AI Orchestrator:
        - When MOCK_AI_AGENT is False and real CodeTrust AI is loaded, runs the real multi-agent pipeline.
        - Otherwise, falls back to the deterministic local mock/heuristic engine.
        """
        session_id = str(uuid.uuid4())
        start = time.perf_counter()

        use_real = (not settings.MOCK_AI_AGENT) and (self._real_orchestrator is not None)
        if use_real:
            logger.info(
                f"[AIAgentService] Running real CodeTrust AI Orchestrator — "
                f"session={session_id}, lang={request.language.value}"
            )
            try:
                real_result = await asyncio.to_thread(
                    self._real_orchestrator.run,
                    source_code=request.code,
                    language=request.language.value,
                    bug_description=request.context_description or "Analyze and fix code bugs",
                    file_name=request.file_name or "code",
                )
                elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
                return _map_real_orchestrator_result_to_response(
                    real_result, request, session_id, elapsed_ms
                )
            except Exception as e:
                logger.error(
                    f"[AIAgentService] Real CodeTrust AI Orchestrator error: {e}. "
                    f"Falling back to local heuristic orchestrator."
                )

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
