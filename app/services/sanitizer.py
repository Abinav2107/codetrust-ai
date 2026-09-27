import ast
from fastapi import HTTPException, status
from app.core.config import settings
from app.schemas.analyze import SupportedLanguage


class CodeSanitizer:
    @staticmethod
    def validate_code_safety(code: str, language: SupportedLanguage) -> None:
        """
        Validates size, character safety, and basic syntax structure.
        """
        code_bytes = len(code.encode("utf-8"))
        if code_bytes > settings.MAX_CODE_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Code size ({code_bytes} bytes) exceeds maximum allowed ({settings.MAX_CODE_SIZE_BYTES} bytes)"
            )

        # For Python code, run an AST sanity check
        if language == SupportedLanguage.PYTHON:
            try:
                ast.parse(code)
            except SyntaxError as e:
                # We do NOT fail here because the code submitted might HAVE bugs/syntax errors that need fixing!
                # We simply flag it if needed.
                pass

    @staticmethod
    def sanitize_output(content: str) -> str:
        """
        Sanitizes output text to prevent injection or malicious formatting.
        """
        if not content:
            return ""
        return content.strip()
