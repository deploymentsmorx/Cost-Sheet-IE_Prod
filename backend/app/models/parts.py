from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Computed, Date, DateTime, ForeignKey, Integer, JSON, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.clients import Client


class CostWorkbook(Base):
    __tablename__ = "cost_workbooks"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    sets_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    client: Mapped[Client] = relationship(back_populates="cost_workbooks")
    cost_sheets: Mapped[list[CostSheet]] = relationship(back_populates="workbook", cascade="all, delete-orphan")


class CostSheet(Base):
    """One costed item (part) within a workbook — merges the old Part + CostingSheet."""
    __tablename__ = "cost_sheets"

    id: Mapped[int] = mapped_column(primary_key=True)
    workbook_id: Mapped[int] = mapped_column(ForeignKey("cost_workbooks.id"), nullable=False)
    # Part identity fields
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    part_no: Mapped[str | None] = mapped_column(String(100), nullable=True)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    drawing_no: Mapped[str | None] = mapped_column(String(100), nullable=True)
    benchmark_price: Mapped[Decimal | None] = mapped_column(Numeric(14, 4), nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    qty_per_set: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False, server_default="1")
    is_optional: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    status: Mapped[str | None] = mapped_column(String(100), nullable=True)
    remarks: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    first_supply_price: Mapped[Decimal | None] = mapped_column(Numeric(14, 4), nullable=True)
    first_supply_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    first_supply_rm_reference: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    # Costing fields
    supply_version: Mapped[str] = mapped_column(String(100), nullable=False, server_default="V1")
    discount_pct: Mapped[Decimal] = mapped_column(Numeric(8, 4), nullable=False, server_default="0")
    transport_cost: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False, server_default="0")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    workbook: Mapped[CostWorkbook] = relationship(back_populates="cost_sheets")
    lines: Mapped[list[CostingLine]] = relationship(
        back_populates="sheet", cascade="all, delete-orphan", order_by="CostingLine.sl_no"
    )
    bo_items: Mapped[list[BOLineItem]] = relationship(
        back_populates="sheet", cascade="all, delete-orphan", order_by="BOLineItem.sl_no"
    )
    finishing_ops: Mapped[list[SheetFinishingOp]] = relationship(
        back_populates="sheet", cascade="all, delete-orphan"
    )
    saved_result: Mapped[CostSheetResult | None] = relationship(
        back_populates="sheet", uselist=False, cascade="all, delete-orphan"
    )
    price_history: Mapped[list[PriceHistoryEntry]] = relationship(
        back_populates="sheet", cascade="all, delete-orphan", order_by="PriceHistoryEntry.change_no"
    )


class CostingLine(Base):
    __tablename__ = "costing_lines"

    id: Mapped[int] = mapped_column(primary_key=True)
    cost_sheet_id: Mapped[int] = mapped_column(ForeignKey("cost_sheets.id"), nullable=False)
    sl_no: Mapped[int] = mapped_column(Integer, nullable=False)
    parent_line_id: Mapped[int | None] = mapped_column(ForeignKey("costing_lines.id"), nullable=True)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    spec: Mapped[str | None] = mapped_column(String(200), nullable=True)
    grade_id: Mapped[int | None] = mapped_column(ForeignKey("material_grades.id"), nullable=True)
    thickness_band: Mapped[str | None] = mapped_column(String(20), nullable=True)
    thickness_mm: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    qty: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False, server_default="1")
    part_weight: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False, server_default="0")
    efficiency_pct: Mapped[Decimal] = mapped_column(Numeric(8, 4), nullable=False, server_default="100")

    sheet: Mapped[CostSheet] = relationship(back_populates="lines")
    parent: Mapped[CostingLine | None] = relationship(
        "CostingLine", remote_side="CostingLine.id", foreign_keys=[parent_line_id]
    )
    operations: Mapped[list[LineOperation]] = relationship(
        back_populates="line", cascade="all, delete-orphan"
    )
    saved_result: Mapped[CostingResult | None] = relationship(
        back_populates="line", uselist=False, cascade="all, delete-orphan"
    )
    process_cost_row: Mapped[ProcessCostRow | None] = relationship(
        back_populates="line", uselist=False, cascade="all, delete-orphan"
    )


class CostingResult(Base):
    """Per-line RM chain snapshot."""
    __tablename__ = "costing_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    costing_line_id: Mapped[int] = mapped_column(ForeignKey("costing_lines.id"), unique=True, nullable=False)
    norm_library_id: Mapped[int] = mapped_column(ForeignKey("norm_libraries.id"), nullable=False)
    calculated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    total_part_weight: Mapped[Decimal | None] = mapped_column(Numeric(14, 6), nullable=True)
    blank_weight: Mapped[Decimal | None] = mapped_column(Numeric(14, 6), nullable=True)
    total_blank_weight: Mapped[Decimal | None] = mapped_column(Numeric(14, 6), nullable=True)
    blank_rate: Mapped[Decimal | None] = mapped_column(Numeric(14, 6), nullable=True)
    blank_cost: Mapped[Decimal | None] = mapped_column(Numeric(14, 4), nullable=True)
    process_loss_pct: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), nullable=True)
    process_loss_weight: Mapped[Decimal | None] = mapped_column(Numeric(14, 6), nullable=True)
    scrap_weight: Mapped[Decimal | None] = mapped_column(Numeric(14, 6), nullable=True)
    scrap_cost: Mapped[Decimal | None] = mapped_column(Numeric(14, 4), nullable=True)
    rm_cost: Mapped[Decimal | None] = mapped_column(Numeric(14, 4), nullable=True)
    line_process_cost: Mapped[Decimal | None] = mapped_column(Numeric(14, 4), nullable=True)

    line: Mapped[CostingLine] = relationship(back_populates="saved_result")


class BOLineItem(Base):
    __tablename__ = "bo_line_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    cost_sheet_id: Mapped[int] = mapped_column(ForeignKey("cost_sheets.id"), nullable=False)
    sl_no: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    qty: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False, server_default="1")
    unit_price: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False, server_default="0")
    bo_line_cost: Mapped[Decimal] = mapped_column(
        Numeric(14, 4), Computed("qty * unit_price", persisted=True)
    )
    catalog_item_id: Mapped[int | None] = mapped_column(ForeignKey("bo_catalog_items.id"), nullable=True)
    unit_weight_kg: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)

    sheet: Mapped[CostSheet] = relationship(back_populates="bo_items")


class LineOperation(Base):
    __tablename__ = "costing_line_operations"

    id: Mapped[int] = mapped_column(primary_key=True)
    costing_line_id: Mapped[int] = mapped_column(ForeignKey("costing_lines.id"), nullable=False)
    operation_type: Mapped[str] = mapped_column(String(50), nullable=False)
    input_data: Mapped[dict] = mapped_column(JSON, nullable=False, server_default="{}")
    operation_cost: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False, server_default="0")

    line: Mapped[CostingLine] = relationship(back_populates="operations")


class SheetFinishingOp(Base):
    __tablename__ = "sheet_finishing_ops"

    id: Mapped[int] = mapped_column(primary_key=True)
    cost_sheet_id: Mapped[int] = mapped_column(ForeignKey("cost_sheets.id"), nullable=False)
    operation_name: Mapped[str] = mapped_column(String(100), nullable=False)
    input_qty: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False, server_default="0")
    computed_cost: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False, server_default="0")

    sheet: Mapped[CostSheet] = relationship(back_populates="finishing_ops")


class CostSheetResult(Base):
    """Sheet-level aggregated result — one row per cost_sheet."""
    __tablename__ = "cost_sheet_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    cost_sheet_id: Mapped[int] = mapped_column(ForeignKey("cost_sheets.id"), unique=True, nullable=False)
    norm_library_id: Mapped[int] = mapped_column(ForeignKey("norm_libraries.id"), nullable=False)
    calculated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    # RM block
    total_rm_cost: Mapped[Decimal | None] = mapped_column(Numeric(14, 4), nullable=True)
    overhead_rm: Mapped[Decimal | None] = mapped_column(Numeric(14, 4), nullable=True)
    rework_rm: Mapped[Decimal | None] = mapped_column(Numeric(14, 4), nullable=True)
    inventory_rm: Mapped[Decimal | None] = mapped_column(Numeric(14, 4), nullable=True)
    profit_rm: Mapped[Decimal | None] = mapped_column(Numeric(14, 4), nullable=True)
    rm_grand_total: Mapped[Decimal | None] = mapped_column(Numeric(14, 4), nullable=True)

    # BO block
    total_bo_cost: Mapped[Decimal | None] = mapped_column(Numeric(14, 4), nullable=True)
    overhead_bo: Mapped[Decimal | None] = mapped_column(Numeric(14, 4), nullable=True)
    inventory_bo: Mapped[Decimal | None] = mapped_column(Numeric(14, 4), nullable=True)
    profit_bo: Mapped[Decimal | None] = mapped_column(Numeric(14, 4), nullable=True)
    bo_grand_total: Mapped[Decimal | None] = mapped_column(Numeric(14, 4), nullable=True)

    # Process block
    total_process_cost: Mapped[Decimal | None] = mapped_column(Numeric(14, 4), nullable=True)
    overhead_proc: Mapped[Decimal | None] = mapped_column(Numeric(14, 4), nullable=True)
    rework_proc: Mapped[Decimal | None] = mapped_column(Numeric(14, 4), nullable=True)
    profit_proc: Mapped[Decimal | None] = mapped_column(Numeric(14, 4), nullable=True)
    process_grand_total: Mapped[Decimal | None] = mapped_column(Numeric(14, 4), nullable=True)

    # Final roll-up
    unit_price: Mapped[Decimal | None] = mapped_column(Numeric(14, 4), nullable=True)
    transport_cost_snap: Mapped[Decimal | None] = mapped_column(Numeric(14, 4), nullable=True)
    discount_pct_snap: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), nullable=True)
    price_after_discount: Mapped[Decimal | None] = mapped_column(Numeric(14, 4), nullable=True)
    pct_change_vs_previous: Mapped[Decimal | None] = mapped_column(Numeric(10, 6), nullable=True)
    bal_margin: Mapped[Decimal | None] = mapped_column(Numeric(14, 4), nullable=True)
    bal_margin_per_kg: Mapped[Decimal | None] = mapped_column(Numeric(14, 4), nullable=True)
    total_part_weight: Mapped[Decimal | None] = mapped_column(Numeric(14, 6), nullable=True)

    sheet: Mapped[CostSheet] = relationship(back_populates="saved_result")


class ProcessCostRow(Base):
    __tablename__ = "process_cost_rows"

    id: Mapped[int] = mapped_column(primary_key=True)
    costing_line_id: Mapped[int] = mapped_column(ForeignKey("costing_lines.id"), unique=True, nullable=False)
    equi_spec: Mapped[str | None] = mapped_column(String(200), nullable=True)
    thk: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    unit_cut_length: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)
    use_laser: Mapped[bool] = mapped_column(nullable=False, server_default="false")
    machining_rate: Mapped[Decimal | None] = mapped_column(Numeric(14, 4), nullable=True)
    bev_slant: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), nullable=True)
    bev_length: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)
    bend_num_bends: Mapped[int | None] = mapped_column(Integer, nullable=True)
    drill_size: Mapped[str | None] = mapped_column(String(50), nullable=True)
    drill_hours: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)
    drill_type: Mapped[str] = mapped_column(String(20), nullable=False, server_default="regular")
    has_rolling: Mapped[bool] = mapped_column(nullable=False, server_default="false")

    line: Mapped[CostingLine] = relationship(back_populates="process_cost_row")


class PriceHistoryEntry(Base):
    """One row per recorded price change for a cost sheet — 'Change 1, 2, ...' log."""
    __tablename__ = "price_history_entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    cost_sheet_id: Mapped[int] = mapped_column(ForeignKey("cost_sheets.id"), nullable=False)
    change_no: Mapped[int] = mapped_column(Integer, nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    rm_reference_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    discount_pct: Mapped[Decimal] = mapped_column(Numeric(8, 4), nullable=False, server_default="0")
    pct_change_vs_last_supplied: Mapped[Decimal | None] = mapped_column(Numeric(10, 6), nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    sheet: Mapped[CostSheet] = relationship(back_populates="price_history")
