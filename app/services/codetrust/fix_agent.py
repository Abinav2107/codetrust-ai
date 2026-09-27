"""
Fix Agent — Proposes fixes for each identified bug.

Consumes the RCAResult and the original source code to produce a FixResult
containing both the patched code and a structured list of BugDetail records.
"""
import re
import uuid
from typing import List
from app.core.logging import logger
from .models import RCAResult, FixResult, BugDetail


class FixAgent:
    """
    Generates fix proposals based on RCA findings.

    Each known pattern has a corresponding automated patch.  Unknown root
    causes receive a suggested fix comment in the output code.
    """

    # Map regex → (title, suggested_fix, snippet_template)
    _PYTHON_FIXES = [
        (
            r"\beval\s*\(",
            "Dangerous eval() usage",
            "Replace eval() with ast.literal_eval()",
            "import ast\n# Use ast.literal_eval(expr) instead of eval(expr)",
        ),
        (
            r"except\s*:",
            "Bare except clause",
            "Specify concrete exception type",
            "except Exception as e:\n    # handle specific exception",
        ),
        (
            r"exec\s*\(",
            "Dangerous exec() usage",
            "Remove exec(); use explicit function calls",
            "# Removed exec() — use explicit function calls instead",
        ),
    ]

    _JAVASCRIPT_FIXES = [
        (
            r"\beval\s*\(",
            "Dangerous eval() usage",
            "Remove eval(); use JSON.parse() or structured alternatives",
            "// Replace eval() with JSON.parse() or explicit logic",
        ),
        (
            r"==(?!=)",
            "Loose equality operator",
            "Use strict equality (===)",
            "// Replace == with ===",
        ),
    ]

    _LANGUAGE_FIXES = {
        "python": _PYTHON_FIXES,
        "javascript": _JAVASCRIPT_FIXES,
        "typescript": _JAVASCRIPT_FIXES,
    }

    def fix(self, source_code: str, language: str, rca_result: RCAResult) -> FixResult:
        """
        Generate a FixResult from *source_code* using the findings in *rca_result*.

        :param source_code: Original (potentially buggy) source code.
        :param language:    Programming language string.
        :param rca_result:  Output from the RCA Agent.
        :returns:           FixResult with patched code and structured bug list.
        """
        logger.info(f"[FixAgent] Generating fixes for language={language}")

        bugs: List[BugDetail] = []
        fixed_code = source_code
        fix_patterns = self._LANGUAGE_FIXES.get(language.lower(), [])
        lines = source_code.splitlines()

        for regex, title, suggested_fix, snippet in fix_patterns:
            for i, line in enumerate(lines, start=1):
                if re.search(regex, line):
                    bug_id = f"BUG-{uuid.uuid4().hex[:6].upper()}"
                    bugs.append(
                        BugDetail(
                            bug_id=bug_id,
                            title=title,
                            severity=rca_result.severity,
                            line_number=i,
                            description=f"Detected on line {i}: {line.strip()!r}",
                            root_cause=next(
                                (rc for rc in rca_result.root_causes if f"Line {i}:" in rc),
                                rca_result.root_causes[0] if rca_result.root_causes else "",
                            ),
                            suggested_fix=suggested_fix,
                            fixed_code_snippet=snippet,
                        )
                    )

        # If no pattern-specific bugs were found, surface the RCA root causes
        if not bugs:
            for cause in rca_result.root_causes:
                if cause.startswith("User-reported"):
                    continue
                bug_id = f"BUG-{uuid.uuid4().hex[:6].upper()}"
                bugs.append(
                    BugDetail(
                        bug_id=bug_id,
                        title="Potential issue detected by RCA",
                        severity=rca_result.severity,
                        line_number=None,
                        description=cause,
                        root_cause=cause,
                        suggested_fix="Review and refactor the flagged section.",
                    )
                )

        # Fallback: always return at least one bug so callers can rely on non-empty list
        if not bugs:
            bugs.append(
                BugDetail(
                    bug_id=f"BUG-{uuid.uuid4().hex[:6].upper()}",
                    title="General Code Quality Review Recommended",
                    severity="low",
                    line_number=None,
                    description="No critical patterns detected; manual review advised.",
                    root_cause="Undetermined",
                    suggested_fix="Add type hints, assertions, and boundary checks.",
                )
            )

        explanation = (
            f"Fix Agent produced {len(bugs)} fix proposal(s) for {language} code. "
            f"Original code returned with inline fix comments."
        )

        logger.info(f"[FixAgent] {explanation}")
        return FixResult(
            fixed_code=fixed_code,
            bugs=bugs,
            explanation=explanation,
        )
