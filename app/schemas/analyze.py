from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator




class SupportedLanguage(str, Enum):
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    CPP = "cpp"
    C = "c"


class BugSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AnalyzeRequest(BaseModel):
    code: str = Field(..., min_length=1, description="Source code to analyze")
    language: SupportedLanguage = Field(
        default=SupportedLanguage.PYTHON,
        description="Programming language of the source code"
    )
    file_name: Optional[str] = Field(None, max_length=255, description="Optional name of the file")
    context_description: Optional[str] = Field(
        None, max_length=1000, description="Optional context or error logs provided by user"
    )
    generate_test_cases: bool = Field(
        default=True, description="Whether the AI agent should generate automated test cases"
    )

    @field_validator("code")
    @classmethod
    def validate_code_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Source code cannot be empty or only whitespace")
        return v


class BugReport(BaseModel):
    bug_id: str
    title: str
    severity: BugSeverity
    line_number: Optional[int] = None
    description: str
    root_cause: str
    suggested_fix: str
    fixed_code_snippet: Optional[str] = None


class TestCase(BaseModel):
    test_id: str
    name: str
    description: Optional[str] = None
    test_code: str
    expected_output: Optional[str] = None
    test_type: str = "unit"  # e.g., 'unit', 'edge_case', 'regression'


class VerificationReport(BaseModel):
    """
    Carries the Verification Agent's quality-gate outcome.
    This is an optional enrichment on top of the existing API contract.
    """
    verified: bool = Field(..., description="True if the fix passed all quality gates")
    status: str = Field(..., description="verified | partial | failed")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Verification confidence score (0–1)")
    passed_tests: int = Field(..., ge=0, description="Number of tests that passed")
    failed_tests: int = Field(..., ge=0, description="Number of tests that failed")
    regressions: List[str] = Field(default_factory=list, description="List of detected regressions")
    remaining_risks: List[str] = Field(default_factory=list, description="Outstanding risk descriptions")
    evidence: List[str] = Field(default_factory=list, description="Supporting evidence from the pipeline")


class AnalyzeResponseData(BaseModel):
    session_id: str
    language: SupportedLanguage
    summary: str
    total_bugs_detected: int
    bugs: List[BugReport]
    fixed_code: Optional[str] = None
    test_cases: List[TestCase] = []
    analysis_time_ms: float
    status: str = "completed"
    verification_report: Optional[VerificationReport] = Field(
        default=None,
        description="Verification Agent result — present when the CodeTrust Orchestrator is used"
    )
