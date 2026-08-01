"""
Seed a norm library with TLD defaults.
Usage (from backend/ dir):
    python seed_library.py <library_id>
"""
import sys
from decimal import Decimal
from datetime import datetime, UTC

from app.database import SessionLocal
from app.models.norms import (
    NormLibrary, MaterialGrade, RmPriceBand, ScrapRate,
    ProcessRate, CostOverheadParam,
)

# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

# Thickness band → E250BR price (Rs/Kg)
# Source: RM_price_Mapping.xlsx actuals 2026-04-03
# Bands <10mm / 12mm / >12-19mm all fall in the "5-16mm" source range
RM_PRICES_E250BR = {
    "<10mm":     Decimal("62.5"),
    "12mm":      Decimal("62.5"),
    ">12-19mm":  Decimal("62.5"),
    "20mm":      Decimal("64.0"),
    ">20-40mm":  Decimal("65.4"),
    ">40-63mm":  Decimal("55.8"),   # stale — get fresh quote
    "80mm":      Decimal("73.75"),  # stale — get fresh quote
}

SCRAP_RATE    = Decimal("30.0")   # avg TLD + B7150DD
E350C_PREMIUM = Decimal("5.0")    # stored on the derived grade

# Process rates  [operation_name, unit, rate, group_label, sort_order]
# Process Loss % is handled per costing line (efficiency_pct), not here.
PROCESS_RATES = [
    # Material / Cutting
    ("Plasma Cutting",                  "Rs/mm/meter",    "3.0",    "Material / Cutting",   10),
    ("Laser Cutting",                   "Rs/mm/meter",    "5.5",    "Material / Cutting",   20),
    ("Bevelling",                       "Rs/slant/meter", "4.0",    "Material / Cutting",   30),
    # Forming
    ("1 Bend",                          "Rs/Kg",          "4.0",    "Forming",              10),
    ("2 Bend",                          "Rs/Kg",          "6.0",    "Forming",              20),
    ("3 Bend",                          "Rs/Kg",          "7.0",    "Forming",              30),
    ("Rolling",                         "Rs/Kg",          "5.0",    "Forming",              40),
    ("Channel Rolling",                 "Rs/Kg",          "11.7",   "Forming",              50),
    # Drilling
    ("Drilling",                        "Rs/Hr",          "200.0",  "Drilling",             10),
    ("Drilling (EH/Hiten)",             "Rs/Hr",          "350.0",  "Drilling",             20),
    ("Drilling (EHC450/EHC500)",        "Rs/Hr",          "500.0",  "Drilling",             30),
    # Welding / Finishing
    ("Tack Welding",                    "Rs/Hr",          "300.0",  "Welding / Finishing",  10),
    ("Full Welding (solid wire)",       "Rs/Kg",          "300.0",  "Welding / Finishing",  20),
    ("Dressing",                        "Rs/Hr",          "225.0",  "Welding / Finishing",  30),
    ("Sandering",                       "Rs/Hr",          "225.0",  "Welding / Finishing",  40),
    ("Gauging",                         "Rs/Hr",          "300.0",  "Welding / Finishing",  50),
    ("Preheating / Heat Correction",    "Rs/Hr",          "300.0",  "Welding / Finishing",  60),
    ("Straightening",                   "Rs/Kg",          "2.0",    "Welding / Finishing",  70),
    ("Stud Welding",                    "Rs/Nos",         "39.0",   "Welding / Finishing",  80),
    ("Hard Facing Charges",             "Rs/Kg",          "292.5",  "Welding / Finishing",  90),
    ("Hard Facing",                     "Rs/Kg",          "316.875","Welding / Finishing", 100),
    # Surface Treatment
    ("Shot Blasting",                   "Rs/Kg",          "1.75",   "Surface Treatment",    10),
    ("Zinc Plating",                    "Rs/Kg",          "30.0",   "Surface Treatment",    20),
    ("Final Painting (Primer + Final Coat)", "Rs/Sqm",   "575.0",  "Surface Treatment",    30),
    ("Galvanizing",                     "Rs/Kg",          "40.0",   "Surface Treatment",    40),
    ("Hardening",                       "Rs/Hr",          "195.0",  "Surface Treatment",    50),
    # Other
    ("Sub Transport",                   "Rs/Kg",          "2.5",    "Other",                10),
    ("Machining (VTL)",                 "Rs/Hr",          "500.0",  "Other",                20),
    ("Bush Fitting",                    "Rs/Nos",         "175.0",  "Other",                30),
]

# Overhead & Profit  [applies_to, param_name, value, sort_order]
OVERHEAD_PARAMS = [
    # Raw Material
    ("raw_material",  "Overhead",         "0.0",  10),
    ("raw_material",  "Rework",           "0.0",  20),
    ("raw_material",  "Inventory",        "2.5",  30),
    ("raw_material",  "Profit",           "10.0", 40),
    # Bought-Out Parts
    ("bought_out",    "Overhead",         "0.0",  10),
    ("bought_out",    "Inventory",        "2.5",  20),
    ("bought_out",    "Profit",           "5.0",  30),
    # Process Cost
    ("process_cost",  "Overhead",         "10.0", 10),
    ("process_cost",  "Rework",           "0.0",  20),
    ("process_cost",  "Profit",           "10.0", 30),
]

# ---------------------------------------------------------------------------
# Seed
# ---------------------------------------------------------------------------

def seed(library_id: int) -> None:
    db = SessionLocal()
    try:
        lib = db.get(NormLibrary, library_id)
        if not lib:
            print(f"ERROR: No library with id={library_id}")
            return

        print(f"Seeding library #{library_id}: '{lib.label}'")

        # ── RM Prices ──────────────────────────────────────────────────────
        e250br = db.query(MaterialGrade).filter_by(name="IS2062 E250BR").first()
        if not e250br:
            print("ERROR: Grade 'IS2062 E250BR' not found. Run migrations first.")
            return

        # Update E350C premium on the grade record
        e350c = db.query(MaterialGrade).filter_by(name="IS2062 E350C").first()
        if e350c:
            e350c.premium_amount = E350C_PREMIUM
            e350c.updated_at = datetime.now(UTC)

        # Upsert price bands for E250BR
        for band, price in RM_PRICES_E250BR.items():
            existing = (
                db.query(RmPriceBand)
                .filter_by(norm_library_id=library_id, grade_id=e250br.id, thickness_band=band)
                .first()
            )
            if existing:
                existing.price_per_kg = price
                existing.updated_at = datetime.now(UTC)
            else:
                db.add(RmPriceBand(
                    norm_library_id=library_id,
                    grade_id=e250br.id,
                    thickness_band=band,
                    price_per_kg=price,
                ))

        # Scrap rate
        scrap = db.query(ScrapRate).filter_by(norm_library_id=library_id).first()
        if scrap:
            scrap.rate_per_kg = SCRAP_RATE
            scrap.updated_at = datetime.now(UTC)
        else:
            db.add(ScrapRate(norm_library_id=library_id, rate_per_kg=SCRAP_RATE))

        print(f"  OK RM prices set ({len(RM_PRICES_E250BR)} bands)")

        # ── Process Rates ──────────────────────────────────────────────────
        # Clear existing rates for this library before re-seeding
        db.query(ProcessRate).filter_by(norm_library_id=library_id).delete()
        for (op_name, unit, rate, group, sort) in PROCESS_RATES:
            db.add(ProcessRate(
                norm_library_id=library_id,
                operation_name=op_name,
                unit=unit,
                rate=Decimal(rate),
                group_label=group,
                sort_order=sort,
            ))
        print(f"  OK {len(PROCESS_RATES)} process rates added")

        # ── Overhead Params ────────────────────────────────────────────────
        db.query(CostOverheadParam).filter_by(norm_library_id=library_id).delete()
        for (applies_to, param_name, value, sort) in OVERHEAD_PARAMS:
            db.add(CostOverheadParam(
                norm_library_id=library_id,
                applies_to=applies_to,
                param_name=param_name,
                param_value=Decimal(value),
                sort_order=sort,
            ))
        print(f"  OK {len(OVERHEAD_PARAMS)} overhead parameters added")

        db.commit()
        print(f"\nDone. Library #{library_id} is ready to publish.")
        print("Stale bands (get fresh quotes): >40-63mm (Rs55.8, Oct 2025), 80mm (Rs73.75, Jul 2024)")

    except Exception as e:
        db.rollback()
        print(f"ERROR: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python seed_library.py <library_id>")
        print("\nTo find the library ID, run:")
        print("  python -c \"from app.database import SessionLocal; from app.models.norms import NormLibrary; db=SessionLocal(); [print(l.id, l.label, l.client_id) for l in db.query(NormLibrary).all()]\"")
        sys.exit(1)
    seed(int(sys.argv[1]))
