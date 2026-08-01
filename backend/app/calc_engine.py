"""
Pure calculation engine — NO database access inside this module.

Entry points (per-line, unchanged from Phase 2):
    calculate(line, norms)  ->  RmLineResult

New sheet-level entry points (Phase 3):
    calculate_bo_cost(bo_items)                             -> Decimal
    calculate_process_cost_for_line(line, ops, norms)       -> Decimal
    calculate_sheet_finishing_cost(finishing_ops, norms)    -> Decimal
    calculate_block_markup(base_total, applies_to, norms)   -> BlockMarkup
    calculate_sheet(lines, line_ops_map, bo_items,
                    finishing_ops, norms,
                    discount_pct, transport_cost)           -> SheetCalcResult
"""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

# ---------------------------------------------------------------------------
# Shared constants
# ---------------------------------------------------------------------------

_ZERO = Decimal("0")
_HUNDRED = Decimal("100")

# Maps drilling_type string → process_rates key
# NOTE: these must match the operation_name strings actually seeded into
# norm_libraries (see norms.py::_SEED_PROCESS_RATES), not an invented convention.
_DRILLING_RATE_KEY: dict[str, str] = {
    "regular":     "Drilling",
    "eh_hiten":    "Drilling (EH/Hiten)",
    "ehc450_500":  "Drilling (EHC450/EHC500)",
}

# Maps num_bends → process_rates key
_BEND_RATE_KEY: dict[int, str] = {
    1: "1 Bend",
    2: "2 Bend",
    3: "3 Bend",
}


# ---------------------------------------------------------------------------
# Input / output data-classes
# ---------------------------------------------------------------------------

@dataclass
class CostingLineInput:
    """Per-line RM inputs (unchanged from Phase 2, minus old BO/process/discount fields)."""
    grade_id: int
    thickness_band: str
    part_weight: Decimal          # kg, finished part per piece
    qty: Decimal                  # number of pieces
    efficiency_pct: Decimal       # e.g. 90 means 90%
    thickness_mm: Decimal = _ZERO # needed for cutting formulas


@dataclass
class NormsSnapshot:
    """
    All rate/param values resolved from a single norm_library row.
    Built by norms_loader.load_norms_snapshot(); never mutated here.
    """
    norm_library_id: int
    rm_prices: dict[tuple[int, str], Decimal]           # (grade_id, band) -> price/kg
    grade_premiums: dict[int, tuple[int, Decimal]]      # grade_id -> (base_id, premium)
    scrap_rate: Decimal
    process_loss_pct: Decimal
    process_rates: dict[str, Decimal]                   # operation_name -> rate
    overhead_params: dict[tuple[str, str], Decimal]     # (applies_to, param_name) -> pct
    process_rate_units: dict[str, str] = field(default_factory=dict)  # operation_name -> unit


@dataclass
class RmLineResult:
    """Per-line RM chain output (stored in costing_results)."""
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


# Alias kept so existing imports of `CostingResult` still work
CostingResult = RmLineResult


@dataclass
class BOLineItem:
    description: str
    qty: Decimal
    unit_price: Decimal       # per BO item


@dataclass
class LineOperationInput:
    """One structured process operation on a costing_line."""
    operation_type: str       # cutting | laser_cutting | machining | bevelling | bending | drilling | rolling
    input_data: dict[str, Any]


@dataclass
class FinishingOpInput:
    """One sheet-level finishing operation."""
    operation_name: str       # matches process_rates.operation_name
    input_qty: Decimal


@dataclass
class BlockMarkup:
    base_total: Decimal
    overhead: Decimal
    rework: Decimal           # 0 for bought_out
    inventory: Decimal        # 0 for process_cost
    profit: Decimal
    grand_total: Decimal


@dataclass
class ProcessCostRowInput:
    qty: Decimal
    total_wt: Decimal           # from RM result (total_part_weight)
    thk: Decimal                # process-row-specific thickness
    unit_cut_length: Decimal | None
    use_laser: bool
    machining_rate: Decimal | None
    bev_slant: Decimal | None   # number of slants
    bev_length: Decimal | None  # slant length mm
    bend_num_bends: int | None
    drill_hours: Decimal | None
    drill_type: str             # 'regular' | 'eh_hiten' | 'ehc450_500'
    has_rolling: bool


@dataclass
class ProcessCostRowResult:
    cutting_cost: Decimal
    machining_cost: Decimal
    bevelling_cost: Decimal
    bending_rate: Decimal
    bending_cost: Decimal
    drilling_rate: Decimal
    drilling_cost: Decimal
    rolling_rate: Decimal
    rolling_cost: Decimal
    row_total: Decimal


@dataclass
class SheetCalcResult:
    # Per-line RM details
    line_rm_results: list[RmLineResult]
    line_process_costs: list[Decimal]   # parallel list — process cost per line

    # Block totals
    total_rm_cost: Decimal
    total_bo_cost: Decimal
    total_process_cost: Decimal
    total_finishing_cost: Decimal       # subset of total_process_cost

    # Block markups
    rm_block: BlockMarkup
    bo_block: BlockMarkup
    process_block: BlockMarkup

    # Final
    unit_price: Decimal
    transport_cost: Decimal
    discount_pct: Decimal
    price_after_discount: Decimal
    bal_margin: Decimal
    bal_margin_per_kg: Decimal
    total_part_weight: Decimal
    norm_library_id: int


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _pct(norms: NormsSnapshot, applies_to: str, param_name: str) -> Decimal:
    """Return the overhead/profit % as a fraction (e.g. 5% → 0.05)."""
    raw = norms.overhead_params.get((applies_to, param_name), _ZERO)
    return raw / _HUNDRED


def _resolve_blank_rate(line: CostingLineInput, norms: NormsSnapshot) -> Decimal:
    if line.grade_id in norms.grade_premiums:
        base_grade_id, premium = norms.grade_premiums[line.grade_id]
        base_rate = norms.rm_prices.get((base_grade_id, line.thickness_band))
        if base_rate is None:
            raise ValueError(
                f"No RM price for base grade_id={base_grade_id}, "
                f"band='{line.thickness_band}' in norm_library {norms.norm_library_id}"
            )
        return base_rate + premium

    rate = norms.rm_prices.get((line.grade_id, line.thickness_band))
    if rate is None:
        raise ValueError(
            f"No RM price for grade_id={line.grade_id}, "
            f"band='{line.thickness_band}' in norm_library {norms.norm_library_id}"
        )
    return rate


def _operation_cost(
    op: LineOperationInput,
    line: CostingLineInput,
    norms: NormsSnapshot,
) -> Decimal:
    """Compute cost for one structured line operation."""
    d = op.input_data
    total_part_weight = line.part_weight * line.qty
    t = op.operation_type

    if t in ("cutting", "laser_cutting"):
        length_mm = Decimal(str(d["length_mm"]))
        rate_key = "Plasma Cutting" if t == "cutting" else "Laser Cutting"
        # (length_mm/1000) * thickness_mm * qty * rate  [Rs/mm/meter]
        return (length_mm / _HUNDRED / Decimal("10")) * line.thickness_mm * line.qty \
               * norms.process_rates.get(rate_key, _ZERO)

    if t == "machining":
        hours = Decimal(str(d["hours"]))
        custom = d.get("custom_rate")
        rate = Decimal(str(custom)) if custom is not None else norms.process_rates.get("Machining (VTL)", _ZERO)
        return hours * rate * line.qty

    if t == "bevelling":
        slant_mm = Decimal(str(d["slant_length_mm"]))
        num_slants = Decimal(str(d.get("num_slants", 1)))
        # (slant_mm/1000) * num_slants * rate * qty  [Rs/slant/meter]
        return (slant_mm / _HUNDRED / Decimal("10")) * num_slants \
               * norms.process_rates.get("Bevelling", _ZERO) * line.qty

    if t == "bending":
        num_bends = int(d["num_bends"])
        rate_key = _BEND_RATE_KEY.get(num_bends, "1 Bend")
        # rate already encodes total cost for N bends; just multiply by weight
        return total_part_weight * norms.process_rates.get(rate_key, _ZERO)

    if t == "drilling":
        hours = Decimal(str(d["hours"]))
        dtype = d.get("drilling_type", "regular")
        rate_key = _DRILLING_RATE_KEY.get(dtype, "Drilling")
        return hours * line.qty * norms.process_rates.get(rate_key, _ZERO)

    if t == "rolling":
        return norms.process_rates.get("Rolling", _ZERO) * total_part_weight

    # Generic path: operation_type is a norms operation_name (e.g. "TACK WELDING")
    rate = norms.process_rates.get(t, _ZERO)
    unit = norms.process_rate_units.get(t, "")

    if unit == "Rs/mm/meter":
        length_mm = Decimal(str(d.get("length_mm", 0)))
        return (length_mm / Decimal("1000")) * line.thickness_mm * line.qty * rate

    if unit == "Rs/slant/meter":
        slant_mm = Decimal(str(d.get("slant_length_mm", 0)))
        num_slants = Decimal(str(d.get("num_slants", 1)))
        return (slant_mm / Decimal("1000")) * num_slants * rate * line.qty

    if unit == "Rs/Kg":
        return total_part_weight * rate

    if unit == "Rs/Hr":
        hours = Decimal(str(d.get("hours", 0)))
        return hours * line.qty * rate

    if unit in ("Rs/Nos", "Rs/Sqm"):
        input_qty = Decimal(str(d.get("input_qty", 0)))
        return input_qty * rate

    return _ZERO


# ---------------------------------------------------------------------------
# Public API — per-line RM chain (unchanged behaviour from Phase 2)
# ---------------------------------------------------------------------------

def calculate(line: CostingLineInput, norms: NormsSnapshot) -> RmLineResult:
    """
    Pure per-line RM chain calculator.
    Returns weights + rm_cost only — BO/process/markups are now sheet-level.
    """
    total_part_weight  = line.part_weight * line.qty
    blank_rate         = _resolve_blank_rate(line, norms)
    blank_weight       = line.part_weight / (line.efficiency_pct / _HUNDRED)
    total_blank_weight = blank_weight * line.qty
    blank_cost         = total_blank_weight * blank_rate

    ploss_pct          = norms.process_loss_pct
    process_loss_weight = total_blank_weight * (ploss_pct / _HUNDRED)
    scrap_weight       = total_blank_weight - total_part_weight - process_loss_weight
    scrap_cost         = scrap_weight * norms.scrap_rate
    rm_cost            = blank_cost - scrap_cost

    return RmLineResult(
        part_weight         = line.part_weight,
        total_part_weight   = total_part_weight,
        blank_weight        = blank_weight,
        total_blank_weight  = total_blank_weight,
        blank_rate          = blank_rate,
        blank_cost          = blank_cost,
        process_loss_pct    = ploss_pct,
        process_loss_weight = process_loss_weight,
        scrap_weight        = scrap_weight,
        scrap_cost          = scrap_cost,
        rm_cost             = rm_cost,
        norm_library_id    = norms.norm_library_id,
    )


# ---------------------------------------------------------------------------
# Public API — sheet-level (Phase 3, new)
# ---------------------------------------------------------------------------

def calculate_bo_cost(bo_items: list[BOLineItem]) -> Decimal:
    """Sum of qty * unit_price across all BO line items."""
    return sum((item.qty * item.unit_price for item in bo_items), _ZERO)


def calculate_process_cost_for_line(
    line: CostingLineInput,
    operations: list[LineOperationInput],
    norms: NormsSnapshot,
) -> Decimal:
    """Sum of all structured process operation costs for one costing_line."""
    return sum((_operation_cost(op, line, norms) for op in operations), _ZERO)


def calculate_sheet_finishing_cost(
    finishing_ops: list[FinishingOpInput],
    norms: NormsSnapshot,
) -> Decimal:
    """Sum of input_qty * rate for each sheet-level finishing operation."""
    return sum(
        (op.input_qty * norms.process_rates.get(op.operation_name, _ZERO)
         for op in finishing_ops),
        _ZERO,
    )


def calculate_block_markup(
    base_total: Decimal,
    applies_to: str,
    norms: NormsSnapshot,
) -> BlockMarkup:
    """
    Apply overhead/rework/inventory/profit to a block total.

    bought_out  → no Rework      (not stored in DB; _pct returns 0 automatically)
    process_cost → no Inventory  (not stored in DB; _pct returns 0 automatically)
    """
    overhead  = base_total * _pct(norms, applies_to, "Overhead")
    rework    = base_total * _pct(norms, applies_to, "Rework")
    inventory = base_total * _pct(norms, applies_to, "Inventory Carry")
    profit    = base_total * _pct(norms, applies_to, "Profit")
    grand     = base_total + overhead + rework + inventory + profit
    return BlockMarkup(
        base_total  = base_total,
        overhead    = overhead,
        rework      = rework,
        inventory   = inventory,
        profit      = profit,
        grand_total = grand,
    )


def calc_process_cost_from_row(
    row: ProcessCostRowInput,
    norms: NormsSnapshot,
) -> ProcessCostRowResult:
    """
    Compute per-operation costs for one Process Cost table row.

    Formulas:
      cutting:   (unit_cut_length * thk * qty * rate) / 1000
      machining: machining_rate * qty
      bevelling: (bev_length / 1000) * bev_slant * bev_rate * qty
      bending:   bending_rate * total_wt
      drilling:  drill_hours * qty * drill_rate
      rolling:   rolling_rate * total_wt
    """
    _M = Decimal("1000")

    # Cutting / laser cutting
    cutting_cost = _ZERO
    if row.unit_cut_length and row.thk:
        rate_key = "Laser Cutting" if row.use_laser else "Plasma Cutting"
        rate = norms.process_rates.get(rate_key, _ZERO)
        cutting_cost = (row.unit_cut_length * row.thk * row.qty * rate) / _M

    # Machining (flat rate entered per job, no norms lookup)
    machining_cost = _ZERO
    if row.machining_rate:
        machining_cost = row.machining_rate * row.qty

    # Bevelling
    bevelling_cost = _ZERO
    if row.bev_slant and row.bev_length:
        bev_rate = norms.process_rates.get("Bevelling", _ZERO)
        bevelling_cost = (row.bev_length / _M) * row.bev_slant * bev_rate * row.qty

    # Bending
    bending_rate = _ZERO
    bending_cost = _ZERO
    if row.bend_num_bends:
        rate_key = _BEND_RATE_KEY.get(row.bend_num_bends, "1 Bend")
        bending_rate = norms.process_rates.get(rate_key, _ZERO)
        bending_cost = bending_rate * row.total_wt

    # Drilling
    drilling_rate = _ZERO
    drilling_cost = _ZERO
    if row.drill_hours:
        rate_key = _DRILLING_RATE_KEY.get(row.drill_type or "regular", "Drilling")
        drilling_rate = norms.process_rates.get(rate_key, _ZERO)
        drilling_cost = row.drill_hours * row.qty * drilling_rate

    # Rolling
    rolling_rate = _ZERO
    rolling_cost = _ZERO
    if row.has_rolling:
        rolling_rate = norms.process_rates.get("Rolling", _ZERO)
        rolling_cost = rolling_rate * row.total_wt

    row_total = (
        cutting_cost + machining_cost + bevelling_cost
        + bending_cost + drilling_cost + rolling_cost
    )

    return ProcessCostRowResult(
        cutting_cost=cutting_cost,
        machining_cost=machining_cost,
        bevelling_cost=bevelling_cost,
        bending_rate=bending_rate,
        bending_cost=bending_cost,
        drilling_rate=drilling_rate,
        drilling_cost=drilling_cost,
        rolling_rate=rolling_rate,
        rolling_cost=rolling_cost,
        row_total=row_total,
    )


def calculate_sheet(
    lines: list[CostingLineInput],
    line_ops_map: dict[int, list[LineOperationInput]],
    bo_items: list[BOLineItem],
    finishing_ops: list[FinishingOpInput],
    norms: NormsSnapshot,
    discount_pct: Decimal,
    transport_cost: Decimal,
    precomputed_line_process_costs: list[Decimal] | None = None,
) -> SheetCalcResult:
    """
    Full sheet-level calculation.

    lines           : ordered list of CostingLineInput (one per costing_line)
    line_ops_map    : maps list index → list of LineOperationInput for that line
    bo_items        : all BO items on this sheet
    finishing_ops   : all sheet-level finishing operations
    discount_pct    : sheet-level discount %
    transport_cost  : sheet-level transport cost (flat, not discounted)
    """
    # ── Per-line RM chain ────────────────────────────────────────────────────
    line_rm_results: list[RmLineResult] = []
    line_process_costs: list[Decimal] = []
    total_rm_cost = _ZERO
    total_part_weight = _ZERO

    for i, line in enumerate(lines):
        rm = calculate(line, norms)
        line_rm_results.append(rm)
        total_rm_cost     += rm.rm_cost
        total_part_weight += rm.total_part_weight

        if precomputed_line_process_costs is not None:
            pc = precomputed_line_process_costs[i]
        else:
            ops = line_ops_map.get(i, [])
            pc = calculate_process_cost_for_line(line, ops, norms)
        line_process_costs.append(pc)

    # ── BO block ─────────────────────────────────────────────────────────────
    total_bo_cost = calculate_bo_cost(bo_items)

    # ── Process block ─────────────────────────────────────────────────────────
    total_finishing_cost  = calculate_sheet_finishing_cost(finishing_ops, norms)
    total_process_cost    = sum(line_process_costs, _ZERO) + total_finishing_cost

    # ── Block markups ─────────────────────────────────────────────────────────
    rm_block      = calculate_block_markup(total_rm_cost,      "raw_material", norms)
    bo_block      = calculate_block_markup(total_bo_cost,      "bought_out",   norms)
    process_block = calculate_block_markup(total_process_cost, "process_cost", norms)

    # ── Final roll-up ─────────────────────────────────────────────────────────
    unit_price           = rm_block.grand_total + bo_block.grand_total + process_block.grand_total
    price_after_discount = unit_price * (Decimal("1") - discount_pct / _HUNDRED) + transport_cost
    bal_margin           = price_after_discount - (total_rm_cost + total_bo_cost)
    bal_margin_per_kg    = (
        bal_margin / total_part_weight if total_part_weight else _ZERO
    )

    return SheetCalcResult(
        line_rm_results     = line_rm_results,
        line_process_costs  = line_process_costs,
        total_rm_cost       = total_rm_cost,
        total_bo_cost       = total_bo_cost,
        total_process_cost  = total_process_cost,
        total_finishing_cost= total_finishing_cost,
        rm_block            = rm_block,
        bo_block            = bo_block,
        process_block       = process_block,
        unit_price          = unit_price,
        transport_cost      = transport_cost,
        discount_pct        = discount_pct,
        price_after_discount= price_after_discount,
        bal_margin          = bal_margin,
        bal_margin_per_kg   = bal_margin_per_kg,
        total_part_weight   = total_part_weight,
        norm_library_id    = norms.norm_library_id,
    )
