"""
CodeTrust Orchestrator

Entry point for the full CodeTrust pipeline:

    1. RCA Agent         — root cause analysis
    2. Fix Agent         — fix proposals
    3. Test Agent        — test generation
    4. Test Runner       — test execution
    5. Verification Agent — quality gate

Usage::

    from app.services.codetrust import CodeTrustOrchestrator, OrchestratorResult

    orchestrator = CodeTrustOrchestrator()
    result: OrchestratorResult = await orchestrator.run(
        source_code=...,
        language=...,
        bug_description=...,
        file_name=...,
        session_id=...,
    )
"""
import time
import uuid
from app.core.logging import logger
from .models import OrchestratorResult
from .rca_agent import RCAAgent
from .fix_agent import FixAgent
from .test_agent import TestAgent
from .test_runner import MultiLanguageTestRunner
from .verification_agent import VerificationAgent


class CodeTrustOrchestrator:
    """
    Coordinates the full CodeTrust analysis pipeline.

    Each stage is invoked in sequence; the output of each stage is passed
    as input to the next.  All work is performed within this service process —
    there are no external HTTP calls.
    """

    def __init__(self):
        self._rca = RCAAgent()
        self._fix = FixAgent()
        self._test = TestAgent()
        self._runner = MultiLanguageTestRunner()
        self._verifier = VerificationAgent()

    async def run(
        self,
        source_code: str,
        language: str,
        bug_description: str,
        file_name: str = "unknown",
        session_id: str | None = None,
    ) -> OrchestratorResult:
        """
        Execute the full analysis pipeline and return an OrchestratorResult.

        :param source_code:     The source code to analyse.
        :param language:        Programming language string (e.g. "python").
        :param bug_description: User-supplied bug description / error logs.
        :param file_name:       Original file name (informational).
        :param session_id:      Optional session ID; one is generated if omitted.
        :returns:               OrchestratorResult with all pipeline outputs.
        """
        if session_id is None:
            session_id = str(uuid.uuid4())

        start = time.perf_counter()
        logger.info(
            f"[Orchestrator] Starting pipeline: session={session_id}, "
            f"language={language}, file={file_name}"
        )

        # ── Stage 1: Root Cause Analysis ─────────────────────────────────────
        rca_result = self._rca.analyse(
            source_code=source_code,
            language=language,
            bug_description=bug_description,
        )
        logger.info(f"[Orchestrator] Stage 1 complete — RCA: {rca_result.summary}")

        # ── Stage 2: Fix Agent ────────────────────────────────────────────────
        fix_result = self._fix.fix(
            source_code=source_code,
            language=language,
            rca_result=rca_result,
        )
        logger.info(f"[Orchestrator] Stage 2 complete — Fix: {fix_result.explanation}")

        # ── Stage 3: Test Agent ───────────────────────────────────────────────
        test_agent_result = self._test.generate(
            fixed_code=fix_result.fixed_code,
            language=language,
            fix_result=fix_result,
        )
        logger.info(f"[Orchestrator] Stage 3 complete — Tests: {len(test_agent_result.tests)} generated")

        # ── Stage 4: Test Runner ──────────────────────────────────────────────
        test_run_result = await self._runner.run(
            test_result=test_agent_result,
            language=language,
        )
        logger.info(
            f"[Orchestrator] Stage 4 complete — Runner: "
            f"{test_run_result.passed} passed, {test_run_result.failed} failed"
        )

        # ── Stage 5: Verification Agent ───────────────────────────────────────
        verification_result = self._verifier.verify(
            rca_result=rca_result,
            fix_result=fix_result,
            test_agent_result=test_agent_result,
            test_run_result=test_run_result,
        )
        logger.info(
            f"[Orchestrator] Stage 5 complete — Verification: "
            f"verified={verification_result.verified}, status={verification_result.status}"
        )

        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
        logger.info(f"[Orchestrator] Pipeline finished in {elapsed_ms} ms for session={session_id}")

        return OrchestratorResult(
            session_id=session_id,
            language=language,
            rca=rca_result,
            fix=fix_result,
            tests=test_agent_result,
            test_run=test_run_result,
            verification=verification_result,
            analysis_time_ms=elapsed_ms,
        )
