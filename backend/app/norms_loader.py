"""
DB-only layer: builds a NormsSnapshot from a norm_library row.
This is the ONLY file in the engine pipeline that touches the database.
"""
from __future__ import annotations

from decimal import Decimal

from sqlalchemy.orm import Session

from app.calc_engine import NormsSnapshot
from app.models.norms import (
    CostOverheadParam,
    MaterialGrade,
    NormLibrary,
    ProcessRate,
    RmPriceBand,
    ScrapRate,
)


def load_norms_snapshot(
    db: Session,
    client_id: int | None = None,
    norm_library_id: int | None = None,
) -> NormsSnapshot:
    """
    Build a NormsSnapshot from the database.

    Pass client_id to resolve the currently active library for that client
    (is_current=True AND client_id=client_id).

    Pass norm_library_id to reconstruct a historical calculation by exact ID.
    """
    if norm_library_id is not None:
        library = db.get(NormLibrary, norm_library_id)
    else:
        q = db.query(NormLibrary).filter_by(is_current=True)
        if client_id is not None:
            q = q.filter(NormLibrary.client_id == client_id)
        library = q.first()

    if library is None:
        if norm_library_id is not None:
            raise ValueError(f"Norm library {norm_library_id} not found")
        raise ValueError(f"No current norm library found for client {client_id}")

    lid = library.id

    rm_prices: dict[tuple[int, str], Decimal] = {
        (b.grade_id, b.thickness_band): Decimal(str(b.price_per_kg))
        for b in db.query(RmPriceBand).filter_by(norm_library_id=lid).all()
    }

    grade_premiums: dict[int, tuple[int, Decimal]] = {}
    for g in db.query(MaterialGrade).filter(MaterialGrade.base_grade_id.isnot(None)).all():
        if g.premium_amount is not None:
            grade_premiums[g.id] = (g.base_grade_id, Decimal(str(g.premium_amount)))

    scrap_row = db.query(ScrapRate).filter_by(norm_library_id=lid).first()
    scrap_rate = Decimal(str(scrap_row.rate_per_kg)) if scrap_row else Decimal("0")

    all_process: list[ProcessRate] = db.query(ProcessRate).filter_by(norm_library_id=lid).all()
    process_loss_pct = Decimal("0")
    process_rates: dict[str, Decimal] = {}
    process_rate_units: dict[str, str] = {}
    for pr in all_process:
        rate = Decimal(str(pr.rate))
        process_rates[pr.operation_name] = rate
        process_rate_units[pr.operation_name] = pr.unit
        if pr.operation_name.upper() == "PROCESS LOSS":
            process_loss_pct = rate

    overhead_params: dict[tuple[str, str], Decimal] = {
        (op.applies_to, op.param_name): Decimal(str(op.param_value))
        for op in db.query(CostOverheadParam).filter_by(norm_library_id=lid).all()
        if op.param_value is not None
    }

    return NormsSnapshot(
        norm_library_id=lid,
        rm_prices=rm_prices,
        grade_premiums=grade_premiums,
        scrap_rate=scrap_rate,
        process_loss_pct=process_loss_pct,
        process_rates=process_rates,
        overhead_params=overhead_params,
        process_rate_units=process_rate_units,
    )
