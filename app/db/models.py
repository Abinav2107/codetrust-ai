import datetime
from sqlalchemy import Column, DateTime, Integer, String, Text
from app.db.session import Base


class AnalysisRecord(Base):
    __tablename__ = "analysis_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(String(64), unique=True, index=True, nullable=False)
    language = Column(String(32), nullable=False)
    file_name = Column(String(255), nullable=True)
    code_snippet = Column(Text, nullable=False)
    total_bugs_detected = Column(Integer, default=0)
    summary = Column(Text, nullable=True)
    status = Column(String(32), default="completed")
    created_at = Column(
        DateTime,
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        nullable=False,
    )
