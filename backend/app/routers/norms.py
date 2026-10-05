from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.norms import (
    BoughtOutCatalogItem,
    CostOverheadParam,
    GradeEquivalence,
    MaterialGrade,
    NormLibrary,
    ProcessRate,
    RmPriceBand,
    ScrapRate,
    SectionCatalogItem,
    SteelPriceBuildUp,
)
from app.schemas.norms import (
    AddGradeRequest,
    AddOverheadParamRequest,
    AddProcessRateRequest,
    BoughtOutCatalogItemCreate,
    BoughtOutCatalogItemOut,
    BoughtOutCatalogItemUpdate,
    CostOverheadParamOut,
    CreateLibraryRequest,
    GradeEquivalenceCreate,
    GradeEquivalenceOut,
    GradeEquivalenceResolveOut,
    GradeEquivalenceUpdate,
    MaterialGradeOut,
    NormsLookup,
    NormLibraryDetail,
    NormLibrarySummary,
    OverheadParamsBulkUpdate,
    ProcessRateOut,
    ProcessRatesBulkUpdate,
    RmPriceBandOut,
    RmPricesBulkUpdate,
    RmPriceTrendPoint,
    ScrapRateOut,
    SectionCatalogItemCreate,
    SectionCatalogItemOut,
    SectionCatalogItemUpdate,
    SteelPriceBuildUpCreate,
    SteelPriceBuildUpOut,
    SteelPriceBuildUpUpdate,
)

router = APIRouter(prefix="/api/v1/norms", tags=["norms"])

THICKNESS_BANDS = ["<10mm", "12mm", ">12-19mm", "20mm", ">20-40mm", ">40-63mm", "80mm"]

# Default seed data (TLD, 2026-04-03)
_SEED_RM_E250BR = {
    "<10mm": Decimal("62.5"), "12mm": Decimal("62.5"), ">12-19mm": Decimal("62.5"),
    "20mm": Decimal("64.0"), ">20-40mm": Decimal("65.4"),
    ">40-63mm": Decimal("55.8"), "80mm": Decimal("73.75"),
}
_SEED_SCRAP = Decimal("30.0")
_SEED_E350C_PREMIUM = Decimal("5.0")
_SEED_PROCESS_RATES = [
    # norms_loader.py resolves process_loss_pct by matching operation_name == "Process Loss"
    # (case-insensitive) — this row must always exist or RM scrap/process-loss math silently
    # computes as 0%.
    ("Process Loss",                 "%",              Decimal("5.0"),      "Material / Cutting",   1),
    ("Plasma Cutting",               "Rs/mm/meter",    Decimal("3.0"),      "Material / Cutting",  10),
    ("Laser Cutting",                "Rs/mm/meter",    Decimal("5.5"),      "Material / Cutting",  20),
    ("Bevelling",                    "Rs/slant/meter", Decimal("4.0"),      "Material / Cutting",  30),
    ("1 Bend",                       "Rs/Kg",          Decimal("4.0"),      "Forming",             10),
    ("2 Bend",                       "Rs/Kg",          Decimal("6.0"),      "Forming",             20),
    ("3 Bend",                       "Rs/Kg",          Decimal("7.0"),      "Forming",             30),
    ("Rolling",                      "Rs/Kg",          Decimal("5.0"),      "Forming",             40),
    ("Channel Rolling",              "Rs/Kg",          Decimal("11.7"),     "Forming",             50),
    ("Drilling",                     "Rs/Hr",          Decimal("200.0"),    "Drilling",            10),
    ("Drilling (EH/Hiten)",          "Rs/Hr",          Decimal("350.0"),    "Drilling",            20),
    ("Drilling (EHC450/EHC500)",     "Rs/Hr",          Decimal("500.0"),    "Drilling",            30),
    ("Tack Welding",                 "Rs/Hr",          Decimal("300.0"),    "Welding / Finishing", 10),
    ("Full Welding (solid wire)",    "Rs/Kg",          Decimal("300.0"),    "Welding / Finishing", 20),
    ("Dressing",                     "Rs/Hr",          Decimal("225.0"),    "Welding / Finishing", 30),
    ("Sandering",                    "Rs/Hr",          Decimal("225.0"),    "Welding / Finishing", 40),
    ("Gauging",                      "Rs/Hr",          Decimal("300.0"),    "Welding / Finishing", 50),
    ("Preheating / Heat Correction", "Rs/Hr",          Decimal("300.0"),    "Welding / Finishing", 60),
    ("Straightening",                "Rs/Kg",          Decimal("2.0"),      "Welding / Finishing", 70),
    ("Stud Welding",                 "Rs/Nos",         Decimal("39.0"),     "Welding / Finishing", 80),
    ("Hard Facing Charges",          "Rs/Kg",          Decimal("292.5"),    "Welding / Finishing", 90),
    ("Hard Facing",                  "Rs/Kg",          Decimal("316.875"),  "Welding / Finishing",100),
    ("Shot Blasting",                "Rs/Kg",          Decimal("1.75"),     "Surface Treatment",   10),
    ("Zinc Plating",                 "Rs/Kg",          Decimal("30.0"),     "Surface Treatment",   20),
    ("Final Painting (Primer + Final Coat)", "Rs/Sqm", Decimal("575.0"),   "Surface Treatment",   30),
    ("Galvanizing",                  "Rs/Kg",          Decimal("40.0"),     "Surface Treatment",   40),
    ("Hardening",                    "Rs/Hr",          Decimal("195.0"),    "Surface Treatment",   50),
    ("Sub Transport",                "Rs/Kg",          Decimal("2.5"),      "Other",               10),
    ("Machining (VTL)",              "Rs/Hr",          Decimal("500.0"),    "Other",               20),
    ("Bush Fitting",                 "Rs/Nos",         Decimal("175.0"),    "Other",               30),
]
_SEED_OVERHEAD = [
    ("raw_material", "Overhead",  Decimal("0.0"),  10),
    ("raw_material", "Rework",    Decimal("0.0"),  20),
    ("raw_material", "Inventory", Decimal("2.5"),  30),
    ("raw_material", "Profit",    Decimal("10.0"), 40),
    ("bought_out",   "Overhead",  Decimal("0.0"),  10),
    ("bought_out",   "Inventory", Decimal("2.5"),  20),
    ("bought_out",   "Profit",    Decimal("5.0"),  30),
    ("process_cost", "Overhead",  Decimal("10.0"), 10),
    ("process_cost", "Rework",    Decimal("0.0"),  20),
    ("process_cost", "Profit",    Decimal("10.0"), 30),
]


def _seed_library_defaults(library_id: int, db: Session) -> None:
    e250br = db.query(MaterialGrade).filter_by(name="IS2062 E250BR").first()
    if not e250br:
        return
    e350c = db.query(MaterialGrade).filter_by(name="IS2062 E350C").first()
    if e350c:
        e350c.premium_amount = _SEED_E350C_PREMIUM

    for band, price in _SEED_RM_E250BR.items():
        existing = db.query(RmPriceBand).filter_by(
            norm_library_id=library_id, grade_id=e250br.id, thickness_band=band
        ).first()
        if existing:
            existing.price_per_kg = price
        else:
            db.add(RmPriceBand(norm_library_id=library_id, grade_id=e250br.id,
                               thickness_band=band, price_per_kg=price))

    scrap = db.query(ScrapRate).filter_by(norm_library_id=library_id).first()
    if scrap:
        scrap.rate_per_kg = _SEED_SCRAP
    else:
        db.add(ScrapRate(norm_library_id=library_id, rate_per_kg=_SEED_SCRAP))

    db.query(ProcessRate).filter_by(norm_library_id=library_id).delete()
    for (op, unit, rate, group, sort) in _SEED_PROCESS_RATES:
        db.add(ProcessRate(norm_library_id=library_id, operation_name=op,
                           unit=unit, rate=rate, group_label=group, sort_order=sort))

    db.query(CostOverheadParam).filter_by(norm_library_id=library_id).delete()
    for (applies_to, name, value, sort) in _SEED_OVERHEAD:
        db.add(CostOverheadParam(norm_library_id=library_id, applies_to=applies_to,
                                 param_name=name, param_value=value, sort_order=sort))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_library_or_404(library_id: int, db: Session) -> NormLibrary:
    lib = db.get(NormLibrary, library_id)
    if not lib:
        raise HTTPException(status_code=404, detail=f"Norm library {library_id} not found")
    return lib


def _assert_editable(lib: NormLibrary) -> None:
    if not lib.is_current and not lib.is_draft:
        raise HTTPException(
            status_code=409,
            detail=(
                f"Library '{lib.label}' is a historical version and cannot be edited. "
                "Duplicate it to create a new draft."
            ),
        )


def _build_detail(library_id: int, db: Session) -> NormLibraryDetail:
    lib = _get_library_or_404(library_id, db)
    grades = db.query(MaterialGrade).order_by(MaterialGrade.id).all()
    price_bands = (
        db.query(RmPriceBand)
        .filter_by(norm_library_id=library_id)
        .order_by(RmPriceBand.grade_id, RmPriceBand.id)
        .all()
    )
    scrap = db.query(ScrapRate).filter_by(norm_library_id=library_id).first()
    process_rates = (
        db.query(ProcessRate)
        .filter_by(norm_library_id=library_id)
        .order_by(ProcessRate.group_label, ProcessRate.sort_order)
        .all()
    )
    overhead = (
        db.query(CostOverheadParam)
        .filter_by(norm_library_id=library_id)
        .order_by(CostOverheadParam.applies_to, CostOverheadParam.sort_order)
        .all()
    )
    steel_buildups = (
        db.query(SteelPriceBuildUp).filter_by(norm_library_id=library_id)
        .order_by(SteelPriceBuildUp.grade_id, SteelPriceBuildUp.thickness_band).all()
    )
    grade_equivs = (
        db.query(GradeEquivalence).filter_by(norm_library_id=library_id)
        .order_by(GradeEquivalence.customer_spec).all()
    )
    section_items = (
        db.query(SectionCatalogItem).filter_by(norm_library_id=library_id)
        .order_by(SectionCatalogItem.category, SectionCatalogItem.designation).all()
    )
    bo_items = (
        db.query(BoughtOutCatalogItem).filter_by(norm_library_id=library_id)
        .order_by(BoughtOutCatalogItem.name).all()
    )
    return NormLibraryDetail(
        library=NormLibrarySummary.model_validate(lib),
        material_grades=[MaterialGradeOut.model_validate(g) for g in grades],
        rm_price_bands=[RmPriceBandOut.model_validate(b) for b in price_bands],
        scrap_rate=ScrapRateOut.model_validate(scrap) if scrap else None,
        process_rates=[ProcessRateOut.model_validate(r) for r in process_rates],
        overhead_params=[CostOverheadParamOut.model_validate(o) for o in overhead],
        steel_price_buildups=[SteelPriceBuildUpOut.model_validate(b) for b in steel_buildups],
        grade_equivalences=[GradeEquivalenceOut.model_validate(g) for g in grade_equivs],
        section_catalog_items=[SectionCatalogItemOut.model_validate(s) for s in section_items],
        bo_catalog_items=[BoughtOutCatalogItemOut.model_validate(b) for b in bo_items],
    )


# ---------------------------------------------------------------------------
# Lookup
# ---------------------------------------------------------------------------

@router.get("/lookup", response_model=NormsLookup)
def get_norms_lookup(client_id: int, db: Session = Depends(get_db)):
    """Grades + process-rates for the client's current norm library — used by line editor dropdowns."""
    grades = db.query(MaterialGrade).order_by(MaterialGrade.id).all()
    library = db.query(NormLibrary).filter_by(is_current=True, client_id=client_id).first()
    if not library:
        # No published library yet — return grades so dropdowns still work
        return NormsLookup(
            norm_library_id=None,
            material_grades=[MaterialGradeOut.model_validate(g) for g in grades],
            process_rates=[],
            overhead_params=[],
        )
    rates = (
        db.query(ProcessRate)
        .filter_by(norm_library_id=library.id)
        .order_by(ProcessRate.group_label, ProcessRate.sort_order)
        .all()
    )
    overhead = (
        db.query(CostOverheadParam)
        .filter_by(norm_library_id=library.id)
        .order_by(CostOverheadParam.applies_to, CostOverheadParam.sort_order)
        .all()
    )
    return NormsLookup(
        norm_library_id=library.id,
        material_grades=[MaterialGradeOut.model_validate(g) for g in grades],
        process_rates=[ProcessRateOut.model_validate(r) for r in rates],
        overhead_params=[CostOverheadParamOut.model_validate(o) for o in overhead],
    )


@router.get("/grade-equivalences/resolve", response_model=GradeEquivalenceResolveOut)
def resolve_grade_equivalence(client_id: int, spec: str, db: Session = Depends(get_db)):
    """Auto-resolve a customer spec (e.g. 'S235J2') to its Indian-equivalent grade, via the client's current library."""
    library = db.query(NormLibrary).filter_by(is_current=True, client_id=client_id).first()
    if not library:
        raise HTTPException(status_code=404, detail="No current norm library for this client")
    match = (
        db.query(GradeEquivalence)
        .filter(GradeEquivalence.norm_library_id == library.id, func.lower(GradeEquivalence.customer_spec) == spec.strip().lower())
        .first()
    )
    if not match:
        raise HTTPException(status_code=404, detail=f"No grade equivalence mapped for spec '{spec}'")
    grade = db.get(MaterialGrade, match.material_grade_id)
    return GradeEquivalenceResolveOut(
        customer_spec=match.customer_spec,
        material_grade_id=match.material_grade_id,
        material_grade_name=grade.name if grade else "",
    )


@router.get("/rm-price-trend", response_model=list[RmPriceTrendPoint])
def rm_price_trend(client_id: int, grade_id: int, thickness_band: str, db: Session = Depends(get_db)):
    """RM price for one grade+band across every norm library version for this client, oldest first."""
    libraries = (
        db.query(NormLibrary)
        .filter_by(client_id=client_id)
        .order_by(NormLibrary.effective_date, NormLibrary.created_at)
        .all()
    )
    points: list[RmPriceTrendPoint] = []
    for lib in libraries:
        band = db.query(RmPriceBand).filter_by(
            norm_library_id=lib.id, grade_id=grade_id, thickness_band=thickness_band
        ).first()
        if band:
            points.append(RmPriceTrendPoint(
                norm_library_id=lib.id,
                label=lib.label,
                effective_date=lib.effective_date,
                is_current=lib.is_current,
                is_draft=lib.is_draft,
                price_per_kg=band.price_per_kg,
            ))
    return points


# ---------------------------------------------------------------------------
# Library CRUD
# ---------------------------------------------------------------------------

@router.get("/libraries", response_model=list[NormLibrarySummary])
def list_libraries(client_id: int | None = None, db: Session = Depends(get_db)):
    q = db.query(NormLibrary)
    if client_id is not None:
        q = q.filter(NormLibrary.client_id == client_id)
    return q.order_by(NormLibrary.created_at.desc()).all()


@router.post("/libraries", response_model=NormLibraryDetail, status_code=201)
def create_library(body: CreateLibraryRequest, db: Session = Depends(get_db)):
    from app.models.clients import Client
    client = db.get(Client, body.client_id)
    if not client:
        raise HTTPException(status_code=404, detail=f"Client {body.client_id} not found")
    label = body.label.strip()
    if not label:
        raise HTTPException(status_code=422, detail="Label cannot be empty")
    lib = NormLibrary(
        client_id=body.client_id,
        label=label,
        effective_date=body.effective_date or date.today(),
        is_current=False,
        is_draft=True,
        created_at=datetime.now(UTC),
    )
    db.add(lib)
    db.flush()

    # Seed empty price bands for all existing grades so the matrix is immediately editable
    for grade in db.query(MaterialGrade).order_by(MaterialGrade.id).all():
        for band in THICKNESS_BANDS:
            db.add(RmPriceBand(
                norm_library_id=lib.id,
                grade_id=grade.id,
                thickness_band=band,
                price_per_kg=Decimal("0"),
            ))
    db.add(ScrapRate(norm_library_id=lib.id, rate_per_kg=Decimal("0")))

    if body.seed_defaults:
        db.flush()  # write blank bands/scrap to DB so seed can find and update them
        _seed_library_defaults(lib.id, db)

    db.commit()
    return _build_detail(lib.id, db)


@router.get("/libraries/{library_id}", response_model=NormLibraryDetail)
def get_library(library_id: int, db: Session = Depends(get_db)):
    return _build_detail(library_id, db)


@router.post("/libraries/{library_id}/duplicate", response_model=NormLibraryDetail, status_code=201)
def duplicate_library(library_id: int, db: Session = Depends(get_db)):
    src = _get_library_or_404(library_id, db)

    new_lib = NormLibrary(
        client_id=src.client_id,
        label=f"{src.label} (copy)",
        effective_date=date.today(),
        is_current=False,
        is_draft=True,
        created_at=datetime.now(UTC),
    )
    db.add(new_lib)
    db.flush()

    for band in db.query(RmPriceBand).filter_by(norm_library_id=src.id).all():
        db.add(RmPriceBand(
            norm_library_id=new_lib.id,
            grade_id=band.grade_id,
            thickness_band=band.thickness_band,
            price_per_kg=band.price_per_kg,
        ))

    scrap = db.query(ScrapRate).filter_by(norm_library_id=src.id).first()
    if scrap:
        db.add(ScrapRate(norm_library_id=new_lib.id, rate_per_kg=scrap.rate_per_kg))

    for pr in db.query(ProcessRate).filter_by(norm_library_id=src.id).order_by(ProcessRate.sort_order).all():
        db.add(ProcessRate(
            norm_library_id=new_lib.id,
            operation_name=pr.operation_name,
            unit=pr.unit,
            rate=pr.rate,
            sort_order=pr.sort_order,
            group_label=pr.group_label,
        ))

    for op in db.query(CostOverheadParam).filter_by(norm_library_id=src.id).all():
        db.add(CostOverheadParam(
            norm_library_id=new_lib.id,
            applies_to=op.applies_to,
            param_name=op.param_name,
            sort_order=op.sort_order,
            param_value=op.param_value,
        ))

    for sb in db.query(SteelPriceBuildUp).filter_by(norm_library_id=src.id).all():
        db.add(SteelPriceBuildUp(
            norm_library_id=new_lib.id,
            grade_id=sb.grade_id,
            thickness_band=sb.thickness_band,
            basic_price_per_tonne=sb.basic_price_per_tonne,
            ust_amount=sb.ust_amount,
            trimming_amount=sb.trimming_amount,
            normalising_amount=sb.normalising_amount,
            trader_transport_constant=sb.trader_transport_constant,
        ))

    for ge in db.query(GradeEquivalence).filter_by(norm_library_id=src.id).all():
        db.add(GradeEquivalence(
            norm_library_id=new_lib.id,
            customer_spec=ge.customer_spec,
            material_grade_id=ge.material_grade_id,
            notes=ge.notes,
        ))

    for sc in db.query(SectionCatalogItem).filter_by(norm_library_id=src.id).all():
        db.add(SectionCatalogItem(
            norm_library_id=new_lib.id,
            category=sc.category,
            designation=sc.designation,
            kg_per_m=sc.kg_per_m,
            rate_per_kg=sc.rate_per_kg,
        ))

    for bo in db.query(BoughtOutCatalogItem).filter_by(norm_library_id=src.id).all():
        db.add(BoughtOutCatalogItem(
            norm_library_id=new_lib.id,
            name=bo.name,
            category=bo.category,
            unit_weight_kg=bo.unit_weight_kg,
            rate=bo.rate,
        ))

    db.commit()
    return _build_detail(new_lib.id, db)


@router.delete("/libraries/{library_id}", status_code=204)
def delete_library(library_id: int, db: Session = Depends(get_db)):
    lib = _get_library_or_404(library_id, db)
    if lib.is_current:
        raise HTTPException(status_code=409, detail="Cannot delete the current library. Publish a different version first.")
    if not lib.is_draft:
        raise HTTPException(status_code=409, detail="Only draft libraries can be deleted. Historical versions are locked.")
    db.query(RmPriceBand).filter_by(norm_library_id=library_id).delete()
    db.query(ScrapRate).filter_by(norm_library_id=library_id).delete()
    db.query(ProcessRate).filter_by(norm_library_id=library_id).delete()
    db.query(CostOverheadParam).filter_by(norm_library_id=library_id).delete()
    db.query(SteelPriceBuildUp).filter_by(norm_library_id=library_id).delete()
    db.query(GradeEquivalence).filter_by(norm_library_id=library_id).delete()
    db.query(SectionCatalogItem).filter_by(norm_library_id=library_id).delete()
    db.query(BoughtOutCatalogItem).filter_by(norm_library_id=library_id).delete()
    db.delete(lib)
    db.commit()


@router.patch("/libraries/{library_id}/rename", response_model=NormLibraryDetail)
def rename_library(library_id: int, body: dict, db: Session = Depends(get_db)):
    lib = _get_library_or_404(library_id, db)
    _assert_editable(lib)
    label = (body.get("label") or "").strip()
    if not label:
        raise HTTPException(status_code=422, detail="Label cannot be empty")
    lib.label = label
    db.commit()
    return _build_detail(library_id, db)


@router.post("/libraries/{library_id}/publish", response_model=NormLibraryDetail)
def publish_library(library_id: int, db: Session = Depends(get_db)):
    lib = _get_library_or_404(library_id, db)
    if lib.is_current:
        raise HTTPException(status_code=409, detail=f"Library '{lib.label}' is already current.")
    if not lib.is_draft:
        raise HTTPException(status_code=409, detail=f"Library '{lib.label}' is historical and cannot be re-published.")

    db.query(NormLibrary).filter_by(is_current=True, client_id=lib.client_id).update({"is_current": False, "is_draft": False})
    lib.is_current = True
    lib.is_draft = False
    db.commit()
    return _build_detail(library_id, db)


# ---------------------------------------------------------------------------
# RM Prices
# ---------------------------------------------------------------------------

@router.patch("/libraries/{library_id}/rm-prices", response_model=NormLibraryDetail)
def update_rm_prices(library_id: int, body: RmPricesBulkUpdate, db: Session = Depends(get_db)):
    lib = _get_library_or_404(library_id, db)
    _assert_editable(lib)

    now = datetime.now(UTC)

    if body.scrap_rate is not None:
        scrap = db.query(ScrapRate).filter_by(norm_library_id=library_id).first()
        if scrap:
            if scrap.rate_per_kg != body.scrap_rate:
                scrap.rate_per_kg = body.scrap_rate
                scrap.updated_at = now
        else:
            db.add(ScrapRate(norm_library_id=library_id, rate_per_kg=body.scrap_rate))

    for pu in body.grade_premium_updates:
        grade = db.get(MaterialGrade, pu.grade_id)
        if not grade:
            raise HTTPException(status_code=404, detail=f"Material grade {pu.grade_id} not found")
        if grade.base_grade_id is None:
            raise HTTPException(status_code=422, detail=f"Grade '{grade.name}' is not a premium-derived grade")
        if grade.premium_amount != pu.premium_amount:
            grade.premium_amount = pu.premium_amount
            grade.updated_at = now

    for upd in body.price_updates:
        band = (
            db.query(RmPriceBand)
            .filter_by(norm_library_id=library_id, grade_id=upd.grade_id, thickness_band=upd.thickness_band)
            .first()
        )
        if not band:
            raise HTTPException(
                status_code=404,
                detail=f"Price band not found: grade_id={upd.grade_id}, band={upd.thickness_band}",
            )
        new_price = Decimal(str(upd.price_per_kg))
        if band.price_per_kg != new_price:
            band.price_per_kg = new_price
            band.updated_at = now

    db.commit()
    return _build_detail(library_id, db)


@router.post("/libraries/{library_id}/grades", response_model=NormLibraryDetail, status_code=201)
def add_grade(library_id: int, body: AddGradeRequest, db: Session = Depends(get_db)):
    lib = _get_library_or_404(library_id, db)
    _assert_editable(lib)

    existing = db.query(MaterialGrade).filter_by(name=body.name).first()
    if existing:
        grade = existing
    else:
        grade = MaterialGrade(
            name=body.name,
            base_grade_id=body.base_grade_id,
            premium_amount=body.premium_amount,
        )
        db.add(grade)
        db.flush()

    already = db.query(RmPriceBand).filter_by(norm_library_id=library_id, grade_id=grade.id).first()
    if already:
        raise HTTPException(status_code=409, detail=f"Grade '{body.name}' already has price bands in this library")

    if body.base_grade_id is None:
        initial = body.initial_price or Decimal("0")
        for band in THICKNESS_BANDS:
            db.add(RmPriceBand(
                norm_library_id=library_id,
                grade_id=grade.id,
                thickness_band=band,
                price_per_kg=initial,
            ))

    db.commit()
    return _build_detail(library_id, db)


# ---------------------------------------------------------------------------
# Process Rates
# ---------------------------------------------------------------------------

@router.patch("/libraries/{library_id}/process-rates", response_model=NormLibraryDetail)
def update_process_rates(library_id: int, body: ProcessRatesBulkUpdate, db: Session = Depends(get_db)):
    lib = _get_library_or_404(library_id, db)
    _assert_editable(lib)

    now = datetime.now(UTC)
    for upd in body.rates:
        pr = db.get(ProcessRate, upd.id)
        if not pr or pr.norm_library_id != library_id:
            raise HTTPException(status_code=404, detail=f"Process rate {upd.id} not found in library {library_id}")
        new_rate = Decimal(str(upd.rate))
        if pr.rate != new_rate:
            pr.rate = new_rate
            pr.updated_at = now

    db.commit()
    return _build_detail(library_id, db)


@router.post("/libraries/{library_id}/process-rates", response_model=NormLibraryDetail, status_code=201)
def add_process_rate(library_id: int, body: AddProcessRateRequest, db: Session = Depends(get_db)):
    lib = _get_library_or_404(library_id, db)
    _assert_editable(lib)

    max_order = (
        db.query(func.max(ProcessRate.sort_order))
        .filter_by(norm_library_id=library_id, group_label=body.group_label)
        .scalar()
    ) or 0

    db.add(ProcessRate(
        norm_library_id=library_id,
        operation_name=body.operation_name,
        unit=body.unit,
        rate=body.rate,
        sort_order=max_order + 1,
        group_label=body.group_label,
    ))
    db.commit()
    return _build_detail(library_id, db)


# ---------------------------------------------------------------------------
# Overhead Params
# ---------------------------------------------------------------------------

@router.patch("/libraries/{library_id}/overhead-params", response_model=NormLibraryDetail)
def update_overhead_params(library_id: int, body: OverheadParamsBulkUpdate, db: Session = Depends(get_db)):
    lib = _get_library_or_404(library_id, db)
    _assert_editable(lib)

    now = datetime.now(UTC)
    for upd in body.params:
        param = db.get(CostOverheadParam, upd.id)
        if not param or param.norm_library_id != library_id:
            raise HTTPException(status_code=404, detail=f"Overhead param {upd.id} not found in library {library_id}")
        new_val = Decimal(str(upd.param_value)) if upd.param_value is not None else None
        if param.param_value != new_val:
            param.param_value = new_val
            param.updated_at = now

    db.commit()
    return _build_detail(library_id, db)


@router.post("/libraries/{library_id}/overhead-params", response_model=NormLibraryDetail, status_code=201)
def add_overhead_param(library_id: int, body: AddOverheadParamRequest, db: Session = Depends(get_db)):
    lib = _get_library_or_404(library_id, db)
    _assert_editable(lib)

    max_order = (
        db.query(func.max(CostOverheadParam.sort_order))
        .filter_by(norm_library_id=library_id, applies_to=body.applies_to)
        .scalar()
    ) or 0

    db.add(CostOverheadParam(
        norm_library_id=library_id,
        applies_to=body.applies_to,
        param_name=body.param_name,
        sort_order=max_order + 1,
        param_value=body.param_value,
    ))
    db.commit()
    return _build_detail(library_id, db)


# ---------------------------------------------------------------------------
# Steel Price Build-Up
# ---------------------------------------------------------------------------

@router.post("/libraries/{library_id}/steel-buildups", response_model=NormLibraryDetail, status_code=201)
def add_steel_buildup(library_id: int, body: SteelPriceBuildUpCreate, db: Session = Depends(get_db)):
    lib = _get_library_or_404(library_id, db)
    _assert_editable(lib)

    if not db.get(MaterialGrade, body.grade_id):
        raise HTTPException(status_code=404, detail=f"Material grade {body.grade_id} not found")

    existing = db.query(SteelPriceBuildUp).filter_by(
        norm_library_id=library_id, grade_id=body.grade_id, thickness_band=body.thickness_band
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="A build-up already exists for this grade + thickness band — edit it instead")

    db.add(SteelPriceBuildUp(
        norm_library_id=library_id,
        grade_id=body.grade_id,
        thickness_band=body.thickness_band,
        basic_price_per_tonne=body.basic_price_per_tonne,
        ust_amount=body.ust_amount,
        trimming_amount=body.trimming_amount,
        normalising_amount=body.normalising_amount,
        trader_transport_constant=body.trader_transport_constant,
    ))
    db.commit()
    return _build_detail(library_id, db)


@router.patch("/libraries/{library_id}/steel-buildups/{buildup_id}", response_model=NormLibraryDetail)
def update_steel_buildup(library_id: int, buildup_id: int, body: SteelPriceBuildUpUpdate, db: Session = Depends(get_db)):
    lib = _get_library_or_404(library_id, db)
    _assert_editable(lib)

    row = db.get(SteelPriceBuildUp, buildup_id)
    if not row or row.norm_library_id != library_id:
        raise HTTPException(status_code=404, detail=f"Steel price build-up {buildup_id} not found in library {library_id}")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(row, field, value)
    row.updated_at = datetime.now(UTC)
    db.commit()
    return _build_detail(library_id, db)


@router.delete("/libraries/{library_id}/steel-buildups/{buildup_id}", response_model=NormLibraryDetail)
def delete_steel_buildup(library_id: int, buildup_id: int, db: Session = Depends(get_db)):
    lib = _get_library_or_404(library_id, db)
    _assert_editable(lib)

    row = db.get(SteelPriceBuildUp, buildup_id)
    if not row or row.norm_library_id != library_id:
        raise HTTPException(status_code=404, detail=f"Steel price build-up {buildup_id} not found in library {library_id}")
    db.delete(row)
    db.commit()
    return _build_detail(library_id, db)


@router.post("/libraries/{library_id}/steel-buildups/{buildup_id}/apply-to-rm", response_model=NormLibraryDetail)
def apply_steel_buildup_to_rm(library_id: int, buildup_id: int, db: Session = Depends(get_db)):
    """Write this build-up's computed Rs/kg into the matching RM price band."""
    lib = _get_library_or_404(library_id, db)
    _assert_editable(lib)

    row = db.get(SteelPriceBuildUp, buildup_id)
    if not row or row.norm_library_id != library_id:
        raise HTTPException(status_code=404, detail=f"Steel price build-up {buildup_id} not found in library {library_id}")

    band = db.query(RmPriceBand).filter_by(
        norm_library_id=library_id, grade_id=row.grade_id, thickness_band=row.thickness_band
    ).first()
    if not band:
        raise HTTPException(status_code=404, detail="No matching RM price band found — add the grade to this library first")

    band.price_per_kg = row.price_per_kg
    band.updated_at = datetime.now(UTC)
    db.commit()
    return _build_detail(library_id, db)


# ---------------------------------------------------------------------------
# Grade Equivalence Mapping
# ---------------------------------------------------------------------------

@router.post("/libraries/{library_id}/grade-equivalences", response_model=NormLibraryDetail, status_code=201)
def add_grade_equivalence(library_id: int, body: GradeEquivalenceCreate, db: Session = Depends(get_db)):
    lib = _get_library_or_404(library_id, db)
    _assert_editable(lib)

    if not db.get(MaterialGrade, body.material_grade_id):
        raise HTTPException(status_code=404, detail=f"Material grade {body.material_grade_id} not found")

    existing = db.query(GradeEquivalence).filter(
        GradeEquivalence.norm_library_id == library_id,
        func.lower(GradeEquivalence.customer_spec) == body.customer_spec.lower(),
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Spec '{body.customer_spec}' is already mapped in this library")

    db.add(GradeEquivalence(
        norm_library_id=library_id,
        customer_spec=body.customer_spec,
        material_grade_id=body.material_grade_id,
        notes=body.notes,
    ))
    db.commit()
    return _build_detail(library_id, db)


@router.patch("/libraries/{library_id}/grade-equivalences/{equiv_id}", response_model=NormLibraryDetail)
def update_grade_equivalence(library_id: int, equiv_id: int, body: GradeEquivalenceUpdate, db: Session = Depends(get_db)):
    lib = _get_library_or_404(library_id, db)
    _assert_editable(lib)

    row = db.get(GradeEquivalence, equiv_id)
    if not row or row.norm_library_id != library_id:
        raise HTTPException(status_code=404, detail=f"Grade equivalence {equiv_id} not found in library {library_id}")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(row, field, value)
    row.updated_at = datetime.now(UTC)
    db.commit()
    return _build_detail(library_id, db)


@router.delete("/libraries/{library_id}/grade-equivalences/{equiv_id}", response_model=NormLibraryDetail)
def delete_grade_equivalence(library_id: int, equiv_id: int, db: Session = Depends(get_db)):
    lib = _get_library_or_404(library_id, db)
    _assert_editable(lib)

    row = db.get(GradeEquivalence, equiv_id)
    if not row or row.norm_library_id != library_id:
        raise HTTPException(status_code=404, detail=f"Grade equivalence {equiv_id} not found in library {library_id}")
    db.delete(row)
    db.commit()
    return _build_detail(library_id, db)


# ---------------------------------------------------------------------------
# Section / Bar / Tube Catalogue
# ---------------------------------------------------------------------------

@router.post("/libraries/{library_id}/section-catalog", response_model=NormLibraryDetail, status_code=201)
def add_section_catalog_item(library_id: int, body: SectionCatalogItemCreate, db: Session = Depends(get_db)):
    lib = _get_library_or_404(library_id, db)
    _assert_editable(lib)

    existing = db.query(SectionCatalogItem).filter(
        SectionCatalogItem.norm_library_id == library_id,
        func.lower(SectionCatalogItem.designation) == body.designation.lower(),
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Designation '{body.designation}' already exists in this library")

    db.add(SectionCatalogItem(
        norm_library_id=library_id,
        category=body.category,
        designation=body.designation,
        kg_per_m=body.kg_per_m,
        rate_per_kg=body.rate_per_kg,
    ))
    db.commit()
    return _build_detail(library_id, db)


@router.patch("/libraries/{library_id}/section-catalog/{item_id}", response_model=NormLibraryDetail)
def update_section_catalog_item(library_id: int, item_id: int, body: SectionCatalogItemUpdate, db: Session = Depends(get_db)):
    lib = _get_library_or_404(library_id, db)
    _assert_editable(lib)

    row = db.get(SectionCatalogItem, item_id)
    if not row or row.norm_library_id != library_id:
        raise HTTPException(status_code=404, detail=f"Section catalog item {item_id} not found in library {library_id}")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(row, field, value)
    row.updated_at = datetime.now(UTC)
    db.commit()
    return _build_detail(library_id, db)


@router.delete("/libraries/{library_id}/section-catalog/{item_id}", response_model=NormLibraryDetail)
def delete_section_catalog_item(library_id: int, item_id: int, db: Session = Depends(get_db)):
    lib = _get_library_or_404(library_id, db)
    _assert_editable(lib)

    row = db.get(SectionCatalogItem, item_id)
    if not row or row.norm_library_id != library_id:
        raise HTTPException(status_code=404, detail=f"Section catalog item {item_id} not found in library {library_id}")
    db.delete(row)
    db.commit()
    return _build_detail(library_id, db)


# ---------------------------------------------------------------------------
# Bought-Out Item Master
# ---------------------------------------------------------------------------

@router.post("/libraries/{library_id}/bo-catalog", response_model=NormLibraryDetail, status_code=201)
def add_bo_catalog_item(library_id: int, body: BoughtOutCatalogItemCreate, db: Session = Depends(get_db)):
    lib = _get_library_or_404(library_id, db)
    _assert_editable(lib)

    existing = db.query(BoughtOutCatalogItem).filter(
        BoughtOutCatalogItem.norm_library_id == library_id,
        func.lower(BoughtOutCatalogItem.name) == body.name.lower(),
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Item '{body.name}' already exists in this library")

    db.add(BoughtOutCatalogItem(
        norm_library_id=library_id,
        name=body.name,
        category=body.category,
        unit_weight_kg=body.unit_weight_kg,
        rate=body.rate,
    ))
    db.commit()
    return _build_detail(library_id, db)


@router.patch("/libraries/{library_id}/bo-catalog/{item_id}", response_model=NormLibraryDetail)
def update_bo_catalog_item(library_id: int, item_id: int, body: BoughtOutCatalogItemUpdate, db: Session = Depends(get_db)):
    lib = _get_library_or_404(library_id, db)
    _assert_editable(lib)

    row = db.get(BoughtOutCatalogItem, item_id)
    if not row or row.norm_library_id != library_id:
        raise HTTPException(status_code=404, detail=f"Bought-out catalog item {item_id} not found in library {library_id}")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(row, field, value)
    row.updated_at = datetime.now(UTC)
    db.commit()
    return _build_detail(library_id, db)


@router.delete("/libraries/{library_id}/bo-catalog/{item_id}", response_model=NormLibraryDetail)
def delete_bo_catalog_item(library_id: int, item_id: int, db: Session = Depends(get_db)):
    lib = _get_library_or_404(library_id, db)
    _assert_editable(lib)

    row = db.get(BoughtOutCatalogItem, item_id)
    if not row or row.norm_library_id != library_id:
        raise HTTPException(status_code=404, detail=f"Bought-out catalog item {item_id} not found in library {library_id}")
    db.delete(row)
    db.commit()
    return _build_detail(library_id, db)
