from __future__ import annotations

import enum
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Computed,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.clients import Client


class ThicknessBand(str, enum.Enum):
    lt10 = "<10mm"
    t12 = "12mm"
    gt12_19 = ">12-19mm"
    t20 = "20mm"
    gt20_40 = ">20-40mm"
    gt40_63 = ">40-63mm"
    t80 = "80mm"


THICKNESS_BAND_ORDER = [
    ThicknessBand.lt10,
    ThicknessBand.t12,
    ThicknessBand.gt12_19,
    ThicknessBand.t20,
    ThicknessBand.gt20_40,
    ThicknessBand.gt40_63,
    ThicknessBand.t80,
]


class NormLibrary(Base):
    __tablename__ = "norm_libraries"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), nullable=False)
    label: Mapped[str] = mapped_column(String(100), nullable=False)
    effective_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_draft: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    client: Mapped[Client] = relationship(back_populates="norm_libraries")
    rm_price_bands: Mapped[list[RmPriceBand]] = relationship(back_populates="library", cascade="all, delete-orphan")
    scrap_rates: Mapped[list[ScrapRate]] = relationship(back_populates="library", cascade="all, delete-orphan")
    process_rates: Mapped[list[ProcessRate]] = relationship(back_populates="library", cascade="all, delete-orphan")
    overhead_params: Mapped[list[CostOverheadParam]] = relationship(back_populates="library", cascade="all, delete-orphan")
    steel_price_buildups: Mapped[list[SteelPriceBuildUp]] = relationship(back_populates="library", cascade="all, delete-orphan")
    grade_equivalences: Mapped[list[GradeEquivalence]] = relationship(back_populates="library", cascade="all, delete-orphan")
    section_catalog_items: Mapped[list[SectionCatalogItem]] = relationship(back_populates="library", cascade="all, delete-orphan")
    bo_catalog_items: Mapped[list[BoughtOutCatalogItem]] = relationship(back_populates="library", cascade="all, delete-orphan")


class MaterialGrade(Base):
    __tablename__ = "material_grades"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    base_grade_id: Mapped[int | None] = mapped_column(ForeignKey("material_grades.id"), nullable=True)
    premium_amount: Mapped[float | None] = mapped_column(Numeric(12, 4), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    base_grade: Mapped[MaterialGrade | None] = relationship("MaterialGrade", remote_side="MaterialGrade.id", foreign_keys=[base_grade_id])
    rm_price_bands: Mapped[list[RmPriceBand]] = relationship(back_populates="grade")


class RmPriceBand(Base):
    __tablename__ = "rm_price_bands"

    id: Mapped[int] = mapped_column(primary_key=True)
    norm_library_id: Mapped[int] = mapped_column(ForeignKey("norm_libraries.id"), nullable=False)
    grade_id: Mapped[int] = mapped_column(ForeignKey("material_grades.id"), nullable=False)
    thickness_band: Mapped[str] = mapped_column(
        String(20),
        CheckConstraint(
            "thickness_band IN ('<10mm','12mm','>12-19mm','20mm','>20-40mm','>40-63mm','80mm')",
            name="ck_rm_price_bands_thickness_band",
        ),
        nullable=False,
    )
    price_per_kg: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    library: Mapped[NormLibrary] = relationship(back_populates="rm_price_bands")
    grade: Mapped[MaterialGrade] = relationship(back_populates="rm_price_bands")


class ScrapRate(Base):
    __tablename__ = "scrap_rates"

    id: Mapped[int] = mapped_column(primary_key=True)
    norm_library_id: Mapped[int] = mapped_column(ForeignKey("norm_libraries.id"), nullable=False, unique=True)
    rate_per_kg: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    library: Mapped[NormLibrary] = relationship(back_populates="scrap_rates")


class ProcessRate(Base):
    __tablename__ = "process_rates"

    id: Mapped[int] = mapped_column(primary_key=True)
    norm_library_id: Mapped[int] = mapped_column(ForeignKey("norm_libraries.id"), nullable=False)
    operation_name: Mapped[str] = mapped_column(String(200), nullable=False)
    unit: Mapped[str] = mapped_column(
        Enum(
            "Rs/Kg", "Rs/Hr", "Rs/mm/meter", "Rs/slant/meter", "Rs/Nos", "Rs/Sqm", "%",
            name="process_unit",
        ),
        nullable=False,
    )
    rate: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    group_label: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    library: Mapped[NormLibrary] = relationship(back_populates="process_rates")


class CostOverheadParam(Base):
    __tablename__ = "cost_overhead_params"

    id: Mapped[int] = mapped_column(primary_key=True)
    norm_library_id: Mapped[int] = mapped_column(ForeignKey("norm_libraries.id"), nullable=False)
    applies_to: Mapped[str] = mapped_column(
        Enum("raw_material", "bought_out", "process_cost", name="applies_to_enum"),
        nullable=False,
    )
    param_name: Mapped[str] = mapped_column(String(100), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    param_value: Mapped[float | None] = mapped_column(Numeric(8, 4), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    library: Mapped[NormLibrary] = relationship(back_populates="overhead_params")


class SteelPriceBuildUp(Base):
    """Basic price/tonne + extras (UST, trimming, normalising, trader/transport constant) -> Rs/kg."""
    __tablename__ = "steel_price_buildups"

    id: Mapped[int] = mapped_column(primary_key=True)
    norm_library_id: Mapped[int] = mapped_column(ForeignKey("norm_libraries.id"), nullable=False)
    grade_id: Mapped[int] = mapped_column(ForeignKey("material_grades.id"), nullable=False)
    thickness_band: Mapped[str] = mapped_column(
        String(20),
        CheckConstraint(
            "thickness_band IN ('<10mm','12mm','>12-19mm','20mm','>20-40mm','>40-63mm','80mm')",
            name="ck_steel_price_buildups_thickness_band",
        ),
        nullable=False,
    )
    basic_price_per_tonne: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False, default=0)
    ust_amount: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False, default=0)
    trimming_amount: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False, default=0)
    normalising_amount: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False, default=0)
    trader_transport_constant: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False, default=0)
    price_per_kg: Mapped[float] = mapped_column(
        Numeric(12, 4),
        Computed(
            "(basic_price_per_tonne + ust_amount + trimming_amount + normalising_amount + trader_transport_constant) / 1000",
            persisted=True,
        ),
    )
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    library: Mapped[NormLibrary] = relationship(back_populates="steel_price_buildups")
    grade: Mapped[MaterialGrade] = relationship()


class GradeEquivalence(Base):
    """Maps a customer spec (e.g. S235J2) to our Indian-equivalent material grade."""
    __tablename__ = "grade_equivalences"

    id: Mapped[int] = mapped_column(primary_key=True)
    norm_library_id: Mapped[int] = mapped_column(ForeignKey("norm_libraries.id"), nullable=False)
    customer_spec: Mapped[str] = mapped_column(String(100), nullable=False)
    material_grade_id: Mapped[int] = mapped_column(ForeignKey("material_grades.id"), nullable=False)
    notes: Mapped[str | None] = mapped_column(String(300), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    library: Mapped[NormLibrary] = relationship(back_populates="grade_equivalences")
    material_grade: Mapped[MaterialGrade] = relationship()


class SectionCatalogItem(Base):
    """Channels, angles, round/square/flat bars, pipes — kg/m and rate."""
    __tablename__ = "section_catalog_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    norm_library_id: Mapped[int] = mapped_column(ForeignKey("norm_libraries.id"), nullable=False)
    category: Mapped[str] = mapped_column(
        String(20),
        CheckConstraint(
            "category IN ('channel','angle','round_bar','square_bar','flat_bar','pipe')",
            name="ck_section_catalog_category",
        ),
        nullable=False,
    )
    designation: Mapped[str] = mapped_column(String(100), nullable=False)
    kg_per_m: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False, default=0)
    rate_per_kg: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False, default=0)
    rate_per_m: Mapped[float] = mapped_column(Numeric(14, 4), Computed("kg_per_m * rate_per_kg", persisted=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    library: Mapped[NormLibrary] = relationship(back_populates="section_catalog_items")


class BoughtOutCatalogItem(Base):
    """Reusable bought-out item master: nuts, bolts, washers, bushes, etc."""
    __tablename__ = "bo_catalog_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    norm_library_id: Mapped[int] = mapped_column(ForeignKey("norm_libraries.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    unit_weight_kg: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    rate: Mapped[float] = mapped_column(Numeric(14, 4), nullable=False, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    library: Mapped[NormLibrary] = relationship(back_populates="bo_catalog_items")
