"""
Verification Agent

Evaluates the overall quality gate by examining:
  - test execution results (pass/fail/regression)
  - RCA severity
  - Fix proposals

Hard rules (applied in priority order — first match wins):
  1. invalid      — duplicate or unknown test IDs
  2. inconclusive — empty results (no tests generated or run)
  3. inconclusive — incomplete execution (total_run < total_generated)
  4. not_verified — any original-bug (regression) test failed
  5. not_verified — any unit test failed
  6. failed       — any high-risk or adversarial test failed
  7. verified     — all rules passed

Returns a VerificationResult with a verified flag, confidence score,
passed/failed test counts, regressions, remaining risks, and evidence.
"""
from app.core.logging import logger
from .models import RCAResult, FixResult, TestAgentResult, TestRunResult, VerificationResult


class VerificationAgent:
    """
    Final gate in the CodeTrust pipeline.

    Applies evidence-based hard rules before any statistical confidence
    adjustment.  A single failed hard rule overrides all other signals.
    """

    # Test-type labels that represent the original-bug verification tests
    _REGRESSION_TYPES = {"regression"}

    # Test-type labels that represent adversarial / high-risk coverage
    _HIGH_RISK_TYPES = {"adversarial", "high_risk", "security"}

    def verify(
        self,
        rca_result: RCAResult,
        fix_result: FixResult,
        test_agent_result: TestAgentResult,
        test_run_result: TestRunResult,
    ) -> VerificationResult:
        """
        Evaluate the full pipeline output and produce a VerificationResult.

        :param rca_result:         Output of the RCA Agent.
        :param fix_result:         Output of the Fix Agent.
        :param test_agent_result:  Output of the Test Agent.
        :param test_run_result:    Output of the Test Runner.
        :returns:                  VerificationResult indicating status.
        """
        logger.info("[VerificationAgent] Starting verification.")

        regressions: list[str] = []
        remaining_risks: list[str] = []
        evidence: list[str] = []

        # ── Collect baseline evidence ─────────────────────────────────────────
        total_generated = len(test_agent_result.tests)
        total_run = test_run_result.total

        evidence.append(
            f"Test execution: {test_run_result.passed} passed, "
            f"{test_run_result.failed} failed, "
            f"{test_run_result.skipped} skipped "
            f"(total run: {total_run}, total generated: {total_generated})."
        )
        evidence.append(
            f"RCA severity: {rca_result.severity}. "
            f"RCA confidence: {rca_result.confidence}."
        )
        evidence.append(
            f"Fix Agent produced {len(fix_result.bugs)} fix proposal(s)."
        )

        # ── Build per-type failure sets from test_details ─────────────────────
        # test_details entries: {"test_id": str, "name": str, "status": str, ...}
        # Fall back to aggregate counts when details are unavailable.
        details = test_run_result.test_details  # may be empty

        # Index generated tests by ID for duplicate / unknown detection
        generated_ids: dict[str, int] = {}
        for t in test_agent_result.tests:
            generated_ids[t.test_id] = generated_ids.get(t.test_id, 0) + 1

        # Gather IDs reported by the runner
        reported_ids = [d.get("test_id", "") for d in details if d.get("test_id")]

        # ── HARD RULE 1: duplicate or unknown test IDs → invalid ──────────────
        duplicate_ids = [tid for tid, cnt in generated_ids.items() if cnt > 1]
        unknown_ids = [tid for tid in reported_ids if tid not in generated_ids]

        if duplicate_ids or unknown_ids:
            msg_parts = []
            if duplicate_ids:
                msg_parts.append(f"duplicate test IDs: {duplicate_ids}")
            if unknown_ids:
                msg_parts.append(f"unknown test IDs in runner output: {unknown_ids}")
            reason = "; ".join(msg_parts)
            evidence.append(f"INVALID: {reason}.")
            logger.warning(f"[VerificationAgent] invalid — {reason}")
            return VerificationResult(
                verified=False,
                confidence=0.0,
                passed_tests=test_run_result.passed,
                failed_tests=test_run_result.failed,
                regressions=[reason],
                remaining_risks=["Test suite integrity compromised — manual review required."],
                evidence=evidence,
                status="invalid",
            )

        # ── HARD RULE 2: no tests generated or run → inconclusive ─────────────
        if total_generated == 0 or total_run == 0:
            reason = (
                "No tests were generated." if total_generated == 0
                else "No tests were executed."
            )
            evidence.append(f"INCONCLUSIVE: {reason}")
            remaining_risks.append(f"{reason} Manual verification required.")
            logger.warning(f"[VerificationAgent] inconclusive — {reason}")
            return VerificationResult(
                verified=False,
                confidence=0.1,
                passed_tests=0,
                failed_tests=0,
                regressions=[],
                remaining_risks=remaining_risks,
                evidence=evidence,
                status="inconclusive",
            )

        # ── HARD RULE 3: incomplete execution → inconclusive ──────────────────
        # Skipped tests count as not executed for the purpose of completeness.
        executed = test_run_result.passed + test_run_result.failed
        if executed < total_generated:
            reason = (
                f"Only {executed} of {total_generated} generated test(s) were executed "
                f"({test_run_result.skipped} skipped)."
            )
            evidence.append(f"INCONCLUSIVE: {reason}")
            remaining_risks.append(reason + " Manual verification required.")
            logger.warning(f"[VerificationAgent] inconclusive — {reason}")
            return VerificationResult(
                verified=False,
                confidence=0.2,
                passed_tests=test_run_result.passed,
                failed_tests=test_run_result.failed,
                regressions=[],
                remaining_risks=remaining_risks,
                evidence=evidence,
                status="inconclusive",
            )

        # ── Classify per-type failures (requires test_details) ────────────────
        regression_failures: list[str] = []
        high_risk_failures: list[str] = []
        unit_failures: list[str] = []

        if details:
            # Build a map from test_id → test_type for generated tests
            type_map: dict[str, str] = {t.test_id: t.test_type for t in test_agent_result.tests}
            for d in details:
                if d.get("status") not in ("failed", "error"):
                    continue
                tid = d.get("test_id", "")
                ttype = type_map.get(tid, "unit")
                name = d.get("name", tid)
                if ttype in self._HIGH_RISK_TYPES:
                    high_risk_failures.append(name)
                elif ttype in self._REGRESSION_TYPES:
                    regression_failures.append(name)
                else:
                    unit_failures.append(name)
        else:
            # No per-test detail — classify all failures as unit failures
            # (conservative: can't promote to regression/high-risk without evidence)
            if test_run_result.failed > 0:
                unit_failures = [f"{test_run_result.failed} test(s) failed (no detail available)"]

        # ── HARD RULE 4: any regression (original-bug) test failed ────────────
        if regression_failures:
            for name in regression_failures:
                regressions.append(
                    f"Original-bug regression test FAILED: '{name}' — fix is not verified."
                )
            evidence.append(
                f"NOT VERIFIED: {len(regression_failures)} regression test(s) failed: "
                f"{regression_failures}."
            )
            logger.warning(
                f"[VerificationAgent] not_verified — regression test(s) failed: {regression_failures}"
            )
            return VerificationResult(
                verified=False,
                confidence=0.05,
                passed_tests=test_run_result.passed,
                failed_tests=test_run_result.failed,
                regressions=regressions,
                remaining_risks=[
                    "The fix did not resolve the original bug — do not merge."
                ],
                evidence=evidence,
                status="not_verified",
            )

        # ── HARD RULE 5: any unit test failed ─────────────────────────────────
        if unit_failures:
            for name in unit_failures:
                regressions.append(f"Test FAILED: '{name}'.")
            evidence.append(
                f"NOT VERIFIED: {len(unit_failures)} unit test(s) failed: {unit_failures}."
            )
            logger.warning(
                f"[VerificationAgent] not_verified — unit test(s) failed: {unit_failures}"
            )
            return VerificationResult(
                verified=False,
                confidence=0.1,
                passed_tests=test_run_result.passed,
                failed_tests=test_run_result.failed,
                regressions=regressions,
                remaining_risks=["One or more tests failed — investigate before merging."],
                evidence=evidence,
                status="not_verified",
            )

        # ── HARD RULE 6: any high-risk / adversarial test failed ──────────────
        if high_risk_failures:
            for name in high_risk_failures:
                regressions.append(
                    f"High-risk/adversarial test FAILED: '{name}'."
                )
            evidence.append(
                f"FAILED: {len(high_risk_failures)} high-risk/adversarial test(s) failed: "
                f"{high_risk_failures}."
            )
            remaining_risks.append(
                "Security or adversarial test failed — fix is unsafe to merge."
            )
            logger.warning(
                f"[VerificationAgent] failed — high-risk test(s) failed: {high_risk_failures}"
            )
            return VerificationResult(
                verified=False,
                confidence=0.05,
                passed_tests=test_run_result.passed,
                failed_tests=test_run_result.failed,
                regressions=regressions,
                remaining_risks=remaining_risks,
                evidence=evidence,
                status="failed",
            )

        # ── All hard rules passed — compute confidence and verify ─────────────
        # Base: 0.5, +0.3 if all tests pass, −0.05 per unaddressed risk
        for cause in rca_result.root_causes:
            if "User-reported" in cause:
                continue
            addressed = any(
                b.root_cause and cause[:40] in b.root_cause
                for b in fix_result.bugs
            )
            if not addressed:
                remaining_risks.append(f"Unaddressed: {cause[:120]}")

        confidence = 0.5
        if test_run_result.all_passed:
            confidence += 0.3
        confidence -= 0.05 * len(remaining_risks)

        if rca_result.severity in ("critical", "high"):
            confidence -= 0.1
            if remaining_risks:
                remaining_risks.append(
                    f"High/critical severity issue: {rca_result.severity}."
                )

        confidence = max(0.05, min(0.99, confidence))
        verified = test_run_result.all_passed and len(remaining_risks) == 0

        status = "verified" if verified else "partial"

        logger.info(
            f"[VerificationAgent] Result: verified={verified}, "
            f"confidence={confidence:.2f}, status={status}"
        )

        return VerificationResult(
            verified=verified,
            confidence=round(confidence, 2),
            passed_tests=test_run_result.passed,
            failed_tests=test_run_result.failed,
            regressions=regressions,
            remaining_risks=remaining_risks,
            evidence=evidence,
            status=status,
        )
