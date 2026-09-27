from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.logging import logger
from app.core.security import limiter, verify_api_key
from app.db.models import AnalysisRecord
from app.db.session import get_db
from app.schemas.analyze import AnalyzeRequest, AnalyzeResponseData
from app.schemas.common import APIResponse
from app.services.ai_agent import ai_agent_service
from app.services.sanitizer import CodeSanitizer

router = APIRouter()


@router.post(
    "/analyze",
    response_model=APIResponse[AnalyzeResponseData],
    status_code=status.HTTP_200_OK,
    tags=["Analysis & Debugging"],
    summary="Submit source code for AI-driven bug detection and test generation",
)
@limiter.limit(settings.RATE_LIMIT_ANALYZE)
async def analyze_code_endpoint(
    request: Request,
    payload: AnalyzeRequest,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key),
):
    """
    Core backend workflow:
    1. Validate source code payload & size limit
    2. Route to AI Agent service (Abinav's service with fallback)
    3. Generate root cause, fix suggestions, and test cases
    4. Store history record asynchronously
    5. Return structured JSON
    """
    logger.info(f"Received code analysis request: lang={payload.language}, file={payload.file_name}")

    # Step 6: Validate code size & safety
    CodeSanitizer.validate_code_safety(payload.code, payload.language)

    # Step 7-11: Call AI Agent service
    analysis_data = await ai_agent_service.analyze_code(payload)

    # Step 14: Save record to database history
    try:
        record = AnalysisRecord(
            session_id=analysis_data.session_id,
            language=payload.language.value,
            file_name=payload.file_name,
            code_snippet=payload.code[:500],  # Save snippet for reference
            total_bugs_detected=analysis_data.total_bugs_detected,
            summary=analysis_data.summary,
            status=analysis_data.status,
        )
        db.add(record)
        await db.commit()
    except Exception as db_err:
        logger.warning(f"Could not persist history record: {db_err}")
        # Analysis should still succeed even if DB logging is unavailable

    return APIResponse(
        success=True,
        message="Code analyzed successfully",
        data=analysis_data,
    )
