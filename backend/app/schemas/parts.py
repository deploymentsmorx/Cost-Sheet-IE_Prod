from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict


# ---------------------------------------------------------------------------
# Cost Workbooks
# ---------------------------------------------------------------------------

class WorkbookCreate(BaseModel):
    name: str
    client_id: int
    description: str | None = None


class WorkbookUpdate(BaseModel):
    name: str | None = None
    client_id: int | None = None
    description: str | None = None


class WorkbookOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    client_id: int
    client_name: str | None = None
    description: str | None
    created_at: datetime
    sheet_count: int = 0


# ---------------------------------------------------------------------------
# Cost Sheets (merged Part + CostingSheet)
# ---------------------------------------------------------------------------

class CostSheetCreate(BaseModel):
    name: str
    part_no: str | None = None
    description: str | None = None
    drawing_no: str | None = None
    benchmark_price: Decimal | None = None
    supply_version: str = "V1"
    discount_pct: Decimal = Decimal("0")
    transport_cost: Decimal = Decimal("0")


class CostSheetUpdate(BaseModel):
    name: str | None = None
    part_no: str | None = None
    description: str | None = None
    drawing_no: str | None = None
    benchmark_price: Decimal | None = None
    supply_version: str | None = None
    discount_pct: Decimal | None = None
    transport_cost: Decimal | None = None


# ---------------------------------------------------------------------------
# BO Line Items
# ---------------------------------------------------------------------------

class BOLineItemCreate(BaseModel):
    sl_no: int | None = None
    description: str | None = None
    qty: Decimal = Decimal("1")
    unit_price: Decimal = Decimal("0")


class BOLineItemUpdate(BaseModel):
    sl_no: int | None = None
    description: str | None = None
    qty: Decimal | None = None
    unit_price: Decimal | None = None


class BOLineItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    cost_sheet_id: int
    sl_no: int
    description: str | None
    qty: Decimal
    unit_price: Decimal
    bo_line_cost: Decimal


# ---------------------------------------------------------------------------
# Costing Line Operations
# ---------------------------------------------------------------------------

class LineOperationCreate(BaseModel):
    operation_type: str
    input_data: dict[str, Any] = {}


class LineOperationUpdate(BaseModel):
    operation_type: str | None = None
    input_data: dict[str, Any] | None = None


class LineOperationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    costing_line_id: int
    operation_type: str
    input_data: dict[str, Any]
    operation_cost: Decimal


# ---------------------------------------------------------------------------
# Sheet Finishing Ops
# ---------------------------------------------------------------------------

class SheetFinishingOpCreate(BaseModel):
    operation_name: str
    input_qty: Decimal = Decimal("0")


class SheetFinishingOpUpdate(BaseModel):
    input_qty: Decimal | None = None


class SheetFinishingOpOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    cost_sheet_id: int
    operation_name: str
    input_qty: Decimal
    computed_cost: Decimal


# ---------------------------------------------------------------------------
# Costing Lines
# ---------------------------------------------------------------------------

class CostingLineCreate(BaseModel):
    sl_no: int | None = None
    description: str | None = None
    spec: str | None = None
    grade_id: int | None = None
    thickness_band: str | None = None
    thickness_mm: Decimal | None = None
    qty: Decimal = Decimal("1")
    part_weight: Decimal = Decimal("0")
    efficiency_pct: Decimal = Decimal("100")


class CostingLineUpdate(BaseModel):
    description: str | None = None
    spec: str | None = None
    grade_id: int | None = None
    thickness_band: str | None = None
    thickness_mm: Decimal | None = None
    qty: Decimal | None = None
    part_weight: Decimal | None = None
    efficiency_pct: Decimal | None = None


class RmLineResultOut(BaseModel):
    """Per-line RM chain result."""
    part_weight: Decimal
    total_part_weight: Decimal
    blank_weight: Decimal
    total_blank_weight: Decimal
    blank_rate: Decimal
    blank_cost: Decimal
    process_loss_pct: Decimal
    process_loss_weight: Decimal
    scrap_weight: Decimal
    scrap_cost: Decimal
    rm_cost: Decimal
    norm_library_id: int


class CostingLineOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    cost_sheet_id: int
    sl_no: int
    description: str | None
    spec: str | None
    grade_id: int | None
    thickness_band: str | None
    thickness_mm: Decimal | None
    qty: Decimal
    part_weight: Decimal
    efficiency_pct: Decimal
    operations: list[LineOperationOut] = []
    rm_result: RmLineResultOut | None = None
    line_process_cost: Decimal | None = None
    saved_at: datetime | None = None


# ---------------------------------------------------------------------------
# Sheet-level result
# ---------------------------------------------------------------------------

class BlockMarkupOut(BaseModel):
    base_total: Decimal
    overhead: Decimal
    rework: Decimal
    inventory: Decimal
    profit: Decimal
    grand_total: Decimal


class SheetCalcResultOut(BaseModel):
    line_process_costs: list[Decimal] = []
    total_rm_cost: Decimal
    total_bo_cost: Decimal
    total_process_cost: Decimal
    total_finishing_cost: Decimal
    rm_block: BlockMarkupOut
    bo_block: BlockMarkupOut
    process_block: BlockMarkupOut
    unit_price: Decimal
    transport_cost: Decimal
    discount_pct: Decimal
    price_after_discount: Decimal
    bal_margin: Decimal
    bal_margin_per_kg: Decimal
    total_part_weight: Decimal
    norm_library_id: int


# ---------------------------------------------------------------------------
# Process Cost Rows
# ---------------------------------------------------------------------------

class ProcessCostRowUpdate(BaseModel):
    equi_spec: str | None = None
    thk: Decimal | None = None
    unit_cut_length: Decimal | None = None
    use_laser: bool | None = None
    machining_rate: Decimal | None = None
    bev_slant: Decimal | None = None
    bev_length: Decimal | None = None
    bend_num_bends: int | None = None
    drill_size: str | None = None
    drill_hours: Decimal | None = None
    drill_type: str | None = None
    has_rolling: bool | None = None


class ProcessCostRowOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    costing_line_id: int
    equi_spec: str | None
    thk: Decimal | None
    unit_cut_length: Decimal | None
    use_laser: bool
    machining_rate: Decimal | None
    bev_slant: Decimal | None
    bev_length: Decimal | None
    bend_num_bends: int | None
    drill_size: str | None
    drill_hours: Decimal | None
    drill_type: str
    has_rolling: bool
    cutting_cost: Decimal = Decimal("0")
    machining_cost: Decimal = Decimal("0")
    bevelling_cost: Decimal = Decimal("0")
    bending_rate: Decimal = Decimal("0")
    bending_cost: Decimal = Decimal("0")
    drilling_rate: Decimal = Decimal("0")
    drilling_cost: Decimal = Decimal("0")
    rolling_rate: Decimal = Decimal("0")
    rolling_cost: Decimal = Decimal("0")
    row_total: Decimal = Decimal("0")
    total_wt: Decimal = Decimal("0")


class CostSheetWithLines(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    workbook_id: int
    name: str
    part_no: str | None = None
    description: str | None = None
    drawing_no: str | None = None
    benchmark_price: Decimal | None = None
    client_id: int | None = None
    supply_version: str
    discount_pct: Decimal
    transport_cost: Decimal
    created_at: datetime
    lines: list[CostingLineOut] = []
    bo_items: list[BOLineItemOut] = []
    finishing_ops: list[SheetFinishingOpOut] = []
    process_rows: list[ProcessCostRowOut] = []
    sheet_result: SheetCalcResultOut | None = None


# ---------------------------------------------------------------------------
# Workbook summary
# ---------------------------------------------------------------------------

class CostSheetSummary(BaseModel):
    sheet_id: int
    name: str
    part_no: str | None
    supply_version: str
    total_price: Decimal | None
    rm_cost: Decimal | None
    bo_grand_total: Decimal | None = None
    process_grand_total: Decimal | None = None
    bal_margin: Decimal | None = None
    total_weight: Decimal | None
    discount_pct: Decimal | None
    pct_change_vs_previous: Decimal | None
    saved_at: datetime | None
    line_count: int
    saved_count: int


class WorkbookSummaryOut(BaseModel):
    id: int
    name: str
    client_id: int
    client_name: str | None = None
    cost_sheets: list[CostSheetSummary]


# ---------------------------------------------------------------------------
# Legacy — kept so /calculate endpoint compiles
# ---------------------------------------------------------------------------

class CalculateRequest(BaseModel):
    grade_id: int
    thickness_band: str
    part_weight: Decimal
    qty: Decimal = Decimal("1")
    efficiency_pct: Decimal = Decimal("100")
    thickness_mm: Decimal = Decimal("0")
    norm_library_id: int | None = None
    client_id: int | None = None


CalculateResultOut = RmLineResultOut
