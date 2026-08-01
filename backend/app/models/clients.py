from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.norms import NormLibrary
    from app.models.parts import CostWorkbook


class Client(Base):
    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    norm_libraries: Mapped[list[NormLibrary]] = relationship(back_populates="client", cascade="all, delete-orphan")
    cost_workbooks: Mapped[list[CostWorkbook]] = relationship(back_populates="client", cascade="all, delete-orphan")
