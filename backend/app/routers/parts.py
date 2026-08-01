from __future__ import annotations

import dataclasses
import logging
from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

log = logging.getLogger(__name__)

from app.calc_engine import (
    BOLineItem,
    CostingLineInput,
    FinishingOpInput,
    LineOperationInput,
    NormsSnapshot,
    ProcessCostRowInput,
    SheetCalcResult,
    calc_process_cost_from_row,
    calculate,
    calculate_process_cost_for_line,
    calculate_sheet,
)
from app.database import get_db
from app.models.clients import Client
from app.models.parts import (
    BOLineItem as BOLineItemModel,
    CostingLine,
    CostingResult,
    CostSheet,
    CostSheetResult,
    CostWorkbook,
    LineOperation,
    ProcessCostRow as ProcessCostRowModel,
    SheetFinishingOp,
)
from app.norms_loader import load_norms_snapshot
from app.schemas.parts import (
    BOLineItemCreate,
    BOLineItemOut,
    BOLineItemUpdate,
    CalculateRequest,
    CalculateResultOut,
    CostingLineCreate,
    CostingLineOut,
    CostingLineUpdate,
    CostSheetCreate,
    CostSheetUpdate,
    CostSheetWithLines,
    CostSheetSummary,
    LineOperationCreate,
    LineOperationOut,
    LineOperationUpdate,
    ProcessCostRowOut,
    ProcessCostRowUpdate,
    RmLineResultOut,
    SheetCalcResultOut,
    BlockMarkupOut,
    SheetFinishingOpCreate,
    SheetFinishingOpOut,
    SheetFinishingOpUpdate,
    WorkbookCreate,
    WorkbookOut,
    WorkbookSummaryOut,
    WorkbookUpdate,
)

router = APIRouter(prefix="/api/v1", tags=["workbooks"])


def _clear_sheet_result(cost_sheet_id: int, db: Session) -> None:
    db.query(CostSheetResult).filter_by(cost_sheet_id=cost_sheet_id).delete()
    db.flush()


def _sheet_client_id(sheet: CostSheet) -> int | None:
    try:
        return sheet.workbook.client_id
    except AttributeError:
        return None


def _line_client_id(line: CostingLine) -> int | None:
    try:
        return line.sheet.workbook.client_id
    except AttributeError:
        return None


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _run_rm_calc(line: CostingLine, norms: NormsSnapshot | None) -> RmLineResultOut | None:
    if norms is None or line.grade_id is None or not line.thickness_band:
        return None
    try:
        inp = CostingLineInput(
            grade_id=line.grade_id,
            thickness_band=line.thickness_band,
            part_weight=line.part_weight,
            qty=line.qty,
            efficiency_pct=line.efficiency_pct,
            thickness_mm=line.thickness_mm or Decimal("0"),
        )
        r = calculate(inp, norms)
        return RmLineResultOut(**dataclasses.asdict(r))
    except (ValueError, KeyError) as e:
        log.warning("RM calc skipped for line %s grade=%s band=%s: %s", line.id, line.grade_id, line.thickness_band, e)
        return None


def _line_out(line: CostingLine, norms: NormsSnapshot | None) -> CostingLineOut:
    out = CostingLineOut.model_validate(line)
    out.rm_result = _run_rm_calc(line, norms)
    if norms and line.grade_id and line.thickness_band:
        inp = CostingLineInput(
            grade_id=line.grade_id,
            thickness_band=line.thickness_band,
            part_weight=line.part_weight,
            qty=line.qty,
            efficiency_pct=line.efficiency_pct,
            thickness_mm=line.thickness_mm or Decimal("0"),
        )
        ops = [LineOperationInput(op.operation_type, op.input_data) for op in line.operations]
        try:
            out.line_process_cost = calculate_process_cost_for_line(inp, ops, norms) + _line_process_row_cost(line, norms)
        except Exception:
            out.line_process_cost = Decimal("0")
    else:
        out.line_process_cost = Decimal("0")
    out.saved_at = line.saved_result.calculated_at if line.saved_result else None
    return out


def _process_row_out(row: ProcessCostRowModel, line: CostingLine, norms: NormsSnapshot | None) -> ProcessCostRowOut:
    out = ProcessCostRowOut.model_validate(row)
    total_wt = line.part_weight * line.qty
    out.total_wt = total_wt
    if norms is None:
        return out
    row_input = ProcessCostRowInput(
        qty=line.qty,
        total_wt=total_wt,
        thk=row.thk or Decimal("0"),
        unit_cut_length=row.unit_cut_length,
        use_laser=row.use_laser,
        machining_rate=row.machining_rate,
        bev_slant=row.bev_slant,
        bev_length=row.bev_length,
        bend_num_bends=row.bend_num_bends,
        drill_hours=row.drill_hours,
        drill_type=row.drill_type,
        has_rolling=row.has_rolling,
    )
    result = calc_process_cost_from_row(row_input, norms)
    out.cutting_cost = result.cutting_cost
    out.machining_cost = result.machining_cost
    out.bevelling_cost = result.bevelling_cost
    out.bending_rate = result.bending_rate
    out.bending_cost = result.bending_cost
    out.drilling_rate = result.drilling_rate
    out.drilling_cost = result.drilling_cost
    out.rolling_rate = result.rolling_rate
    out.rolling_cost = result.rolling_cost
    out.row_total = result.row_total
    return out


def _line_process_row_cost(line: CostingLine, norms: NormsSnapshot) -> Decimal:
    """Cost contributed by this line's structured Process Cost grid row, if any."""
    pcr = line.process_cost_row
    if pcr is None:
        return Decimal("0")
    total_wt = line.part_weight * line.qty
    row_input = ProcessCostRowInput(
        qty=line.qty,
        total_wt=total_wt,
        thk=pcr.thk or Decimal("0"),
        unit_cut_length=pcr.unit_cut_length,
        use_laser=pcr.use_laser,
        machining_rate=pcr.machining_rate,
        bev_slant=pcr.bev_slant,
        bev_length=pcr.bev_length,
        bend_num_bends=pcr.bend_num_bends,
        drill_hours=pcr.drill_hours,
        drill_type=pcr.drill_type,
        has_rolling=pcr.has_rolling,
    )
    return calc_process_cost_from_row(row_input, norms).row_total


def _sheet_calc(sheet: CostSheet, norms: NormsSnapshot | None) -> SheetCalcResult | None:
    if norms is None:
        return None
    try:
        lines_inp: list[CostingLineInput] = []
        line_ops_map: dict[int, list[LineOperationInput]] = {}
        precomputed_costs: list[Decimal] = []

        for i, line in enumerate(sheet.lines):
            if line.grade_id is None or not line.thickness_band:
                return None
            line_inp = CostingLineInput(
                grade_id=line.grade_id,
                thickness_band=line.thickness_band,
                part_weight=line.part_weight,
                qty=line.qty,
                efficiency_pct=line.efficiency_pct,
                thickness_mm=line.thickness_mm or Decimal("0"),
            )
            lines_inp.append(line_inp)
            ops = [
                LineOperationInput(op.operation_type, op.input_data)
                for op in line.operations
            ]
            line_ops_map[i] = ops

            # A line's process cost is whatever was entered via the structured
            # Process Cost grid (ProcessCostRow) PLUS any ad-hoc LineOperations —
            # both are legitimate, additive cost sources for the same line.
            ops_cost = calculate_process_cost_for_line(line_inp, ops, norms)
            row_cost = _line_process_row_cost(line, norms)
            precomputed_costs.append(ops_cost + row_cost)

        bo_items = [
            BOLineItem(item.description or "", item.qty, item.unit_price)
            for item in sheet.bo_items
        ]
        finishing_ops = [
            FinishingOpInput(op.operation_name, op.input_qty)
            for op in sheet.finishing_ops
        ]

        return calculate_sheet(
            lines=lines_inp,
            line_ops_map=line_ops_map,
            bo_items=bo_items,
            finishing_ops=finishing_ops,
            norms=norms,
            discount_pct=sheet.discount_pct,
            transport_cost=sheet.transport_cost,
            precomputed_line_process_costs=precomputed_costs,
        )
    except Exception as exc:
        log.warning("_sheet_calc failed for sheet_id=%s: %s", sheet.id, exc)
        return None


def _sheet_calc_out(r: SheetCalcResult) -> SheetCalcResultOut:
    def _bm(b) -> BlockMarkupOut:
        return BlockMarkupOut(
            base_total=b.base_total,
            overhead=b.overhead,
            rework=b.rework,
            inventory=b.inventory,
            profit=b.profit,
            grand_total=b.grand_total,
        )
    return SheetCalcResultOut(
        line_process_costs=r.line_process_costs,
        total_rm_cost=r.total_rm_cost,
        total_bo_cost=r.total_bo_cost,
        total_process_cost=r.total_process_cost,
        total_finishing_cost=r.total_finishing_cost,
        rm_block=_bm(r.rm_block),
        bo_block=_bm(r.bo_block),
        process_block=_bm(r.process_block),
        unit_price=r.unit_price,
        transport_cost=r.transport_cost,
        discount_pct=r.discount_pct,
        price_after_discount=r.price_after_discount,
        bal_margin=r.bal_margin,
        bal_margin_per_kg=r.bal_margin_per_kg,
        total_part_weight=r.total_part_weight,
        norm_library_id=r.norm_library_id,
    )


def _sheet_out(sheet: CostSheet, db: Session, norms: NormsSnapshot | None = None) -> CostSheetWithLines:
    client_id = _sheet_client_id(sheet)
    if norms is None:
        try:
            norms = load_norms_snapshot(db, client_id=client_id)
        except ValueError:
            norms = None  # no published norm library yet — return sheet without calculations
    out = CostSheetWithLines.model_validate(sheet)
    out.client_id = client_id
    out.lines = [_line_out(ln, norms) for ln in sheet.lines]
    out.process_rows = [
        _process_row_out(ln.process_cost_row, ln, norms)
        for ln in sheet.lines
        if ln.process_cost_row is not None
    ]
    calc = _sheet_calc(sheet, norms)
    out.sheet_result = _sheet_calc_out(calc) if calc else None
    return out


# ---------------------------------------------------------------------------
# Cost Workbooks
# ---------------------------------------------------------------------------

def _workbook_out(wb: CostWorkbook, sheet_count: int | None = None) -> WorkbookOut:
    out = WorkbookOut.model_validate(wb)
    out.client_name = wb.client.name if wb.client else None
    out.sheet_count = sheet_count if sheet_count is not None else len(wb.cost_sheets)
    return out


@router.get("/workbooks", response_model=list[WorkbookOut])
def list_workbooks(client_id: int | None = None, db: Session = Depends(get_db)):
    q = db.query(CostWorkbook)
    if client_id is not None:
        q = q.filter(CostWorkbook.client_id == client_id)
    workbooks = q.order_by(CostWorkbook.created_at.desc()).all()
    return [_workbook_out(wb) for wb in workbooks]


@router.post("/workbooks", response_model=WorkbookOut, status_code=201)
def create_workbook(body: WorkbookCreate, db: Session = Depends(get_db)):
    if not db.get(Client, body.client_id):
        raise HTTPException(status_code=404, detail=f"Client {body.client_id} not found")
    wb = CostWorkbook(**body.model_dump())
    db.add(wb)
    db.commit()
    db.refresh(wb)
    return _workbook_out(wb, sheet_count=0)


@router.get("/workbooks/{workbook_id}", response_model=WorkbookOut)
def get_workbook(workbook_id: int, db: Session = Depends(get_db)):
    wb = db.get(CostWorkbook, workbook_id)
    if not wb:
        raise HTTPException(status_code=404, detail="Workbook not found")
    return _workbook_out(wb)


@router.get("/workbooks/{workbook_id}/summary", response_model=WorkbookSummaryOut)
def get_workbook_summary(workbook_id: int, db: Session = Depends(get_db)):
    wb = db.get(CostWorkbook, workbook_id)
    if not wb:
        raise HTTPException(status_code=404, detail="Workbook not found")

    sheet_summaries: list[CostSheetSummary] = []
    for sheet in sorted(wb.cost_sheets, key=lambda s: s.created_at):
        saved = sheet.saved_result
        sheet_summaries.append(CostSheetSummary(
            sheet_id=sheet.id,
            name=sheet.name,
            part_no=sheet.part_no,
            supply_version=sheet.supply_version,
            total_price=saved.unit_price if saved else None,
            rm_cost=saved.rm_grand_total if saved else None,
            bo_grand_total=saved.bo_grand_total if saved else None,
            process_grand_total=saved.process_grand_total if saved else None,
            bal_margin=saved.bal_margin if saved else None,
            total_weight=saved.total_part_weight if saved else None,
            discount_pct=saved.discount_pct_snap if saved else None,
            pct_change_vs_previous=saved.pct_change_vs_previous if saved else None,
            saved_at=saved.calculated_at if saved else None,
            line_count=len(sheet.lines),
            saved_count=1 if saved else 0,
        ))

    return WorkbookSummaryOut(
        id=wb.id,
        name=wb.name,
        client_id=wb.client_id,
        client_name=wb.client.name if wb.client else None,
        cost_sheets=sheet_summaries,
    )


@router.patch("/workbooks/{workbook_id}", response_model=WorkbookOut)
def update_workbook(workbook_id: int, body: WorkbookUpdate, db: Session = Depends(get_db)):
    wb = db.get(CostWorkbook, workbook_id)
    if not wb:
        raise HTTPException(status_code=404, detail="Workbook not found")
    updates = body.model_dump(exclude_unset=True)
    if "client_id" in updates and updates["client_id"] is not None:
        if not db.get(Client, updates["client_id"]):
            raise HTTPException(status_code=404, detail=f"Client {updates['client_id']} not found")
    for field, value in updates.items():
        setattr(wb, field, value)
    db.commit()
    db.refresh(wb)
    return _workbook_out(wb)


@router.delete("/workbooks/{workbook_id}", status_code=204)
def delete_workbook(workbook_id: int, db: Session = Depends(get_db)):
    wb = db.get(CostWorkbook, workbook_id)
    if not wb:
        raise HTTPException(status_code=404, detail="Workbook not found")
    db.delete(wb)
    db.commit()


# ---------------------------------------------------------------------------
# Cost Sheets
# ---------------------------------------------------------------------------

@router.get("/workbooks/{workbook_id}/sheets", response_model=list[CostSheetWithLines])
def list_sheets(workbook_id: int, db: Session = Depends(get_db)):
    wb = db.get(CostWorkbook, workbook_id)
    if not wb:
        raise HTTPException(status_code=404, detail="Workbook not found")
    sheets = db.query(CostSheet).filter_by(workbook_id=workbook_id).order_by(CostSheet.created_at).all()
    return [_sheet_out(s, db) for s in sheets]


@router.post("/workbooks/{workbook_id}/sheets", response_model=CostSheetWithLines, status_code=201)
def create_sheet(workbook_id: int, body: CostSheetCreate, db: Session = Depends(get_db)):
    if not db.get(CostWorkbook, workbook_id):
        raise HTTPException(status_code=404, detail="Workbook not found")
    sheet = CostSheet(workbook_id=workbook_id, **body.model_dump())
    db.add(sheet)
    db.commit()
    db.refresh(sheet)
    return _sheet_out(sheet, db)


@router.get("/sheets/{sheet_id}", response_model=CostSheetWithLines)
def get_sheet(sheet_id: int, db: Session = Depends(get_db)):
    sheet = db.get(CostSheet, sheet_id)
    if not sheet:
        raise HTTPException(status_code=404, detail="Cost sheet not found")
    return _sheet_out(sheet, db)


@router.patch("/sheets/{sheet_id}", response_model=CostSheetWithLines)
def update_sheet(sheet_id: int, body: CostSheetUpdate, db: Session = Depends(get_db)):
    sheet = db.get(CostSheet, sheet_id)
    if not sheet:
        raise HTTPException(status_code=404, detail="Cost sheet not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(sheet, field, value)
    _clear_sheet_result(sheet_id, db)
    db.commit()
    db.refresh(sheet)
    return _sheet_out(sheet, db)


@router.delete("/sheets/{sheet_id}", status_code=204)
def delete_sheet(sheet_id: int, db: Session = Depends(get_db)):
    sheet = db.get(CostSheet, sheet_id)
    if not sheet:
        raise HTTPException(status_code=404, detail="Cost sheet not found")
    db.delete(sheet)
    db.commit()


@router.post("/sheets/{sheet_id}/save-results", response_model=CostSheetWithLines)
def save_sheet_results(sheet_id: int, db: Session = Depends(get_db)):
    sheet = db.get(CostSheet, sheet_id)
    if not sheet:
        raise HTTPException(status_code=404, detail="Cost sheet not found")

    try:
        norms = load_norms_snapshot(db, client_id=_sheet_client_id(sheet))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    calc = _sheet_calc(sheet, norms)
    if calc is None:
        raise HTTPException(status_code=400, detail="Sheet has incomplete lines; cannot save results")

    # Find previous sheet in the same workbook for pct_change
    all_sheets = (
        db.query(CostSheet)
        .filter_by(workbook_id=sheet.workbook_id)
        .order_by(CostSheet.created_at)
        .all()
    )
    prev_sheet: CostSheet | None = None
    for i, s in enumerate(all_sheets):
        if s.id == sheet_id and i > 0:
            prev_sheet = all_sheets[i - 1]
            break

    prev_price: Decimal | None = None
    if prev_sheet and prev_sheet.saved_result:
        prev_price = prev_sheet.saved_result.price_after_discount

    pct_change: Decimal | None = None
    if prev_price is not None and prev_price != Decimal("0"):
        pct_change = (calc.price_after_discount - prev_price) / prev_price * Decimal("100")

    now = datetime.now(timezone.utc).replace(tzinfo=None)

    for i, (line, rm_r) in enumerate(zip(sheet.lines, calc.line_rm_results)):
        pc = calc.line_process_costs[i]
        existing = db.query(CostingResult).filter_by(costing_line_id=line.id).first()
        vals = dict(
            norm_library_id=rm_r.norm_library_id,
            calculated_at=now,
            total_part_weight=rm_r.total_part_weight,
            blank_weight=rm_r.blank_weight,
            total_blank_weight=rm_r.total_blank_weight,
            blank_rate=rm_r.blank_rate,
            blank_cost=rm_r.blank_cost,
            process_loss_pct=rm_r.process_loss_pct,
            process_loss_weight=rm_r.process_loss_weight,
            scrap_weight=rm_r.scrap_weight,
            scrap_cost=rm_r.scrap_cost,
            rm_cost=rm_r.rm_cost,
            line_process_cost=pc,
        )
        if existing:
            for k, v in vals.items():
                setattr(existing, k, v)
        else:
            db.add(CostingResult(costing_line_id=line.id, **vals))

    sheet_vals = dict(
        norm_library_id=calc.norm_library_id,
        calculated_at=now,
        total_rm_cost=calc.total_rm_cost,
        overhead_rm=calc.rm_block.overhead,
        rework_rm=calc.rm_block.rework,
        inventory_rm=calc.rm_block.inventory,
        profit_rm=calc.rm_block.profit,
        rm_grand_total=calc.rm_block.grand_total,
        total_bo_cost=calc.total_bo_cost,
        overhead_bo=calc.bo_block.overhead,
        inventory_bo=calc.bo_block.inventory,
        profit_bo=calc.bo_block.profit,
        bo_grand_total=calc.bo_block.grand_total,
        total_process_cost=calc.total_process_cost,
        overhead_proc=calc.process_block.overhead,
        rework_proc=calc.process_block.rework,
        profit_proc=calc.process_block.profit,
        process_grand_total=calc.process_block.grand_total,
        unit_price=calc.unit_price,
        transport_cost_snap=calc.transport_cost,
        discount_pct_snap=calc.discount_pct,
        price_after_discount=calc.price_after_discount,
        pct_change_vs_previous=pct_change,
        bal_margin=calc.bal_margin,
        bal_margin_per_kg=calc.bal_margin_per_kg,
        total_part_weight=calc.total_part_weight,
    )
    existing_result = db.query(CostSheetResult).filter_by(cost_sheet_id=sheet_id).first()
    if existing_result:
        for k, v in sheet_vals.items():
            setattr(existing_result, k, v)
    else:
        db.add(CostSheetResult(cost_sheet_id=sheet_id, **sheet_vals))

    for i, line in enumerate(sheet.lines):
        inp = CostingLineInput(
            grade_id=line.grade_id or 0,
            thickness_band=line.thickness_band or "",
            part_weight=line.part_weight,
            qty=line.qty,
            efficiency_pct=line.efficiency_pct,
            thickness_mm=line.thickness_mm or Decimal("0"),
        )
        from app.calc_engine import _operation_cost as _op_cost
        for op in line.operations:
            op_inp = LineOperationInput(op.operation_type, op.input_data)
            try:
                op.operation_cost = _op_cost(op_inp, inp, norms)
            except Exception:
                op.operation_cost = Decimal("0")

    for fop in sheet.finishing_ops:
        from app.calc_engine import _ZERO
        rate = norms.process_rates.get(fop.operation_name, _ZERO)
        fop.computed_cost = fop.input_qty * rate

    db.commit()
    db.refresh(sheet)
    return _sheet_out(sheet, db, norms)


# ---------------------------------------------------------------------------
# Costing Lines
# ---------------------------------------------------------------------------

@router.post("/sheets/{sheet_id}/lines", response_model=CostingLineOut, status_code=201)
def add_line(sheet_id: int, body: CostingLineCreate, db: Session = Depends(get_db)):
    sheet = db.get(CostSheet, sheet_id)
    if not sheet:
        raise HTTPException(status_code=404, detail="Cost sheet not found")

    if body.sl_no is None:
        max_sl = db.query(func.max(CostingLine.sl_no)).filter_by(cost_sheet_id=sheet_id).scalar() or 0
        sl_no = max_sl + 1
    else:
        sl_no = body.sl_no

    line = CostingLine(
        cost_sheet_id=sheet_id,
        sl_no=sl_no,
        description=body.description,
        spec=body.spec,
        grade_id=body.grade_id,
        thickness_band=body.thickness_band,
        thickness_mm=body.thickness_mm,
        qty=body.qty,
        part_weight=body.part_weight,
        efficiency_pct=body.efficiency_pct,
    )
    db.add(line)
    db.flush()
    db.add(ProcessCostRowModel(costing_line_id=line.id, thk=body.thickness_mm))
    _clear_sheet_result(sheet_id, db)
    db.commit()
    db.refresh(line)
    try:
        norms = load_norms_snapshot(db, client_id=_sheet_client_id(sheet))
    except ValueError:
        norms = None
    return _line_out(line, norms)


@router.patch("/sheets/{sheet_id}/lines/{line_id}", response_model=CostingLineOut)
def update_line(sheet_id: int, line_id: int, body: CostingLineUpdate, db: Session = Depends(get_db)):
    line = db.get(CostingLine, line_id)
    if not line or line.cost_sheet_id != sheet_id:
        raise HTTPException(status_code=404, detail="Costing line not found")
    for fld, value in body.model_dump(exclude_unset=True).items():
        setattr(line, fld, value)
    _clear_sheet_result(sheet_id, db)
    db.flush()
    try:
        norms = load_norms_snapshot(db, client_id=_line_client_id(line))
    except ValueError:
        norms = None
    if norms and line.grade_id and line.thickness_band:
        from app.calc_engine import _operation_cost as _op_cost
        inp = CostingLineInput(
            grade_id=line.grade_id or 0,
            thickness_band=line.thickness_band or "",
            part_weight=line.part_weight,
            qty=line.qty,
            efficiency_pct=line.efficiency_pct,
            thickness_mm=line.thickness_mm or Decimal("0"),
        )
        for op in line.operations:
            op_inp = LineOperationInput(op.operation_type, op.input_data)
            try:
                op.operation_cost = _op_cost(op_inp, inp, norms)
            except Exception as e:
                log.warning("recompute op cost failed for type=%r: %s", op.operation_type, e)
    db.commit()
    db.refresh(line)
    return _line_out(line, norms)


@router.delete("/sheets/{sheet_id}/lines/{line_id}", status_code=204)
def delete_line(sheet_id: int, line_id: int, db: Session = Depends(get_db)):
    line = db.get(CostingLine, line_id)
    if not line or line.cost_sheet_id != sheet_id:
        raise HTTPException(status_code=404, detail="Costing line not found")
    _clear_sheet_result(sheet_id, db)
    db.delete(line)
    db.commit()


# ---------------------------------------------------------------------------
# Process Cost Rows
# ---------------------------------------------------------------------------

@router.patch("/process-rows/{row_id}", response_model=ProcessCostRowOut)
def update_process_row(row_id: int, body: ProcessCostRowUpdate, db: Session = Depends(get_db)):
    row = db.get(ProcessCostRowModel, row_id)
    if not row:
        raise HTTPException(status_code=404, detail="Process cost row not found")
    line = db.get(CostingLine, row.costing_line_id)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(row, field, value)
    _clear_sheet_result(line.cost_sheet_id, db)
    db.commit()
    db.refresh(row)
    try:
        norms = load_norms_snapshot(db, client_id=_line_client_id(line))
    except ValueError:
        norms = None
    return _process_row_out(row, line, norms)


# ---------------------------------------------------------------------------
# BO Line Items
# ---------------------------------------------------------------------------

@router.post("/sheets/{sheet_id}/bo-items", response_model=BOLineItemOut, status_code=201)
def add_bo_item(sheet_id: int, body: BOLineItemCreate, db: Session = Depends(get_db)):
    sheet = db.get(CostSheet, sheet_id)
    if not sheet:
        raise HTTPException(status_code=404, detail="Cost sheet not found")
    if body.sl_no is None:
        max_sl = db.query(func.max(BOLineItemModel.sl_no)).filter_by(cost_sheet_id=sheet_id).scalar() or 0
        sl_no = max_sl + 1
    else:
        sl_no = body.sl_no
    item = BOLineItemModel(
        cost_sheet_id=sheet_id,
        sl_no=sl_no,
        description=body.description,
        qty=body.qty,
        unit_price=body.unit_price,
    )
    db.add(item)
    _clear_sheet_result(sheet_id, db)
    db.commit()
    db.refresh(item)
    return BOLineItemOut.model_validate(item)


@router.patch("/sheets/{sheet_id}/bo-items/{item_id}", response_model=BOLineItemOut)
def update_bo_item(sheet_id: int, item_id: int, body: BOLineItemUpdate, db: Session = Depends(get_db)):
    item = db.get(BOLineItemModel, item_id)
    if not item or item.cost_sheet_id != sheet_id:
        raise HTTPException(status_code=404, detail="BO item not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    _clear_sheet_result(sheet_id, db)
    db.commit()
    db.refresh(item)
    return BOLineItemOut.model_validate(item)


@router.delete("/sheets/{sheet_id}/bo-items/{item_id}", status_code=204)
def delete_bo_item(sheet_id: int, item_id: int, db: Session = Depends(get_db)):
    item = db.get(BOLineItemModel, item_id)
    if not item or item.cost_sheet_id != sheet_id:
        raise HTTPException(status_code=404, detail="BO item not found")
    _clear_sheet_result(sheet_id, db)
    db.delete(item)
    db.commit()


# ---------------------------------------------------------------------------
# Costing Line Operations
# ---------------------------------------------------------------------------

@router.post("/costing-lines/{line_id}/operations", response_model=LineOperationOut, status_code=201)
def add_line_operation(line_id: int, body: LineOperationCreate, db: Session = Depends(get_db)):
    line = db.get(CostingLine, line_id)
    if not line:
        raise HTTPException(status_code=404, detail="Costing line not found")
    try:
        norms = load_norms_snapshot(db, client_id=_line_client_id(line))
    except ValueError:
        norms = None
    inp = CostingLineInput(
        grade_id=line.grade_id or 0,
        thickness_band=line.thickness_band or "",
        part_weight=line.part_weight,
        qty=line.qty,
        efficiency_pct=line.efficiency_pct,
        thickness_mm=line.thickness_mm or Decimal("0"),
    )
    from app.calc_engine import _operation_cost
    op_inp = LineOperationInput(body.operation_type, body.input_data)
    try:
        cost = _operation_cost(op_inp, inp, norms)
    except Exception as e:
        log.warning("op_cost failed for type=%r: %s", body.operation_type, e)
        cost = Decimal("0")
    op = LineOperation(
        costing_line_id=line_id,
        operation_type=body.operation_type,
        input_data=body.input_data,
        operation_cost=cost,
    )
    db.add(op)
    _clear_sheet_result(line.cost_sheet_id, db)
    db.commit()
    db.refresh(op)
    return LineOperationOut.model_validate(op)


@router.patch("/costing-lines/{line_id}/operations/{op_id}", response_model=LineOperationOut)
def update_line_operation(line_id: int, op_id: int, body: LineOperationUpdate, db: Session = Depends(get_db)):
    op = db.get(LineOperation, op_id)
    if not op or op.costing_line_id != line_id:
        raise HTTPException(status_code=404, detail="Operation not found")
    if body.operation_type is not None:
        op.operation_type = body.operation_type
    if body.input_data is not None:
        op.input_data = body.input_data
    line = db.get(CostingLine, line_id)
    try:
        norms = load_norms_snapshot(db, client_id=_line_client_id(line))
    except ValueError:
        norms = None
    inp = CostingLineInput(
        grade_id=line.grade_id or 0,
        thickness_band=line.thickness_band or "",
        part_weight=line.part_weight,
        qty=line.qty,
        efficiency_pct=line.efficiency_pct,
        thickness_mm=line.thickness_mm or Decimal("0"),
    )
    from app.calc_engine import _operation_cost
    op_inp = LineOperationInput(op.operation_type, op.input_data)
    try:
        op.operation_cost = _operation_cost(op_inp, inp, norms)
    except Exception as e:
        log.warning("op_cost update failed: %s", e)
        op.operation_cost = Decimal("0")
    _clear_sheet_result(line.cost_sheet_id, db)
    db.commit()
    db.refresh(op)
    return LineOperationOut.model_validate(op)


@router.delete("/costing-lines/{line_id}/operations/{op_id}", status_code=204)
def delete_line_operation(line_id: int, op_id: int, db: Session = Depends(get_db)):
    op = db.get(LineOperation, op_id)
    if not op or op.costing_line_id != line_id:
        raise HTTPException(status_code=404, detail="Operation not found")
    line = db.get(CostingLine, line_id)
    if line:
        _clear_sheet_result(line.cost_sheet_id, db)
    db.delete(op)
    db.commit()


# ---------------------------------------------------------------------------
# Sheet Finishing Ops
# ---------------------------------------------------------------------------

@router.post("/sheets/{sheet_id}/finishing-ops", response_model=SheetFinishingOpOut, status_code=201)
def add_finishing_op(sheet_id: int, body: SheetFinishingOpCreate, db: Session = Depends(get_db)):
    sheet = db.get(CostSheet, sheet_id)
    if not sheet:
        raise HTTPException(status_code=404, detail="Cost sheet not found")
    try:
        norms = load_norms_snapshot(db, client_id=_sheet_client_id(sheet))
    except ValueError:
        norms = None
    from app.calc_engine import _ZERO
    rate = norms.process_rates.get(body.operation_name, _ZERO) if norms else _ZERO
    cost = body.input_qty * rate
    op = SheetFinishingOp(
        cost_sheet_id=sheet_id,
        operation_name=body.operation_name,
        input_qty=body.input_qty,
        computed_cost=cost,
    )
    db.add(op)
    _clear_sheet_result(sheet_id, db)
    db.commit()
    db.refresh(op)
    return SheetFinishingOpOut.model_validate(op)


@router.patch("/sheets/{sheet_id}/finishing-ops/{op_id}", response_model=SheetFinishingOpOut)
def update_finishing_op(sheet_id: int, op_id: int, body: SheetFinishingOpUpdate, db: Session = Depends(get_db)):
    op = db.get(SheetFinishingOp, op_id)
    if not op or op.cost_sheet_id != sheet_id:
        raise HTTPException(status_code=404, detail="Finishing op not found")
    if body.input_qty is not None:
        op.input_qty = body.input_qty
        sheet = db.get(CostSheet, sheet_id)
        try:
            norms = load_norms_snapshot(db, client_id=_sheet_client_id(sheet) if sheet else None)
        except ValueError:
            norms = None
        from app.calc_engine import _ZERO
        rate = norms.process_rates.get(op.operation_name, _ZERO) if norms else _ZERO
        op.computed_cost = body.input_qty * rate
    _clear_sheet_result(sheet_id, db)
    db.commit()
    db.refresh(op)
    return SheetFinishingOpOut.model_validate(op)


@router.delete("/sheets/{sheet_id}/finishing-ops/{op_id}", status_code=204)
def delete_finishing_op(sheet_id: int, op_id: int, db: Session = Depends(get_db)):
    op = db.get(SheetFinishingOp, op_id)
    if not op or op.cost_sheet_id != sheet_id:
        raise HTTPException(status_code=404, detail="Finishing op not found")
    _clear_sheet_result(sheet_id, db)
    db.delete(op)
    db.commit()


# ---------------------------------------------------------------------------
# Legacy single-line RM preview
# ---------------------------------------------------------------------------

@router.post("/calculate", response_model=CalculateResultOut)
def calculate_line(body: CalculateRequest, db: Session = Depends(get_db)):
    try:
        norms = load_norms_snapshot(
            db,
            client_id=body.client_id,
            norm_library_id=body.norm_library_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    inp = CostingLineInput(
        grade_id=body.grade_id,
        thickness_band=body.thickness_band,
        part_weight=body.part_weight,
        qty=body.qty,
        efficiency_pct=body.efficiency_pct,
        thickness_mm=body.thickness_mm,
    )
    try:
        result = calculate(inp, norms)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return CalculateResultOut(**dataclasses.asdict(result))
