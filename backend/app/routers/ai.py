from __future__ import annotations

import json
import logging

import anthropic
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.norms import CostOverheadParam
from app.models.parts import CostSheet
from app.norms_loader import load_norms_snapshot
from app.routers.parts import _sheet_calc

log = logging.getLogger(__name__)

router = APIRouter(prefix="/api/sheets", tags=["ai"])


class CostFlag(BaseModel):
    type: str
    message: str

class PricingOption(BaseModel):
    label: str
    price: float
    margin_pct: float
    rationale: str

class MaterialSuggestion(BaseModel):
    area: str
    suggestion: str
    estimated_saving_pct: float

class MarginScenario(BaseModel):
    scenario: str
    margin_pct: float

class AiInsights(BaseModel):
    cost_analysis: str
    cost_flags: list[CostFlag]
    pricing_recommendation: str
    pricing_options: list[PricingOption]
    material_optimization: str
    material_suggestions: list[MaterialSuggestion]
    margin_analysis: str
    margin_scenarios: list[MarginScenario]


@router.post("/{sheet_id}/ai-insights", response_model=AiInsights)
def get_ai_insights(sheet_id: int, db: Session = Depends(get_db)):
    if not settings.anthropic_api_key:
        raise HTTPException(status_code=503, detail="ANTHROPIC_API_KEY not configured")

    sheet = db.get(CostSheet, sheet_id)
    if not sheet:
        raise HTTPException(status_code=404, detail="Cost sheet not found")

    workbook = sheet.workbook
    client_id = workbook.client_id if workbook else None

    norms = load_norms_snapshot(db, client_id=client_id)
    calc = _sheet_calc(sheet, norms)

    rm_cost    = float(calc.total_rm_cost)       if calc else 0.0
    bo_cost    = float(calc.total_bo_cost)        if calc else 0.0
    proc_cost  = float(calc.total_process_cost)   if calc else 0.0
    unit_price = float(calc.unit_price)           if calc else 0.0
    margin     = float(calc.bal_margin)           if calc else 0.0
    margin_kg  = float(calc.bal_margin_per_kg)    if calc else 0.0
    tot_wt     = float(calc.total_part_weight)    if calc else 0.0
    discount   = float(sheet.discount_pct)
    transport  = float(sheet.transport_cost)

    line_summaries = []
    for ln in sheet.lines:
        ops_text = ", ".join(op.operation_type for op in ln.operations) or "none"
        line_summaries.append(
            f"  - Grade: {ln.grade_id}, Band: {ln.thickness_band}, "
            f"Thickness: {ln.thickness_mm}mm, Part Wt: {ln.part_weight}kg, "
            f"Qty: {ln.qty}, Efficiency: {ln.efficiency_pct}%, "
            f"Operations: [{ops_text}]"
        )

    bo_texts = [
        f"  - {item.description or 'BO item'}: qty={item.qty} × ₹{item.unit_price} = ₹{float(item.bo_line_cost):.2f}"
        for item in sheet.bo_items
    ]

    overhead_texts = []
    for op in db.query(CostOverheadParam).filter_by(norm_library_id=norms.norm_library_id).all():
        if op.param_value is not None:
            overhead_texts.append(f"  - {op.applies_to} / {op.param_name}: {op.param_value}%")

    client_name = workbook.client.name if workbook and workbook.client else "Not specified"
    workbook_name = workbook.name if workbook else "Unknown"

    prompt = f"""You are an expert manufacturing cost analyst specializing in steel fabrication and industrial engineering. Analyze this costing sheet and return ONLY valid JSON — no markdown, no explanation.

CONTEXT:
Workbook: {workbook_name} | Customer: {client_name}
Sheet: {sheet.name} ({sheet.part_no or 'N/A'}) — {sheet.description or 'No description'}
Supply version: {sheet.supply_version}
Total part weight: {tot_wt:.3f} kg

COST BREAKDOWN (INR):
  RM cost:       ₹{rm_cost:,.2f}  ({rm_cost/unit_price*100:.1f}% of price)
  BO cost:       ₹{bo_cost:,.2f}  ({bo_cost/unit_price*100:.1f}% of price)
  Process cost:  ₹{proc_cost:,.2f}  ({proc_cost/unit_price*100:.1f}% of price)
  Unit price:    ₹{unit_price:,.2f}
  Discount:      {discount:.1f}%
  Transport:     ₹{transport:,.2f}
  Balance margin:₹{margin:,.2f} (₹{margin_kg:,.2f}/kg)

RM LINES:
{chr(10).join(line_summaries) if line_summaries else '  None'}

BOUGHT-OUT ITEMS:
{chr(10).join(bo_texts) if bo_texts else '  None'}

OVERHEAD & PROFIT PARAMS:
{chr(10).join(overhead_texts) if overhead_texts else '  Not configured'}

Return exactly this JSON structure:
{{
  "cost_analysis": "<2-3 sentence summary of the cost structure and any notable observations>",
  "cost_flags": [
    {{"type": "warning|info|positive", "message": "<specific actionable observation>"}}
  ],
  "pricing_recommendation": "<2-3 sentence pricing strategy recommendation>",
  "pricing_options": [
    {{"label": "<e.g. Competitive>", "price": <number>, "margin_pct": <number>, "rationale": "<why>"}}
  ],
  "material_optimization": "<2-3 sentence analysis of material cost opportunities>",
  "material_suggestions": [
    {{"area": "<what to change>", "suggestion": "<how>", "estimated_saving_pct": <number>}}
  ],
  "margin_analysis": "<2-3 sentence margin health assessment and outlook>",
  "margin_scenarios": [
    {{"scenario": "<e.g. RM price +10%>", "margin_pct": <number>}}
  ]
}}

Rules:
- pricing_options: provide exactly 3 (conservative, target, aggressive)
- cost_flags: 2-5 flags, at least one "positive" if warranted
- material_suggestions: 1-3 concrete suggestions
- margin_scenarios: exactly 3 (base case, RM +10%, RM -10%)
- All prices in INR, margin_pct and estimated_saving_pct as percentages (e.g. 15.5 not 0.155)
- Be specific to the actual data, not generic"""

    try:
        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = message.content[0].text.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        data = json.loads(raw)
        return AiInsights(**data)
    except json.JSONDecodeError as e:
        log.warning("AI response JSON parse error: %s", e)
        raise HTTPException(status_code=502, detail="AI returned invalid JSON")
    except anthropic.APIError as e:
        log.warning("Anthropic API error: %s", e)
        raise HTTPException(status_code=502, detail=f"AI service error: {e}")
