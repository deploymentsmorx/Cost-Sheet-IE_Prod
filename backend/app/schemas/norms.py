from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, field_validator

VALID_THICKNESS_BANDS = {"<10mm", "12mm", ">12-19mm", "20mm", ">20-40mm", ">40-63mm", "80mm"}
VALID_UNITS = {"Rs/Kg", "Rs/Hr", "Rs/mm/meter", "Rs/slant/meter", "Rs/Nos", "Rs/Sqm", "%"}
VALID_APPLIES_TO = {"raw_material", "bought_out", "process_cost"}


# ---------------------------------------------------------------------------
# Norm Libraries
# ---------------------------------------------------------------------------

class NormLibrarySummary(BaseModel):
    id: int
    client_id: int
    label: str
    effective_date: date
    is_current: bool
    is_draft: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class CreateLibraryRequest(BaseModel):
    client_id: int
    label: str
    effective_date: Optional[date] = None
    seed_defaults: bool = False


# ---------------------------------------------------------------------------
# Material grades
# ---------------------------------------------------------------------------

class MaterialGradeOut(BaseModel):
    id: int
    name: str
    base_grade_id: Optional[int] = None
    premium_amount: Optional[Decimal] = None
    updated_at: datetime

    model_config = {"from_attributes": True}


class GradePremiumUpdate(BaseModel):
    grade_id: int
    premium_amount: Decimal = Field(..., ge=0)


class AddGradeRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    base_grade_id: Optional[int] = None
    premium_amount: Optional[Decimal] = Field(None, ge=0)
    initial_price: Optional[Decimal] = Field(None, ge=0)

    @field_validator("name")
    @classmethod
    def name_stripped(cls, v: str) -> str:
        return v.strip()


# ---------------------------------------------------------------------------
# RM price bands
# ---------------------------------------------------------------------------

class RmPriceBandOut(BaseModel):
    id: int
    grade_id: int
    thickness_band: str
    price_per_kg: Decimal
    updated_at: datetime

    model_config = {"from_attributes": True}


class RmPriceUpdate(BaseModel):
    grade_id: int
    thickness_band: str
    price_per_kg: Decimal

    @field_validator("price_per_kg")
    @classmethod
    def price_non_negative(cls, v: Decimal) -> Decimal:
        if v < 0:
            raise ValueError("price_per_kg must be non-negative")
        return v

    @field_validator("thickness_band")
    @classmethod
    def band_valid(cls, v: str) -> str:
        if v not in VALID_THICKNESS_BANDS:
            raise ValueError(f"thickness_band must be one of {sorted(VALID_THICKNESS_BANDS)}")
        return v


class RmPricesBulkUpdate(BaseModel):
    scrap_rate: Optional[Decimal] = Field(None, ge=0)
    grade_premium_updates: list[GradePremiumUpdate] = []
    price_updates: list[RmPriceUpdate] = []


# ---------------------------------------------------------------------------
# Scrap rate
# ---------------------------------------------------------------------------

class ScrapRateOut(BaseModel):
    rate_per_kg: Decimal
    updated_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Process rates
# ---------------------------------------------------------------------------

class ProcessRateOut(BaseModel):
    id: int
    operation_name: str
    unit: str
    rate: Decimal
    sort_order: int
    group_label: str
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProcessRateUpdate(BaseModel):
    id: int
    rate: Decimal

    @field_validator("rate")
    @classmethod
    def rate_non_negative(cls, v: Decimal) -> Decimal:
        if v < 0:
            raise ValueError("rate must be non-negative")
        return v


class ProcessRatesBulkUpdate(BaseModel):
    rates: list[ProcessRateUpdate] = Field(..., min_length=1)


class AddProcessRateRequest(BaseModel):
    operation_name: str = Field(..., min_length=1, max_length=200)
    unit: str
    rate: Decimal = Field(..., ge=0)
    group_label: str = Field(..., min_length=1, max_length=100)

    @field_validator("unit")
    @classmethod
    def unit_valid(cls, v: str) -> str:
        if v not in VALID_UNITS:
            raise ValueError(f"unit must be one of {VALID_UNITS}")
        return v

    @field_validator("operation_name", "group_label")
    @classmethod
    def stripped(cls, v: str) -> str:
        return v.strip()


# ---------------------------------------------------------------------------
# Overhead params
# ---------------------------------------------------------------------------

class CostOverheadParamOut(BaseModel):
    id: int
    applies_to: str
    param_name: str
    sort_order: int
    param_value: Optional[Decimal] = None
    updated_at: datetime

    model_config = {"from_attributes": True}


class OverheadParamUpdate(BaseModel):
    id: int
    param_value: Optional[Decimal] = Field(None, ge=0)


class OverheadParamsBulkUpdate(BaseModel):
    params: list[OverheadParamUpdate] = Field(..., min_length=1)


class AddOverheadParamRequest(BaseModel):
    applies_to: str
    param_name: str = Field(..., min_length=1, max_length=100)
    param_value: Optional[Decimal] = Field(None, ge=0)

    @field_validator("applies_to")
    @classmethod
    def applies_to_valid(cls, v: str) -> str:
        if v not in VALID_APPLIES_TO:
            raise ValueError(f"applies_to must be one of {VALID_APPLIES_TO}")
        return v

    @field_validator("param_name")
    @classmethod
    def name_stripped(cls, v: str) -> str:
        return v.strip()


# ---------------------------------------------------------------------------
# Full library detail
# ---------------------------------------------------------------------------

class NormLibraryDetail(BaseModel):
    library: NormLibrarySummary
    material_grades: list[MaterialGradeOut]
    rm_price_bands: list[RmPriceBandOut]
    scrap_rate: Optional[ScrapRateOut]
    process_rates: list[ProcessRateOut]
    overhead_params: list[CostOverheadParamOut]


class NormsLookup(BaseModel):
    """Lightweight payload for populating costing-line editor dropdowns."""
    norm_library_id: Optional[int]  # None when no library is published yet
    material_grades: list[MaterialGradeOut]
    process_rates: list[ProcessRateOut]
    overhead_params: list[CostOverheadParamOut] = []
