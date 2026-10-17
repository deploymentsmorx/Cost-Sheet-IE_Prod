"""
Calculation engine tests — Phase 3 rewrite.

Section A  : Per-line RM chain tests (unchanged formulas, updated imports).
Section B  : New sheet-level function unit tests using synthetic norms.
Section C  : DB integration smoke test.
Section D  : Real-part tests from TLD_Costing Sheet "1".
             Fill in EXPECTED_* values with your Excel figures before enabling.
             Until then these tests are marked skip.

All Decimal assertions use tol() for ± tolerance at 2 d.p. unless noted.
"""
from __future__ import annotations

import os
from decimal import Decimal

import pytest
from dotenv import load_dotenv

from app.calc_engine import (
    BOLineItem,
    BlockMarkup,
    CostingLineInput,
    FinishingOpInput,
    LineOperationInput,
    NormsSnapshot,
    RmLineResult,
    calculate,
    calculate_block_markup,
    calculate_bo_cost,
    calculate_process_cost_for_line,
    calculate_sheet,
    calculate_sheet_finishing_cost,
)

load_dotenv()


# ---------------------------------------------------------------------------
# Shared synthetic NormsSnapshot — mirrors Phase 1 seed data exactly
# ---------------------------------------------------------------------------

SEED_NORMS = NormsSnapshot(
    norms_version_id=999,
    rm_prices={
        (1, "<10mm"):    Decimal("56.96"),
        (1, "12mm"):     Decimal("56.96"),
        (1, ">12-19mm"): Decimal("55.96"),
        (1, "20mm"):     Decimal("55.96"),
        (1, ">20-40mm"): Decimal("54.96"),
        (1, ">40-63mm"): Decimal("54.46"),
        (1, "80mm"):     Decimal("54.46"),
        (2, "<10mm"):    Decimal("78.00"),
        (2, "12mm"):     Decimal("78.00"),
        (2, ">12-19mm"): Decimal("77.00"),
        (2, "20mm"):     Decimal("77.00"),
        (2, ">20-40mm"): Decimal("76.00"),
        (2, ">40-63mm"): Decimal("75.50"),
        (2, "80mm"):     Decimal("75.50"),
    },
    grade_premiums={5: (1, Decimal("5.00"))},
    scrap_rate=Decimal("30.00"),
    process_loss_pct=Decimal("5"),
    process_rates={
        "PROCESS LOSS":               Decimal("5"),
        "CUTTING COST":               Decimal("0.15"),
        "LASER CUTTING":              Decimal("0.25"),
        "BEVELLING COST":             Decimal("120.00"),
        "1 BEND":                     Decimal("4.50"),
        "2 BEND":                     Decimal("7.00"),
        "3 BEND":                     Decimal("9.00"),
        "DRILLING":                   Decimal("350.00"),
        "DRILLING EH/HITEN":          Decimal("420.00"),
        "DRILLING EHC450/EHC500":     Decimal("480.00"),
        "ROLLING":                    Decimal("6.00"),
        "TACK WELDING":               Decimal("300.00"),
        "FULL WELDING solid wire":    Decimal("18.00"),
        "DRESSING":                   Decimal("280.00"),
        "SANDERING":                  Decimal("260.00"),
        "SHOT BLASTING":              Decimal("3.50"),
        "GAUGING":                    Decimal("320.00"),
        "PREHEATING/HEAT CORRECTION": Decimal("290.00"),
        "STRAIGHTENING":              Decimal("5.50"),
        "SUB TRANSPORT":              Decimal("2.00"),
        "MACHINING VTL":              Decimal("650.00"),
        "ZINC PLATING":               Decimal("12.00"),
        "FINAL PAINTING":             Decimal("85.00"),
        "BUSH FITTING":               Decimal("25.00"),
        "GALVANIZING":                Decimal("15.00"),
    },
    overhead_params={
        ("raw_material", "Overhead"):        Decimal("5"),
        ("raw_material", "Rework"):          Decimal("2"),
        ("raw_material", "Inventory Carry"): Decimal("1.5"),
        ("raw_material", "Profit"):          Decimal("10"),
        ("bought_out",   "Overhead"):        Decimal("3"),
        ("bought_out",   "Inventory Carry"): Decimal("1.5"),
        ("bought_out",   "Profit"):          Decimal("8"),
        ("process_cost", "Overhead"):        Decimal("8"),
        ("process_cost", "Rework"):          Decimal("2"),
        ("process_cost", "Profit"):          Decimal("12"),
    },
)


def d(s: str) -> Decimal:
    return Decimal(s)


def tol(result: Decimal, expected: Decimal, places: int = 2) -> bool:
    return abs(result - expected) < Decimal("0.5") * Decimal(10) ** (-places)


def line(
    grade_id: int = 1,
    band: str = ">12-19mm",
    part_weight: str = "9",
    qty: str = "1",
    eff: str = "90",
    thickness_mm: str = "0",
) -> CostingLineInput:
    return CostingLineInput(
        grade_id=grade_id,
        thickness_band=band,
        part_weight=d(part_weight),
        qty=d(qty),
        efficiency_pct=d(eff),
        thickness_mm=d(thickness_mm),
    )


# ---------------------------------------------------------------------------
# Section A — per-line RM chain (formulas unchanged from Phase 2)
# ---------------------------------------------------------------------------

class TestRmChain:

    def test_basic_rm(self):
        r = calculate(line(), SEED_NORMS)
        assert r.blank_rate == d("55.96")
        assert r.blank_weight == d("10")
        assert r.total_blank_weight == d("10")
        assert r.blank_cost == d("559.60")
        assert r.process_loss_pct == d("5")
        assert r.process_loss_weight == d("0.5")
        assert r.scrap_weight == d("0.5")
        assert r.scrap_cost == d("15.00")
        assert r.rm_cost == d("544.60")

    def test_e350c_premium(self):
        r = calculate(line(grade_id=5), SEED_NORMS)
        assert r.blank_rate == d("60.96")

    def test_scrap_formula(self):
        r = calculate(line(band=">20-40mm", part_weight="20", eff="80"), SEED_NORMS)
        assert tol(r.blank_weight, d("25"))
        assert tol(r.process_loss_weight, d("1.25"))
        assert tol(r.scrap_weight, d("3.75"))

    def test_known_example(self):
        """Hand-verified end-to-end for E250BR >12-19mm 9 kg qty=1 eff=90%."""
        r = calculate(line(), SEED_NORMS)
        assert tol(r.rm_cost, d("544.60"))
        assert r.norms_version_id == 999


# ---------------------------------------------------------------------------
# Section B — new sheet-level functions
# ---------------------------------------------------------------------------

class TestBoCost:

    def test_empty(self):
        assert calculate_bo_cost([]) == d("0")

    def test_single_item(self):
        items = [BOLineItem("bolt", d("10"), d("5.50"))]
        # 10 * 5.50 = 55.00
        assert calculate_bo_cost(items) == d("55.00")

    def test_multiple_items(self):
        items = [
            BOLineItem("nut M16",  d("4"),  d("8.00")),   # 32.00
            BOLineItem("washer",   d("4"),  d("2.50")),   # 10.00
            BOLineItem("bolt M20", d("2"), d("15.00")),   # 30.00
        ]
        assert calculate_bo_cost(items) == d("72.00")


class TestProcessCostForLine:

    def test_cutting(self):
        # length_mm=500, thickness_mm=10, qty=2, rate=0.15
        # (500/1000) * 10 * 2 * 0.15 = 0.5 * 10 * 2 * 0.15 = 1.50
        ln = line(thickness_mm="10", qty="2")
        ops = [LineOperationInput("cutting", {"length_mm": 500})]
        assert tol(calculate_process_cost_for_line(ln, ops, SEED_NORMS), d("1.50"))

    def test_laser_cutting(self):
        # (300/1000) * 8 * 1 * 0.25 = 0.3 * 8 * 0.25 = 0.60
        ln = line(thickness_mm="8", qty="1")
        ops = [LineOperationInput("laser_cutting", {"length_mm": 300})]
        assert tol(calculate_process_cost_for_line(ln, ops, SEED_NORMS), d("0.60"))

    def test_machining_norms_rate(self):
        # hours=2, rate=650, qty=3  → 2 * 650 * 3 = 3900
        ln = line(qty="3")
        ops = [LineOperationInput("machining", {"hours": 2, "custom_rate": None})]
        assert tol(calculate_process_cost_for_line(ln, ops, SEED_NORMS), d("3900.00"))

    def test_machining_custom_rate(self):
        # hours=1, custom_rate=800, qty=1  → 800
        ln = line(qty="1")
        ops = [LineOperationInput("machining", {"hours": 1, "custom_rate": 800})]
        assert tol(calculate_process_cost_for_line(ln, ops, SEED_NORMS), d("800.00"))

    def test_bevelling_single_slant(self):
        # slant_length=2000mm, num_slants=1, qty=1, rate=120
        # (2000/1000) * 1 * 120 * 1 = 240.00
        ln = line(qty="1")
        ops = [LineOperationInput("bevelling", {"slant_length_mm": 2000, "num_slants": 1})]
        assert tol(calculate_process_cost_for_line(ln, ops, SEED_NORMS), d("240.00"))

    def test_bevelling_two_slants(self):
        # (1000/1000) * 2 * 120 * 1 = 240.00
        ln = line(qty="1")
        ops = [LineOperationInput("bevelling", {"slant_length_mm": 1000, "num_slants": 2})]
        assert tol(calculate_process_cost_for_line(ln, ops, SEED_NORMS), d("240.00"))

    def test_bending_1_bend(self):
        # total_part_weight = 5 * 2 = 10 kg; rate for "1 BEND" = 4.50
        # cost = 10 * 4.50 = 45.00
        ln = line(part_weight="5", qty="2")
        ops = [LineOperationInput("bending", {"num_bends": 1})]
        assert tol(calculate_process_cost_for_line(ln, ops, SEED_NORMS), d("45.00"))

    def test_bending_2_bends(self):
        # total_part_weight = 5 * 2 = 10; rate "2 BEND" = 7.00 → 70.00
        ln = line(part_weight="5", qty="2")
        ops = [LineOperationInput("bending", {"num_bends": 2})]
        assert tol(calculate_process_cost_for_line(ln, ops, SEED_NORMS), d("70.00"))

    def test_bending_3_bends(self):
        # 10 * 9.00 = 90.00
        ln = line(part_weight="5", qty="2")
        ops = [LineOperationInput("bending", {"num_bends": 3})]
        assert tol(calculate_process_cost_for_line(ln, ops, SEED_NORMS), d("90.00"))

    def test_drilling_regular(self):
        # hours=0.5, qty=4, rate=350 → 0.5 * 4 * 350 = 700
        ln = line(qty="4")
        ops = [LineOperationInput("drilling", {"hole_spec": "Dia 7", "hours": 0.5, "drilling_type": "regular"})]
        assert tol(calculate_process_cost_for_line(ln, ops, SEED_NORMS), d("700.00"))

    def test_drilling_eh_hiten(self):
        # hours=1, qty=2, rate=420 → 840
        ln = line(qty="2")
        ops = [LineOperationInput("drilling", {"hole_spec": "M6", "hours": 1, "drilling_type": "eh_hiten"})]
        assert tol(calculate_process_cost_for_line(ln, ops, SEED_NORMS), d("840.00"))

    def test_drilling_ehc450_500(self):
        # hours=2, qty=1, rate=480 → 960
        ln = line(qty="1")
        ops = [LineOperationInput("drilling", {"hole_spec": "M16", "hours": 2, "drilling_type": "ehc450_500"})]
        assert tol(calculate_process_cost_for_line(ln, ops, SEED_NORMS), d("960.00"))

    def test_rolling(self):
        # total_part_weight = 8 * 3 = 24; rate=6 → 144
        ln = line(part_weight="8", qty="3")
        ops = [LineOperationInput("rolling", {})]
        assert tol(calculate_process_cost_for_line(ln, ops, SEED_NORMS), d("144.00"))

    def test_multiple_ops_sum(self):
        # cutting: (400/1000)*5*1*0.15 = 0.30
        # bending 1 bend: 6*1*4.50 = 27.00
        # total = 27.30
        ln = line(part_weight="6", qty="1", thickness_mm="5")
        ops = [
            LineOperationInput("cutting", {"length_mm": 400}),
            LineOperationInput("bending", {"num_bends": 1}),
        ]
        assert tol(calculate_process_cost_for_line(ln, ops, SEED_NORMS), d("27.30"))

    def test_no_ops_returns_zero(self):
        assert calculate_process_cost_for_line(line(), [], SEED_NORMS) == d("0")


class TestSheetFinishingCost:

    def test_zinc_plating(self):
        # 10 kg * 12 Rs/Kg = 120
        ops = [FinishingOpInput("ZINC PLATING", d("10"))]
        assert tol(calculate_sheet_finishing_cost(ops, SEED_NORMS), d("120.00"))

    def test_final_painting(self):
        # 2 Sqm * 85 = 170
        ops = [FinishingOpInput("FINAL PAINTING", d("2"))]
        assert tol(calculate_sheet_finishing_cost(ops, SEED_NORMS), d("170.00"))

    def test_multiple_finishing(self):
        # shot blasting 20kg*3.5=70, bush fitting 5nos*25=125 → 195
        ops = [
            FinishingOpInput("SHOT BLASTING", d("20")),
            FinishingOpInput("BUSH FITTING",  d("5")),
        ]
        assert tol(calculate_sheet_finishing_cost(ops, SEED_NORMS), d("195.00"))

    def test_unknown_op_returns_zero(self):
        ops = [FinishingOpInput("MYSTERY OP", d("10"))]
        assert calculate_sheet_finishing_cost(ops, SEED_NORMS) == d("0")

    def test_empty(self):
        assert calculate_sheet_finishing_cost([], SEED_NORMS) == d("0")


class TestBlockMarkup:

    def test_rm_block_all_four_markups(self):
        # base=1000; overhead=50, rework=20, inventory=15, profit=100 → grand=1185
        bm = calculate_block_markup(d("1000"), "raw_material", SEED_NORMS)
        assert tol(bm.overhead,   d("50.00"))
        assert tol(bm.rework,     d("20.00"))
        assert tol(bm.inventory,  d("15.00"))
        assert tol(bm.profit,     d("100.00"))
        assert tol(bm.grand_total, d("1185.00"))

    def test_bo_block_no_rework(self):
        # base=500; overhead=15, inventory=7.5, profit=40 → grand=562.50
        bm = calculate_block_markup(d("500"), "bought_out", SEED_NORMS)
        assert tol(bm.overhead,   d("15.00"))
        assert bm.rework == d("0")
        assert tol(bm.inventory,  d("7.50"))
        assert tol(bm.profit,     d("40.00"))
        assert tol(bm.grand_total, d("562.50"))

    def test_process_block_no_inventory(self):
        # base=200; overhead=16, rework=4, profit=24 → grand=244
        bm = calculate_block_markup(d("200"), "process_cost", SEED_NORMS)
        assert tol(bm.overhead,   d("16.00"))
        assert tol(bm.rework,     d("4.00"))
        assert bm.inventory == d("0")
        assert tol(bm.profit,     d("24.00"))
        assert tol(bm.grand_total, d("244.00"))

    def test_zero_base(self):
        bm = calculate_block_markup(d("0"), "raw_material", SEED_NORMS)
        assert bm.grand_total == d("0")


class TestCalculateSheet:
    """End-to-end sheet calc with two RM lines, BO items, and finishing ops."""

    def _run(self):
        # Line 0: E250BR >12-19mm, 9 kg, qty=1, eff=90%, thickness=15mm
        #         cutting 500mm + 1 bend
        # Line 1: E250BR <10mm, 5 kg, qty=2, eff=95%, thickness=8mm
        #         no process ops
        lines = [
            CostingLineInput(1, ">12-19mm", d("9"), d("1"), d("90"), d("15")),
            CostingLineInput(1, "<10mm",    d("5"), d("2"), d("95"), d("8")),
        ]
        line_ops_map = {
            0: [
                LineOperationInput("cutting", {"length_mm": 500}),
                LineOperationInput("bending", {"num_bends": 1}),
            ],
            1: [],
        }
        bo_items = [
            BOLineItem("nut M16", d("4"), d("8.00")),   # 32.00
        ]
        finishing_ops = [
            FinishingOpInput("SHOT BLASTING", d("19")),  # 19*3.5=66.50
        ]
        return calculate_sheet(
            lines, line_ops_map, bo_items, finishing_ops, SEED_NORMS,
            discount_pct=d("5"), transport_cost=d("100"),
        )

    def test_total_rm_cost(self):
        r = self._run()
        # Line 0 rm_cost: 9/(90/100)=10; blank_cost=10*55.96=559.60; pl=0.5kg; scrap=0.5*30=15; rm=544.60
        # Line 1 rm_cost: 5/(95/100)=5.2632...; bw*2=10.5263...; bc=10.5263*56.96=599.578...
        #                 pl=10.5263*0.05=0.5263; scrap=(10.5263-10-0.5263)*30=0; rm≈bc-scrap
        r0_rm = calculate(lines := CostingLineInput(1, ">12-19mm", d("9"), d("1"), d("90"), d("15")), SEED_NORMS).rm_cost
        r1_rm = calculate(CostingLineInput(1, "<10mm", d("5"), d("2"), d("95"), d("8")), SEED_NORMS).rm_cost
        assert tol(r.total_rm_cost, r0_rm + r1_rm)

    def test_total_bo_cost(self):
        r = self._run()
        assert tol(r.total_bo_cost, d("32.00"))

    def test_finishing_cost(self):
        r = self._run()
        assert tol(r.total_finishing_cost, d("66.50"))

    def test_block_markup_consistency(self):
        r = self._run()
        assert tol(r.rm_block.grand_total,
                   r.total_rm_cost * d("1.185"))  # 5+2+1.5+10 = 18.5%
        assert tol(r.bo_block.grand_total,
                   r.total_bo_cost * d("1.125"))   # 3+1.5+8 = 12.5%
        assert tol(r.process_block.grand_total,
                   r.total_process_cost * d("1.22"))  # 8+2+12 = 22%

    def test_unit_price_is_sum_of_grand_totals(self):
        r = self._run()
        assert tol(r.unit_price,
                   r.rm_block.grand_total + r.bo_block.grand_total + r.process_block.grand_total)

    def test_price_after_discount_formula(self):
        r = self._run()
        # price = unit_price * (1 - 5/100) + 100
        expected = r.unit_price * d("0.95") + d("100")
        assert tol(r.price_after_discount, expected)

    def test_bal_margin_formula(self):
        r = self._run()
        expected = r.price_after_discount - (r.total_rm_cost + r.total_bo_cost)
        assert tol(r.bal_margin, expected)

    def test_bal_margin_per_kg(self):
        r = self._run()
        # total_part_weight = 9*1 + 5*2 = 19
        assert tol(r.total_part_weight, d("19"))
        assert tol(r.bal_margin_per_kg, r.bal_margin / d("19"))

    def test_norms_version_propagated(self):
        r = self._run()
        assert r.norms_version_id == 999


# ---------------------------------------------------------------------------
# Section C — DB integration smoke test
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_loader_and_engine_against_db():
    """Load current norms from DATABASE_URL and run a basic sheet calculation."""
    from app.database import SessionLocal
    from app.norms_loader import load_norms_snapshot

    db = SessionLocal()
    try:
        snap = load_norms_snapshot(db)  # no client_id: falls back to any is_current version (integration only)
        assert snap.scrap_rate > 0
        assert len(snap.rm_prices) > 0
        assert len(snap.overhead_params) >= 9  # 4 RM + 3 BO + 3 Process (at minimum)

        grade_id, band = next(iter(snap.rm_prices.keys()))
        ln = CostingLineInput(grade_id, band, d("10"), d("1"), d("90"), d("10"))
        r = calculate(ln, snap)
        assert r.rm_cost > 0

        sheet_r = calculate_sheet(
            lines=[ln],
            line_ops_map={},
            bo_items=[],
            finishing_ops=[],
            norms=snap,
            discount_pct=d("0"),
            transport_cost=d("0"),
        )
        assert sheet_r.unit_price > 0
        assert sheet_r.norms_version_id == snap.norms_version_id
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Section D — Real-part tests from TLD_Costing Sheet "1"
#
# HOW TO FILL IN:
#   1. For each RM costing_line, provide: grade_id, thickness_band, part_weight,
#      qty, efficiency_pct, thickness_mm.
#   2. For each line's process operations, provide: operation_type + input_data.
#   3. For BO items: description, qty, unit_price.
#   4. For finishing ops: operation_name, input_qty.
#   5. Sheet-level: discount_pct, transport_cost.
#   6. Expected outputs: total_rm_cost, total_bo_cost, total_process_cost,
#      rm_grand_total, bo_grand_total, process_grand_total,
#      unit_price, price_after_discount, bal_margin.
# ---------------------------------------------------------------------------

@pytest.mark.skip(reason="Fill in TLD_Costing Sheet 1 figures before enabling")
def test_tld_sheet1_full():
    lines = [
        # CostingLineInput(grade_id=?, band=?, part_weight=?, qty=?, eff=?, thickness_mm=?),
    ]
    line_ops_map: dict[int, list[LineOperationInput]] = {
        # 0: [LineOperationInput("cutting", {"length_mm": ?}), ...],
    }
    bo_items = [
        # BOLineItem("Ecrou 8.8 M16 self nut", qty=?, unit_price=?),
    ]
    finishing_ops = [
        # FinishingOpInput("ZINC PLATING", input_qty=?),
    ]

    r = calculate_sheet(
        lines, line_ops_map, bo_items, finishing_ops, SEED_NORMS,
        discount_pct=d("REPLACE"),
        transport_cost=d("REPLACE"),
    )

    assert tol(r.total_rm_cost,       d("REPLACE"))
    assert tol(r.total_bo_cost,       d("REPLACE"))
    assert tol(r.total_process_cost,  d("REPLACE"))
    assert tol(r.rm_block.grand_total,      d("REPLACE"))
    assert tol(r.bo_block.grand_total,      d("REPLACE"))
    assert tol(r.process_block.grand_total, d("REPLACE"))
    assert tol(r.unit_price,          d("REPLACE"))
    assert tol(r.price_after_discount,d("REPLACE"))
    assert tol(r.bal_margin,          d("REPLACE"))
