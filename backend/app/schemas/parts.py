from __future__ import annotations

from datetime import date, datetime
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
    sets_count: int = 1


class WorkbookUpdate(BaseModel):
    name: str | None = None
    client_id: int | None = None
    description: str | None = None
    sets_count: int | None = None


class WorkbookOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    client_id: int
    client_name: str | None = None
    description: str | None
    sets_count: int
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
    image_url: str | None = None
    qty_per_set: Decimal = Decimal("1")
    is_optional: bool = False
    status: str | None = None
    remarks: str | None = None
    supply_version: str = "V1"
    discount_pct: Decimal = Decimal("0")
    transport_cost: Decimal = Decimal("0")


class CostSheetUpdate(BaseModel):
    name: str | None = None
    part_no: str | None = None
    description: str | None = None
    drawing_no: str | None = None
    benchmark_price: Decimal | None = None
    image_url: str | None = None
    qty_per_set: Decimal | None = None
    is_optional: bool | None = None
    status: str | None = None
    remarks: str | None = None
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
    catalog_item_id: int | None = None
    unit_weight_kg: Decimal | None = None


class BOLineItemUpdate(BaseModel):
    sl_no: int | None = None
    description: str | None = None
    qty: Decimal | None = None
    unit_price: Decimal | None = None
    catalog_item_id: int | None = None
    unit_weight_kg: Decimal | None = None


class BOLineItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    cost_sheet_id: int
    sl_no: int
    description: str | None
    qty: Decimal
    unit_price: Decimal
    bo_line_cost: Decimal
    catalog_item_id: int | None = None
    unit_weight_kg: Decimal | None = None


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
    parent_line_id: int | None = None
    description: str | None = None
    spec: str | None = None
    grade_id: int | None = None
    thickness_band: str | None = None
    thickness_mm: Decimal | None = None
    qty: Decimal = Decimal("1")
    part_weight: Decimal = Decimal("0")
    efficiency_pct: Decimal = Decimal("100")


class CostingLineUpdate(BaseModel):
    parent_line_id: int | None = None
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
    parent_line_id: int | None = None
    level_no: str | None = None
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


# ---------------------------------------------------------------------------
# Price History & Repricing
# ---------------------------------------------------------------------------

class PriceHistoryEntryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    cost_sheet_id: int
    change_no: int
    price: Decimal
    rm_reference_price: Decimal | None = None
    discount_pct: Decimal
    pct_change_vs_last_supplied: Decimal | None = None
    recorded_at: datetime


class RepriceResultItem(BaseModel):
    sheet_id: int
    name: str
    before_price: Decimal
    after_price: Decimal
    pct_change: Decimal | None = None


class RepriceResponse(BaseModel):
    workbook_id: int
    repriced_count: int
    items: list[RepriceResultItem]


class CostSheetWithLines(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    workbook_id: int
    name: str
    part_no: str | None = None
    description: str | None = None
    drawing_no: str | None = None
    benchmark_price: Decimal | None = None
    image_url: str | None = None
    qty_per_set: Decimal
    is_optional: bool
    status: str | None = None
    remarks: str | None = None
    first_supply_price: Decimal | None = None
    first_supply_date: date | None = None
    first_supply_rm_reference: Decimal | None = None
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
    price_history: list[PriceHistoryEntryOut] = []


# ---------------------------------------------------------------------------
# Workbook summary
# ---------------------------------------------------------------------------

class CostSheetSummary(BaseModel):
    sheet_id: int
    name: str
    part_no: str | None
    supply_version: str
    total_price: Decimal | None
    price_after_discount: Decimal | None = None
    transport_cost: Decimal = Decimal("0")
    rm_cost: Decimal | None
    bo_grand_total: Decimal | None = None
    process_grand_total: Decimal | None = None
    bal_margin: Decimal | None = None
    bal_margin_per_kg: Decimal | None = None
    total_weight: Decimal | None
    discount_pct: Decimal | None
    pct_change_vs_previous: Decimal | None
    first_supply_price: Decimal | None = None
    first_supply_date: date | None = None
    latest_pct_change_vs_last_supplied: Decimal | None = None
    saved_at: datetime | None
    line_count: int
    saved_count: int

    # Scope / status
    qty_per_set: Decimal = Decimal("1")
    is_optional: bool = False
    status: str | None = None
    remarks: str | None = None

    # Set-level rollup (this sheet's total_price/total_weight x qty_per_set x workbook sets_count)
    set_total_price: Decimal | None = None
    set_total_weight: Decimal | None = None

    # Customer target comparison
    benchmark_price: Decimal | None = None
    price_gap: Decimal | None = None       # price_after_discount - benchmark_price
    price_gap_pct: Decimal | None = None   # price_gap / benchmark_price * 100

    # Per-kg analytics
    fabrication_per_kg: Decimal | None = None
    tack_welding_per_kg: Decimal | None = None
    full_welding_per_kg: Decimal | None = None
    machining_per_kg: Decimal | None = None
    painting_per_kg: Decimal | None = None


class WorkbookSummaryOut(BaseModel):
    id: int
    name: str
    client_id: int
    client_name: str | None = None
    sets_count: int = 1
    cost_sheets: list[CostSheetSummary]

    # Set-level totals, split standard scope vs optional items
    standard_total_price: Decimal = Decimal("0")
    standard_total_weight: Decimal = Decimal("0")
    optional_total_price: Decimal = Decimal("0")
    optional_total_weight: Decimal = Decimal("0")

    # Benchmark comparison, standard scope only
    benchmark_total: Decimal | None = None
    benchmark_gap_total: Decimal | None = None


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
