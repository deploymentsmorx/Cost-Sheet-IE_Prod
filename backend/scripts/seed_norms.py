"""
Seed script: loads the canonical "v4.5 (seed)" norms version.
Run from /backend:  python -m scripts.seed_norms
"""
from __future__ import annotations

import os
import sys
from datetime import date
from decimal import Decimal

# Allow running from /backend or project root
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv

load_dotenv()

from sqlalchemy.orm import Session  # noqa: E402

from app.database import SessionLocal  # noqa: E402
from app.models.norms import (  # noqa: E402
    CostOverheadParam,
    MaterialGrade,
    NormsVersion,
    ProcessRate,
    RmPriceBand,
    ScrapRate,
)

# ---------------------------------------------------------------------------
# Seed data
# ---------------------------------------------------------------------------

THICKNESS_BANDS = ["<10mm", "12mm", ">12-19mm", "20mm", ">20-40mm", ">40-63mm", "80mm"]

# Grades that have their own direct prices
# grade_name -> {thickness_band -> price_per_kg}
# Source: "IS2062 E250BR" is the base. "IS2062 E350C" is derived (E250BR + premium).
# We store E350C in material_grades with base_grade_id pointing to E250BR.
# The RM price rows for E350C are NOT stored; the API/UI computes them dynamically.
# Only base-priced grades get rm_price_bands rows.

GRADE_PRICES: dict[str, dict[str, Decimal]] = {
    "IS2062 E250BR": {
        "<10mm":    Decimal("56.96"),
        "12mm":     Decimal("56.96"),
        ">12-19mm": Decimal("55.96"),
        "20mm":     Decimal("55.96"),
        ">20-40mm": Decimal("54.96"),
        ">40-63mm": Decimal("54.46"),
        "80mm":     Decimal("54.46"),
    },
    "En8D": {
        "<10mm":    Decimal("78.00"),
        "12mm":     Decimal("78.00"),
        ">12-19mm": Decimal("77.00"),
        "20mm":     Decimal("77.00"),
        ">20-40mm": Decimal("76.00"),
        ">40-63mm": Decimal("75.50"),
        "80mm":     Decimal("75.50"),
    },
    "Yst240": {
        "<10mm":    Decimal("62.00"),
        "12mm":     Decimal("62.00"),
        ">12-19mm": Decimal("61.00"),
        "20mm":     Decimal("61.00"),
        ">20-40mm": Decimal("60.00"),
        ">40-63mm": Decimal("59.50"),
        "80mm":     Decimal("59.50"),
    },
    "ASTM A106 Gr B": {
        "<10mm":    Decimal("95.00"),
        "12mm":     Decimal("95.00"),
        ">12-19mm": Decimal("94.00"),
        "20mm":     Decimal("94.00"),
        ">20-40mm": Decimal("93.00"),
        ">40-63mm": Decimal("92.50"),
        "80mm":     Decimal("92.50"),
    },
}

# IS2062 E350C = E250BR + this premium (Rs/Kg)
E350C_PREMIUM = Decimal("5.00")

SCRAP_RATE = Decimal("30.00")  # Rs/Kg

# (operation_name, unit, rate, sort_order)
PROCESS_RATES: list[tuple[str, str, Decimal, int]] = [
    ("PROCESS LOSS",                         "%",               Decimal("5.00"),   1),
    ("CUTTING COST",                         "Rs/mm/meter",     Decimal("0.15"),   2),
    ("LASER CUTTING",                        "Rs/mm/meter",     Decimal("0.25"),   3),
    ("BEVELLING COST",                       "Rs/slant/meter",  Decimal("120.00"), 4),
    ("1 BEND",                               "Rs/Kg",           Decimal("4.50"),   5),
    ("2 BEND",                               "Rs/Kg",           Decimal("7.00"),   6),
    ("3 BEND",                               "Rs/Kg",           Decimal("9.00"),   7),
    ("DRILLING",                             "Rs/Hr",           Decimal("350.00"), 8),
    ("DRILLING EH/HITEN",                    "Rs/Hr",           Decimal("420.00"), 9),
    ("DRILLING EHC450/EHC500",               "Rs/Hr",           Decimal("480.00"), 10),
    ("ROLLING",                              "Rs/Kg",           Decimal("6.00"),   11),
    ("TACK WELDING",                         "Rs/Hr",           Decimal("300.00"), 12),
    ("FULL WELDING solid wire",              "Rs/Kg",           Decimal("18.00"),  13),
    ("DRESSING",                             "Rs/Hr",           Decimal("280.00"), 14),
    ("SANDERING",                            "Rs/Hr",           Decimal("260.00"), 15),
    ("SHOT BLASTING",                        "Rs/Kg",           Decimal("3.50"),   16),
    ("GAUGING",                              "Rs/Hr",           Decimal("320.00"), 17),
    ("PREHEATING/HEAT CORRECTION",           "Rs/Hr",           Decimal("290.00"), 18),
    ("STRAIGHTENING",                        "Rs/Kg",           Decimal("5.50"),   19),
    ("SUB TRANSPORT",                        "Rs/Kg",           Decimal("2.00"),   20),
    ("MACHINING VTL",                        "Rs/Hr",           Decimal("650.00"), 21),
    ("ZINC PLATING",                         "Rs/Kg",           Decimal("12.00"),  22),
    ("FINAL PAINTING",                       "Rs/Sqm",          Decimal("85.00"),  23),
    ("BUSH FITTING",                         "Rs/Nos",          Decimal("25.00"),  24),
    ("GALVANIZING",                          "Rs/Kg",           Decimal("15.00"),  25),
]

# (applies_to, overhead_pct, rework_pct, inventory_carry_pct, profit_pct)
OVERHEAD_PARAMS: list[tuple[str, Decimal | None, Decimal | None, Decimal | None, Decimal | None]] = [
    ("raw_material", Decimal("5.00"),  Decimal("2.00"),  Decimal("1.50"),  Decimal("10.00")),
    ("bought_out",   Decimal("3.00"),  None,             Decimal("1.50"),  Decimal("8.00")),
    ("process_cost", Decimal("8.00"),  Decimal("2.00"),  None,             Decimal("12.00")),
]


# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------

def seed(db: Session) -> None:
    existing = db.query(NormsVersion).filter_by(label="v4.5 (seed)").first()
    if existing:
        print("Seed version 'v4.5 (seed)' already exists — skipping.")
        return

    # Demote any existing current version
    db.query(NormsVersion).filter_by(is_current=True).update({"is_current": False})

    version = NormsVersion(
        label="v4.5 (seed)",
        effective_date=date(2024, 5, 1),
        is_current=True,
    )
    db.add(version)
    db.flush()

    # --- Material grades ---
    grade_map: dict[str, MaterialGrade] = {}
    for name in list(GRADE_PRICES.keys()):
        g = MaterialGrade(name=name)
        db.add(g)
        db.flush()
        grade_map[name] = g

    e250br = grade_map["IS2062 E250BR"]
    e350c = MaterialGrade(name="IS2062 E350C", base_grade_id=e250br.id, premium_amount=E350C_PREMIUM)
    db.add(e350c)
    db.flush()
    grade_map["IS2062 E350C"] = e350c

    # --- RM price bands (only for base-priced grades) ---
    for grade_name, band_prices in GRADE_PRICES.items():
        grade = grade_map[grade_name]
        for band in THICKNESS_BANDS:
            price = band_prices[band]
            db.add(RmPriceBand(
                norms_version_id=version.id,
                grade_id=grade.id,
                thickness_band=band,
                price_per_kg=price,
            ))

    # --- Scrap rate ---
    db.add(ScrapRate(norms_version_id=version.id, rate_per_kg=SCRAP_RATE))

    # --- Process rates ---
    for op_name, unit, rate, sort_order in PROCESS_RATES:
        db.add(ProcessRate(
            norms_version_id=version.id,
            operation_name=op_name,
            unit=unit,
            rate=rate,
            sort_order=sort_order,
        ))

    # --- Overhead params ---
    for applies_to, overhead, rework, inv_carry, profit in OVERHEAD_PARAMS:
        db.add(CostOverheadParam(
            norms_version_id=version.id,
            applies_to=applies_to,
            overhead_pct=overhead,
            rework_pct=rework,
            inventory_carry_pct=inv_carry,
            profit_pct=profit,
        ))

    db.commit()
    print(f"Seeded norms version: '{version.label}' (id={version.id}, is_current=True)")
    print(f"  Grades: {list(grade_map.keys())}")
    print(f"  RM price bands: {len(GRADE_PRICES) * len(THICKNESS_BANDS)} rows")
    print(f"  Process rates: {len(PROCESS_RATES)} rows")
    print(f"  Overhead param rows: {len(OVERHEAD_PARAMS)}")
    print(f"  Scrap rate: Rs {SCRAP_RATE}/Kg")


if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed(db)
    finally:
        db.close()
