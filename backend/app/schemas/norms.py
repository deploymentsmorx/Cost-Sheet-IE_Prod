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
# Steel price build-up
# ---------------------------------------------------------------------------

class SteelPriceBuildUpOut(BaseModel):
    id: int
    grade_id: int
    thickness_band: str
    basic_price_per_tonne: Decimal
    ust_amount: Decimal
    trimming_amount: Decimal
    normalising_amount: Decimal
    trader_transport_constant: Decimal
    price_per_kg: Decimal
    updated_at: datetime

    model_config = {"from_attributes": True}


class SteelPriceBuildUpCreate(BaseModel):
    grade_id: int
    thickness_band: str
    basic_price_per_tonne: Decimal = Field(..., ge=0)
    ust_amount: Decimal = Field(Decimal("0"), ge=0)
    trimming_amount: Decimal = Field(Decimal("0"), ge=0)
    normalising_amount: Decimal = Field(Decimal("0"), ge=0)
    trader_transport_constant: Decimal = Field(Decimal("0"), ge=0)

    @field_validator("thickness_band")
    @classmethod
    def band_valid(cls, v: str) -> str:
        if v not in VALID_THICKNESS_BANDS:
            raise ValueError(f"thickness_band must be one of {sorted(VALID_THICKNESS_BANDS)}")
        return v


class SteelPriceBuildUpUpdate(BaseModel):
    basic_price_per_tonne: Optional[Decimal] = Field(None, ge=0)
    ust_amount: Optional[Decimal] = Field(None, ge=0)
    trimming_amount: Optional[Decimal] = Field(None, ge=0)
    normalising_amount: Optional[Decimal] = Field(None, ge=0)
    trader_transport_constant: Optional[Decimal] = Field(None, ge=0)


# ---------------------------------------------------------------------------
# Grade equivalence mapping
# ---------------------------------------------------------------------------

class GradeEquivalenceOut(BaseModel):
    id: int
    customer_spec: str
    material_grade_id: int
    notes: Optional[str] = None
    updated_at: datetime

    model_config = {"from_attributes": True}


class GradeEquivalenceCreate(BaseModel):
    customer_spec: str = Field(..., min_length=1, max_length=100)
    material_grade_id: int
    notes: Optional[str] = Field(None, max_length=300)

    @field_validator("customer_spec")
    @classmethod
    def spec_stripped(cls, v: str) -> str:
        return v.strip()


class GradeEquivalenceUpdate(BaseModel):
    customer_spec: Optional[str] = Field(None, min_length=1, max_length=100)
    material_grade_id: Optional[int] = None
    notes: Optional[str] = Field(None, max_length=300)


class GradeEquivalenceResolveOut(BaseModel):
    customer_spec: str
    material_grade_id: int
    material_grade_name: str


# ---------------------------------------------------------------------------
# Section / bar / tube catalogue
# ---------------------------------------------------------------------------

VALID_SECTION_CATEGORIES = {"channel", "angle", "round_bar", "square_bar", "flat_bar", "pipe"}


class SectionCatalogItemOut(BaseModel):
    id: int
    category: str
    designation: str
    kg_per_m: Decimal
    rate_per_kg: Decimal
    rate_per_m: Decimal
    updated_at: datetime

    model_config = {"from_attributes": True}


class SectionCatalogItemCreate(BaseModel):
    category: str
    designation: str = Field(..., min_length=1, max_length=100)
    kg_per_m: Decimal = Field(..., ge=0)
    rate_per_kg: Decimal = Field(..., ge=0)

    @field_validator("category")
    @classmethod
    def category_valid(cls, v: str) -> str:
        if v not in VALID_SECTION_CATEGORIES:
            raise ValueError(f"category must be one of {sorted(VALID_SECTION_CATEGORIES)}")
        return v

    @field_validator("designation")
    @classmethod
    def designation_stripped(cls, v: str) -> str:
        return v.strip()


class SectionCatalogItemUpdate(BaseModel):
    category: Optional[str] = None
    designation: Optional[str] = Field(None, min_length=1, max_length=100)
    kg_per_m: Optional[Decimal] = Field(None, ge=0)
    rate_per_kg: Optional[Decimal] = Field(None, ge=0)


# ---------------------------------------------------------------------------
# Bought-out item master
# ---------------------------------------------------------------------------

class BoughtOutCatalogItemOut(BaseModel):
    id: int
    name: str
    category: Optional[str] = None
    unit_weight_kg: Optional[Decimal] = None
    rate: Decimal
    updated_at: datetime

    model_config = {"from_attributes": True}


class BoughtOutCatalogItemCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    category: Optional[str] = Field(None, max_length=100)
    unit_weight_kg: Optional[Decimal] = Field(None, ge=0)
    rate: Decimal = Field(..., ge=0)

    @field_validator("name")
    @classmethod
    def name_stripped(cls, v: str) -> str:
        return v.strip()


class BoughtOutCatalogItemUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    category: Optional[str] = Field(None, max_length=100)
    unit_weight_kg: Optional[Decimal] = Field(None, ge=0)
    rate: Optional[Decimal] = Field(None, ge=0)


# ---------------------------------------------------------------------------
# RM price trend (per grade, across all norm library versions for a client)
# ---------------------------------------------------------------------------

class RmPriceTrendPoint(BaseModel):
    norm_library_id: int
    label: str
    effective_date: date
    is_current: bool
    is_draft: bool
    price_per_kg: Decimal


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
    steel_price_buildups: list[SteelPriceBuildUpOut] = []
    grade_equivalences: list[GradeEquivalenceOut] = []
    section_catalog_items: list[SectionCatalogItemOut] = []
    bo_catalog_items: list[BoughtOutCatalogItemOut] = []


class NormsLookup(BaseModel):
    """Lightweight payload for populating costing-line editor dropdowns."""
    norm_library_id: Optional[int]  # None when no library is published yet
    material_grades: list[MaterialGradeOut]
    process_rates: list[ProcessRateOut]
    overhead_params: list[CostOverheadParamOut] = []
