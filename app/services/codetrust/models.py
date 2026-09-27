"""
Shared data models for the CodeTrust agent pipeline.
All agents communicate through these typed structures.
"""
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class RCAResult:
    """Root Cause Analysis result produced by the RCA Agent."""
    summary: str
    root_causes: List[str] = field(default_factory=list)
    affected_lines: List[int] = field(default_factory=list)
    severity: str = "medium"  # low | medium | high | critical
    confidence: float = 0.0   # 0.0 – 1.0


@dataclass
class BugDetail:
    """Single bug identified during RCA, consumed by the Fix Agent."""
    bug_id: str
    title: str
    severity: str
    line_number: Optional[int]
    description: str
    root_cause: str
    suggested_fix: str
    fixed_code_snippet: Optional[str] = None


@dataclass
class FixResult:
    """Fix proposal produced by the Fix Agent."""
    fixed_code: str
    bugs: List[BugDetail] = field(default_factory=list)
    explanation: str = ""


@dataclass
class GeneratedTest:
    """A single generated test case from the Test Agent."""
    test_id: str
    name: str
    description: Optional[str]
    test_code: str
    expected_output: Optional[str]
    test_type: str = "unit"


@dataclass
class TestAgentResult:
    """Collection of generated tests produced by the Test Agent."""
    tests: List[GeneratedTest] = field(default_factory=list)


@dataclass
class TestRunResult:
    """Outcome of executing the generated tests via the Test Runner."""
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    total: int = 0
    execution_output: str = ""
    test_details: List[dict] = field(default_factory=list)

    @property
    def all_passed(self) -> bool:
        return self.failed == 0 and self.total > 0


@dataclass
class VerificationResult:
    """Outcome of the Verification Agent — summarises the overall quality gate."""
    verified: bool
    confidence: float          # 0.0 – 1.0
    passed_tests: int
    failed_tests: int
    regressions: List[str] = field(default_factory=list)
    remaining_risks: List[str] = field(default_factory=list)
    evidence: List[str] = field(default_factory=list)
    status: str = "verified"   # verified | not_verified | failed | inconclusive | invalid | partial


@dataclass
class OrchestratorResult:
    """
    Top-level result returned by the CodeTrust Orchestrator.
    Carries the output of every pipeline stage.
    """
    session_id: str
    language: str
    rca: RCAResult
    fix: FixResult
    tests: TestAgentResult
    test_run: TestRunResult
    verification: VerificationResult
    analysis_time_ms: float = 0.0
