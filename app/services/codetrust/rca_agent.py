"""
RCA Agent — Root Cause Analysis

Analyses source code and a bug description to identify the root cause(s)
of reported issues. Returns a structured RCAResult.
"""
import uuid
import re
from typing import List
from app.core.logging import logger
from .models import RCAResult


class RCAAgent:
    """
    Performs root cause analysis on the supplied source code.

    In production this should be backed by an LLM or static analysis tool.
    The current implementation uses heuristic pattern detection which is
    sufficient for local development, CI, and the test suite.
    """

    # Severity mapping: pattern → (title, severity, description, suggested_fix)
    _PYTHON_PATTERNS = [
        (
            r"\beval\s*\(",
            "critical",
            "Use of dangerous eval() — arbitrary code execution risk",
            "Replace eval() with ast.literal_eval() or an explicit parser",
        ),
        (
            r"except\s*:",
            "medium",
            "Bare except clause swallows all exceptions including SystemExit",
            "Specify a concrete exception class, e.g. except Exception as e:",
        ),
        (
            r"exec\s*\(",
            "critical",
            "Use of exec() allows arbitrary code execution",
            "Avoid exec(); use explicit function calls instead",
        ),
        (
            r"import\s+\*",
            "low",
            "Wildcard import pollutes the namespace and hides dependencies",
            "Import only the names you need explicitly",
        ),
        (
            r"\bopen\s*\([^)]*\)",
            "low",
            "File opened without a context manager; resource leak possible",
            "Use 'with open(...) as f:' to ensure the file is closed",
        ),
    ]

    _JAVASCRIPT_PATTERNS = [
        (
            r"\beval\s*\(",
            "critical",
            "Use of eval() introduces code injection vulnerabilities",
            "Remove eval(); use JSON.parse() or structured data instead",
        ),
        (
            r"==(?!=)",
            "low",
            "Loose equality (==) can cause unexpected type coercion",
            "Use strict equality (===) throughout",
        ),
    ]

    _LANGUAGE_PATTERNS = {
        "python": _PYTHON_PATTERNS,
        "javascript": _JAVASCRIPT_PATTERNS,
        "typescript": _JAVASCRIPT_PATTERNS,
    }

    def analyse(self, source_code: str, language: str, bug_description: str) -> RCAResult:
        """
        Analyse *source_code* and return an RCAResult.

        :param source_code:     The code under analysis.
        :param language:        Programming language string (e.g. "python").
        :param bug_description: Free-text description of the bug / error logs.
        """
        logger.info(f"[RCAAgent] Starting analysis for language={language}")

        lines = source_code.splitlines()
        patterns = self._LANGUAGE_PATTERNS.get(language.lower(), [])

        root_causes: List[str] = []
        affected_lines: List[int] = []
        highest_severity = "low"
        severity_rank = {"low": 0, "medium": 1, "high": 2, "critical": 3}

        for regex, severity, description, _ in patterns:
            for i, line in enumerate(lines, start=1):
                if re.search(regex, line):
                    root_causes.append(f"Line {i}: {description}")
                    affected_lines.append(i)
                    if severity_rank.get(severity, 0) > severity_rank.get(highest_severity, 0):
                        highest_severity = severity

        # Incorporate the bug description as additional context
        if bug_description and bug_description.strip():
            root_causes.append(f"User-reported issue: {bug_description.strip()}")

        if not root_causes:
            root_causes = [
                "No critical patterns detected via static analysis. "
                "Manual review recommended for logic errors."
            ]

        confidence = min(0.5 + 0.1 * len([rc for rc in root_causes if "Line" in rc]), 0.95)

        summary = (
            f"RCA completed: {len([rc for rc in root_causes if 'Line' in rc])} pattern(s) found "
            f"in {language} code. Highest severity: {highest_severity}."
        )

        logger.info(f"[RCAAgent] {summary}")
        return RCAResult(
            summary=summary,
            root_causes=root_causes,
            affected_lines=sorted(set(affected_lines)),
            severity=highest_severity,
            confidence=round(confidence, 2),
        )
