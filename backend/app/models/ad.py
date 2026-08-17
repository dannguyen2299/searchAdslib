from datetime import datetime, date

from sqlalchemy import JSON, Date, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Ad(Base):
    __tablename__ = "ads"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ad_id: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    page_id: Mapped[str | None] = mapped_column(String, index=True, nullable=True)
    page_name: Mapped[str | None] = mapped_column(String, nullable=True)
    body: Mapped[str | None] = mapped_column(String, nullable=True)
    headline: Mapped[str | None] = mapped_column(String, nullable=True)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str | None] = mapped_column(String, nullable=True)
    platforms: Mapped[list | None] = mapped_column(JSON, nullable=True)
    creative_url: Mapped[str | None] = mapped_column(String, nullable=True)
    landing_url: Mapped[str | None] = mapped_column(String, nullable=True)
    ad_library_url: Mapped[str | None] = mapped_column(String, nullable=True)
    raw_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    keyword: Mapped[str | None] = mapped_column(String, index=True, nullable=True)
    fetched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
