from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
import datetime

from app.core.security import verify_api_key
from app.db.models import AnalysisRecord
from app.db.session import get_db
from app.schemas.common import APIResponse

router = APIRouter()


class HistoryItem(BaseModel):
    session_id: str
    language: str
    file_name: str | None
    code_snippet: str
    total_bugs_detected: int
    summary: str | None
    created_at: datetime.datetime


@router.get(
    "/history",
    response_model=APIResponse[List[HistoryItem]],
    tags=["Analysis History"],
    summary="Get recent code analysis history",
)
async def get_history(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key),
):
    stmt = (
        select(AnalysisRecord)
        .order_by(desc(AnalysisRecord.created_at))
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(stmt)
    records = result.scalars().all()

    items = [
        HistoryItem(
            session_id=r.session_id,
            language=r.language,
            file_name=r.file_name,
            code_snippet=r.code_snippet,
            total_bugs_detected=r.total_bugs_detected,
            summary=r.summary,
            created_at=r.created_at,
        )
        for r in records
    ]

    return APIResponse(
        success=True,
        message=f"Retrieved {len(items)} record(s)",
        data=items,
    )
