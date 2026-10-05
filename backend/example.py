"""
Pre-seed script — recreates the exact data captured from a live run of this app.
Idempotent: safe to run against a fresh OR already-seeded database (ON CONFLICT DO NOTHING).

Usage (from backend/ dir, inside the container or a venv with DATABASE_URL set):
    python example.py
"""
from __future__ import annotations

import json
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import text

from app.database import engine


CLIENTS = [
    {'id': 1, 'name': 'Demo Client', 'created_at': datetime(2026, 10, 4, 14, 51, 5, 540314)},
    {'id': 2, 'name': 'TLD', 'created_at': datetime(2026, 10, 5, 9, 6, 8, 659085)},
]

MATERIAL_GRADES = [
    {'id': 1, 'name': 'IS2062 E250BR', 'base_grade_id': None, 'premium_amount': None, 'updated_at': datetime(2026, 10, 4, 14, 47, 59, 453875)},
    {'id': 2, 'name': 'IS2062 E350C', 'base_grade_id': 1, 'premium_amount': Decimal('4.5000'), 'updated_at': datetime(2026, 10, 5, 9, 6, 8, 714964)},
]

NORM_LIBRARIES = [
    {'id': 1, 'client_id': 1, 'label': 'Original Version', 'effective_date': date(2026, 10, 4), 'is_current': False, 'is_draft': True, 'created_at': datetime(2026, 10, 4, 14, 51, 13, 216217)},
    {'id': 2, 'client_id': 1, 'label': 'Version 2026 2027', 'effective_date': date(2026, 10, 4), 'is_current': False, 'is_draft': False, 'created_at': datetime(2026, 10, 4, 14, 51, 24, 65362)},
    {'id': 4, 'client_id': 1, 'label': 'Version 2026 2027 (copy)', 'effective_date': date(2026, 10, 5), 'is_current': True, 'is_draft': False, 'created_at': datetime(2026, 10, 5, 7, 34, 23, 246000)},
    {'id': 5, 'client_id': 2, 'label': 'TLD Norms v4.5 (06-Apr-2026)', 'effective_date': date(2026, 4, 6), 'is_current': True, 'is_draft': False, 'created_at': datetime(2026, 10, 5, 9, 6, 8, 686656)},
]

RM_PRICE_BANDS = [
    {'id': 1, 'norm_library_id': 1, 'grade_id': 1, 'thickness_band': '<10mm', 'price_per_kg': Decimal('62.5000'), 'updated_at': datetime(2026, 10, 4, 14, 51, 13, 215671)},
    {'id': 2, 'norm_library_id': 1, 'grade_id': 1, 'thickness_band': '12mm', 'price_per_kg': Decimal('62.5000'), 'updated_at': datetime(2026, 10, 4, 14, 51, 13, 215671)},
    {'id': 3, 'norm_library_id': 1, 'grade_id': 1, 'thickness_band': '>12-19mm', 'price_per_kg': Decimal('62.5000'), 'updated_at': datetime(2026, 10, 4, 14, 51, 13, 215671)},
    {'id': 4, 'norm_library_id': 1, 'grade_id': 1, 'thickness_band': '20mm', 'price_per_kg': Decimal('64.0000'), 'updated_at': datetime(2026, 10, 4, 14, 51, 13, 215671)},
    {'id': 5, 'norm_library_id': 1, 'grade_id': 1, 'thickness_band': '>20-40mm', 'price_per_kg': Decimal('65.4000'), 'updated_at': datetime(2026, 10, 4, 14, 51, 13, 215671)},
    {'id': 6, 'norm_library_id': 1, 'grade_id': 1, 'thickness_band': '>40-63mm', 'price_per_kg': Decimal('55.8000'), 'updated_at': datetime(2026, 10, 4, 14, 51, 13, 215671)},
    {'id': 7, 'norm_library_id': 1, 'grade_id': 1, 'thickness_band': '80mm', 'price_per_kg': Decimal('73.7500'), 'updated_at': datetime(2026, 10, 4, 14, 51, 13, 215671)},
    {'id': 8, 'norm_library_id': 1, 'grade_id': 2, 'thickness_band': '<10mm', 'price_per_kg': Decimal('0.0000'), 'updated_at': datetime(2026, 10, 4, 14, 51, 13, 215671)},
    {'id': 9, 'norm_library_id': 1, 'grade_id': 2, 'thickness_band': '12mm', 'price_per_kg': Decimal('0.0000'), 'updated_at': datetime(2026, 10, 4, 14, 51, 13, 215671)},
    {'id': 10, 'norm_library_id': 1, 'grade_id': 2, 'thickness_band': '>12-19mm', 'price_per_kg': Decimal('0.0000'), 'updated_at': datetime(2026, 10, 4, 14, 51, 13, 215671)},
    {'id': 11, 'norm_library_id': 1, 'grade_id': 2, 'thickness_band': '20mm', 'price_per_kg': Decimal('0.0000'), 'updated_at': datetime(2026, 10, 4, 14, 51, 13, 215671)},
    {'id': 12, 'norm_library_id': 1, 'grade_id': 2, 'thickness_band': '>20-40mm', 'price_per_kg': Decimal('0.0000'), 'updated_at': datetime(2026, 10, 4, 14, 51, 13, 215671)},
    {'id': 13, 'norm_library_id': 1, 'grade_id': 2, 'thickness_band': '>40-63mm', 'price_per_kg': Decimal('0.0000'), 'updated_at': datetime(2026, 10, 4, 14, 51, 13, 215671)},
    {'id': 14, 'norm_library_id': 1, 'grade_id': 2, 'thickness_band': '80mm', 'price_per_kg': Decimal('0.0000'), 'updated_at': datetime(2026, 10, 4, 14, 51, 13, 215671)},
    {'id': 15, 'norm_library_id': 2, 'grade_id': 1, 'thickness_band': '<10mm', 'price_per_kg': Decimal('75.0000'), 'updated_at': datetime(2026, 10, 5, 7, 33, 19, 487573)},
    {'id': 16, 'norm_library_id': 2, 'grade_id': 1, 'thickness_band': '12mm', 'price_per_kg': Decimal('62.5000'), 'updated_at': datetime(2026, 10, 4, 14, 51, 24, 64783)},
    {'id': 17, 'norm_library_id': 2, 'grade_id': 1, 'thickness_band': '>12-19mm', 'price_per_kg': Decimal('62.5000'), 'updated_at': datetime(2026, 10, 4, 14, 51, 24, 64783)},
    {'id': 18, 'norm_library_id': 2, 'grade_id': 1, 'thickness_band': '20mm', 'price_per_kg': Decimal('64.0000'), 'updated_at': datetime(2026, 10, 4, 14, 51, 24, 64783)},
    {'id': 19, 'norm_library_id': 2, 'grade_id': 1, 'thickness_band': '>20-40mm', 'price_per_kg': Decimal('65.4000'), 'updated_at': datetime(2026, 10, 4, 14, 51, 24, 64783)},
    {'id': 20, 'norm_library_id': 2, 'grade_id': 1, 'thickness_band': '>40-63mm', 'price_per_kg': Decimal('55.8000'), 'updated_at': datetime(2026, 10, 4, 14, 51, 24, 64783)},
    {'id': 21, 'norm_library_id': 2, 'grade_id': 1, 'thickness_band': '80mm', 'price_per_kg': Decimal('73.7500'), 'updated_at': datetime(2026, 10, 4, 14, 51, 24, 64783)},
    {'id': 22, 'norm_library_id': 2, 'grade_id': 2, 'thickness_band': '<10mm', 'price_per_kg': Decimal('0.0000'), 'updated_at': datetime(2026, 10, 4, 14, 51, 24, 64783)},
    {'id': 23, 'norm_library_id': 2, 'grade_id': 2, 'thickness_band': '12mm', 'price_per_kg': Decimal('0.0000'), 'updated_at': datetime(2026, 10, 4, 14, 51, 24, 64783)},
    {'id': 24, 'norm_library_id': 2, 'grade_id': 2, 'thickness_band': '>12-19mm', 'price_per_kg': Decimal('0.0000'), 'updated_at': datetime(2026, 10, 4, 14, 51, 24, 64783)},
    {'id': 25, 'norm_library_id': 2, 'grade_id': 2, 'thickness_band': '20mm', 'price_per_kg': Decimal('0.0000'), 'updated_at': datetime(2026, 10, 4, 14, 51, 24, 64783)},
    {'id': 26, 'norm_library_id': 2, 'grade_id': 2, 'thickness_band': '>20-40mm', 'price_per_kg': Decimal('0.0000'), 'updated_at': datetime(2026, 10, 4, 14, 51, 24, 64783)},
    {'id': 27, 'norm_library_id': 2, 'grade_id': 2, 'thickness_band': '>40-63mm', 'price_per_kg': Decimal('0.0000'), 'updated_at': datetime(2026, 10, 4, 14, 51, 24, 64783)},
    {'id': 28, 'norm_library_id': 2, 'grade_id': 2, 'thickness_band': '80mm', 'price_per_kg': Decimal('0.0000'), 'updated_at': datetime(2026, 10, 4, 14, 51, 24, 64783)},
    {'id': 43, 'norm_library_id': 4, 'grade_id': 2, 'thickness_band': '<10mm', 'price_per_kg': Decimal('0.0000'), 'updated_at': datetime(2026, 10, 5, 7, 34, 23, 245449)},
    {'id': 44, 'norm_library_id': 4, 'grade_id': 2, 'thickness_band': '12mm', 'price_per_kg': Decimal('0.0000'), 'updated_at': datetime(2026, 10, 5, 7, 34, 23, 245449)},
    {'id': 45, 'norm_library_id': 4, 'grade_id': 2, 'thickness_band': '>12-19mm', 'price_per_kg': Decimal('0.0000'), 'updated_at': datetime(2026, 10, 5, 7, 34, 23, 245449)},
    {'id': 46, 'norm_library_id': 4, 'grade_id': 2, 'thickness_band': '20mm', 'price_per_kg': Decimal('0.0000'), 'updated_at': datetime(2026, 10, 5, 7, 34, 23, 245449)},
    {'id': 47, 'norm_library_id': 4, 'grade_id': 2, 'thickness_band': '>20-40mm', 'price_per_kg': Decimal('0.0000'), 'updated_at': datetime(2026, 10, 5, 7, 34, 23, 245449)},
    {'id': 48, 'norm_library_id': 4, 'grade_id': 2, 'thickness_band': '>40-63mm', 'price_per_kg': Decimal('0.0000'), 'updated_at': datetime(2026, 10, 5, 7, 34, 23, 245449)},
    {'id': 49, 'norm_library_id': 4, 'grade_id': 2, 'thickness_band': '80mm', 'price_per_kg': Decimal('0.0000'), 'updated_at': datetime(2026, 10, 5, 7, 34, 23, 245449)},
    {'id': 50, 'norm_library_id': 4, 'grade_id': 1, 'thickness_band': '12mm', 'price_per_kg': Decimal('62.5000'), 'updated_at': datetime(2026, 10, 5, 7, 34, 23, 245449)},
    {'id': 51, 'norm_library_id': 4, 'grade_id': 1, 'thickness_band': '>12-19mm', 'price_per_kg': Decimal('62.5000'), 'updated_at': datetime(2026, 10, 5, 7, 34, 23, 245449)},
    {'id': 52, 'norm_library_id': 4, 'grade_id': 1, 'thickness_band': '20mm', 'price_per_kg': Decimal('64.0000'), 'updated_at': datetime(2026, 10, 5, 7, 34, 23, 245449)},
    {'id': 53, 'norm_library_id': 4, 'grade_id': 1, 'thickness_band': '>20-40mm', 'price_per_kg': Decimal('65.4000'), 'updated_at': datetime(2026, 10, 5, 7, 34, 23, 245449)},
    {'id': 54, 'norm_library_id': 4, 'grade_id': 1, 'thickness_band': '>40-63mm', 'price_per_kg': Decimal('55.8000'), 'updated_at': datetime(2026, 10, 5, 7, 34, 23, 245449)},
    {'id': 55, 'norm_library_id': 4, 'grade_id': 1, 'thickness_band': '80mm', 'price_per_kg': Decimal('73.7500'), 'updated_at': datetime(2026, 10, 5, 7, 34, 23, 245449)},
    {'id': 56, 'norm_library_id': 4, 'grade_id': 1, 'thickness_band': '<10mm', 'price_per_kg': Decimal('80.0000'), 'updated_at': datetime(2026, 10, 5, 7, 34, 23, 466786)},
    {'id': 57, 'norm_library_id': 5, 'grade_id': 1, 'thickness_band': '<10mm', 'price_per_kg': Decimal('70.0000'), 'updated_at': datetime(2026, 10, 5, 9, 10, 9, 112728)},
    {'id': 58, 'norm_library_id': 5, 'grade_id': 1, 'thickness_band': '12mm', 'price_per_kg': Decimal('64.5000'), 'updated_at': datetime(2026, 10, 5, 9, 6, 8, 714964)},
    {'id': 59, 'norm_library_id': 5, 'grade_id': 1, 'thickness_band': '>12-19mm', 'price_per_kg': Decimal('71.0000'), 'updated_at': datetime(2026, 10, 5, 9, 10, 9, 112728)},
    {'id': 60, 'norm_library_id': 5, 'grade_id': 1, 'thickness_band': '20mm', 'price_per_kg': Decimal('72.0000'), 'updated_at': datetime(2026, 10, 5, 9, 10, 9, 112728)},
    {'id': 61, 'norm_library_id': 5, 'grade_id': 1, 'thickness_band': '>20-40mm', 'price_per_kg': Decimal('66.9000'), 'updated_at': datetime(2026, 10, 5, 9, 6, 8, 714964)},
    {'id': 62, 'norm_library_id': 5, 'grade_id': 1, 'thickness_band': '>40-63mm', 'price_per_kg': Decimal('69.9000'), 'updated_at': datetime(2026, 10, 5, 9, 6, 8, 714964)},
    {'id': 63, 'norm_library_id': 5, 'grade_id': 1, 'thickness_band': '80mm', 'price_per_kg': Decimal('73.9000'), 'updated_at': datetime(2026, 10, 5, 9, 6, 8, 714964)},
    {'id': 64, 'norm_library_id': 5, 'grade_id': 2, 'thickness_band': '<10mm', 'price_per_kg': Decimal('0.0000'), 'updated_at': datetime(2026, 10, 5, 9, 6, 8, 685341)},
    {'id': 65, 'norm_library_id': 5, 'grade_id': 2, 'thickness_band': '12mm', 'price_per_kg': Decimal('0.0000'), 'updated_at': datetime(2026, 10, 5, 9, 6, 8, 685341)},
    {'id': 66, 'norm_library_id': 5, 'grade_id': 2, 'thickness_band': '>12-19mm', 'price_per_kg': Decimal('0.0000'), 'updated_at': datetime(2026, 10, 5, 9, 6, 8, 685341)},
    {'id': 67, 'norm_library_id': 5, 'grade_id': 2, 'thickness_band': '20mm', 'price_per_kg': Decimal('0.0000'), 'updated_at': datetime(2026, 10, 5, 9, 6, 8, 685341)},
    {'id': 68, 'norm_library_id': 5, 'grade_id': 2, 'thickness_band': '>20-40mm', 'price_per_kg': Decimal('0.0000'), 'updated_at': datetime(2026, 10, 5, 9, 6, 8, 685341)},
    {'id': 69, 'norm_library_id': 5, 'grade_id': 2, 'thickness_band': '>40-63mm', 'price_per_kg': Decimal('0.0000'), 'updated_at': datetime(2026, 10, 5, 9, 6, 8, 685341)},
    {'id': 70, 'norm_library_id': 5, 'grade_id': 2, 'thickness_band': '80mm', 'price_per_kg': Decimal('0.0000'), 'updated_at': datetime(2026, 10, 5, 9, 6, 8, 685341)},
]

SCRAP_RATES = [
    {'id': 1, 'norm_library_id': 1, 'rate_per_kg': Decimal('30.0000'), 'updated_at': datetime(2026, 10, 4, 14, 51, 13, 215671)},
    {'id': 2, 'norm_library_id': 2, 'rate_per_kg': Decimal('30.0000'), 'updated_at': datetime(2026, 10, 4, 14, 51, 24, 64783)},
    {'id': 4, 'norm_library_id': 4, 'rate_per_kg': Decimal('30.0000'), 'updated_at': datetime(2026, 10, 5, 7, 34, 23, 245449)},
    {'id': 5, 'norm_library_id': 5, 'rate_per_kg': Decimal('29.5000'), 'updated_at': datetime(2026, 10, 5, 9, 6, 8, 714964)},
]

PROCESS_RATES = [
    {'id': 1, 'norm_library_id': 1, 'operation_name': 'Process Loss', 'unit': '%', 'rate': Decimal('5.0000'), 'sort_order': 1, 'group_label': 'Material / Cutting', 'updated_at': datetime(2026, 10, 4, 14, 51, 13, 215671)},
    {'id': 2, 'norm_library_id': 1, 'operation_name': 'Plasma Cutting', 'unit': 'Rs/mm/meter', 'rate': Decimal('3.0000'), 'sort_order': 10, 'group_label': 'Material / Cutting', 'updated_at': datetime(2026, 10, 4, 14, 51, 13, 215671)},
    {'id': 3, 'norm_library_id': 1, 'operation_name': 'Laser Cutting', 'unit': 'Rs/mm/meter', 'rate': Decimal('5.5000'), 'sort_order': 20, 'group_label': 'Material / Cutting', 'updated_at': datetime(2026, 10, 4, 14, 51, 13, 215671)},
    {'id': 4, 'norm_library_id': 1, 'operation_name': 'Bevelling', 'unit': 'Rs/slant/meter', 'rate': Decimal('4.0000'), 'sort_order': 30, 'group_label': 'Material / Cutting', 'updated_at': datetime(2026, 10, 4, 14, 51, 13, 215671)},
    {'id': 5, 'norm_library_id': 1, 'operation_name': '1 Bend', 'unit': 'Rs/Kg', 'rate': Decimal('4.0000'), 'sort_order': 10, 'group_label': 'Forming', 'updated_at': datetime(2026, 10, 4, 14, 51, 13, 215671)},
    {'id': 6, 'norm_library_id': 1, 'operation_name': '2 Bend', 'unit': 'Rs/Kg', 'rate': Decimal('6.0000'), 'sort_order': 20, 'group_label': 'Forming', 'updated_at': datetime(2026, 10, 4, 14, 51, 13, 215671)},
    {'id': 7, 'norm_library_id': 1, 'operation_name': '3 Bend', 'unit': 'Rs/Kg', 'rate': Decimal('7.0000'), 'sort_order': 30, 'group_label': 'Forming', 'updated_at': datetime(2026, 10, 4, 14, 51, 13, 215671)},
    {'id': 8, 'norm_library_id': 1, 'operation_name': 'Rolling', 'unit': 'Rs/Kg', 'rate': Decimal('5.0000'), 'sort_order': 40, 'group_label': 'Forming', 'updated_at': datetime(2026, 10, 4, 14, 51, 13, 215671)},
    {'id': 9, 'norm_library_id': 1, 'operation_name': 'Channel Rolling', 'unit': 'Rs/Kg', 'rate': Decimal('11.7000'), 'sort_order': 50, 'group_label': 'Forming', 'updated_at': datetime(2026, 10, 4, 14, 51, 13, 215671)},
    {'id': 10, 'norm_library_id': 1, 'operation_name': 'Drilling', 'unit': 'Rs/Hr', 'rate': Decimal('200.0000'), 'sort_order': 10, 'group_label': 'Drilling', 'updated_at': datetime(2026, 10, 4, 14, 51, 13, 215671)},
    {'id': 11, 'norm_library_id': 1, 'operation_name': 'Drilling (EH/Hiten)', 'unit': 'Rs/Hr', 'rate': Decimal('350.0000'), 'sort_order': 20, 'group_label': 'Drilling', 'updated_at': datetime(2026, 10, 4, 14, 51, 13, 215671)},
    {'id': 12, 'norm_library_id': 1, 'operation_name': 'Drilling (EHC450/EHC500)', 'unit': 'Rs/Hr', 'rate': Decimal('500.0000'), 'sort_order': 30, 'group_label': 'Drilling', 'updated_at': datetime(2026, 10, 4, 14, 51, 13, 215671)},
    {'id': 13, 'norm_library_id': 1, 'operation_name': 'Tack Welding', 'unit': 'Rs/Hr', 'rate': Decimal('300.0000'), 'sort_order': 10, 'group_label': 'Welding / Finishing', 'updated_at': datetime(2026, 10, 4, 14, 51, 13, 215671)},
    {'id': 14, 'norm_library_id': 1, 'operation_name': 'Full Welding (solid wire)', 'unit': 'Rs/Kg', 'rate': Decimal('300.0000'), 'sort_order': 20, 'group_label': 'Welding / Finishing', 'updated_at': datetime(2026, 10, 4, 14, 51, 13, 215671)},
    {'id': 15, 'norm_library_id': 1, 'operation_name': 'Dressing', 'unit': 'Rs/Hr', 'rate': Decimal('225.0000'), 'sort_order': 30, 'group_label': 'Welding / Finishing', 'updated_at': datetime(2026, 10, 4, 14, 51, 13, 215671)},
    {'id': 16, 'norm_library_id': 1, 'operation_name': 'Sandering', 'unit': 'Rs/Hr', 'rate': Decimal('225.0000'), 'sort_order': 40, 'group_label': 'Welding / Finishing', 'updated_at': datetime(2026, 10, 4, 14, 51, 13, 215671)},
    {'id': 17, 'norm_library_id': 1, 'operation_name': 'Gauging', 'unit': 'Rs/Hr', 'rate': Decimal('300.0000'), 'sort_order': 50, 'group_label': 'Welding / Finishing', 'updated_at': datetime(2026, 10, 4, 14, 51, 13, 215671)},
    {'id': 18, 'norm_library_id': 1, 'operation_name': 'Preheating / Heat Correction', 'unit': 'Rs/Hr', 'rate': Decimal('300.0000'), 'sort_order': 60, 'group_label': 'Welding / Finishing', 'updated_at': datetime(2026, 10, 4, 14, 51, 13, 215671)},
    {'id': 19, 'norm_library_id': 1, 'operation_name': 'Straightening', 'unit': 'Rs/Kg', 'rate': Decimal('2.0000'), 'sort_order': 70, 'group_label': 'Welding / Finishing', 'updated_at': datetime(2026, 10, 4, 14, 51, 13, 215671)},
    {'id': 20, 'norm_library_id': 1, 'operation_name': 'Stud Welding', 'unit': 'Rs/Nos', 'rate': Decimal('39.0000'), 'sort_order': 80, 'group_label': 'Welding / Finishing', 'updated_at': datetime(2026, 10, 4, 14, 51, 13, 215671)},
    {'id': 21, 'norm_library_id': 1, 'operation_name': 'Hard Facing Charges', 'unit': 'Rs/Kg', 'rate': Decimal('292.5000'), 'sort_order': 90, 'group_label': 'Welding / Finishing', 'updated_at': datetime(2026, 10, 4, 14, 51, 13, 215671)},
    {'id': 22, 'norm_library_id': 1, 'operation_name': 'Hard Facing', 'unit': 'Rs/Kg', 'rate': Decimal('316.8750'), 'sort_order': 100, 'group_label': 'Welding / Finishing', 'updated_at': datetime(2026, 10, 4, 14, 51, 13, 215671)},
    {'id': 23, 'norm_library_id': 1, 'operation_name': 'Shot Blasting', 'unit': 'Rs/Kg', 'rate': Decimal('1.7500'), 'sort_order': 10, 'group_label': 'Surface Treatment', 'updated_at': datetime(2026, 10, 4, 14, 51, 13, 215671)},
    {'id': 24, 'norm_library_id': 1, 'operation_name': 'Zinc Plating', 'unit': 'Rs/Kg', 'rate': Decimal('30.0000'), 'sort_order': 20, 'group_label': 'Surface Treatment', 'updated_at': datetime(2026, 10, 4, 14, 51, 13, 215671)},
    {'id': 25, 'norm_library_id': 1, 'operation_name': 'Final Painting (Primer + Final Coat)', 'unit': 'Rs/Sqm', 'rate': Decimal('575.0000'), 'sort_order': 30, 'group_label': 'Surface Treatment', 'updated_at': datetime(2026, 10, 4, 14, 51, 13, 215671)},
    {'id': 26, 'norm_library_id': 1, 'operation_name': 'Galvanizing', 'unit': 'Rs/Kg', 'rate': Decimal('40.0000'), 'sort_order': 40, 'group_label': 'Surface Treatment', 'updated_at': datetime(2026, 10, 4, 14, 51, 13, 215671)},
    {'id': 27, 'norm_library_id': 1, 'operation_name': 'Hardening', 'unit': 'Rs/Hr', 'rate': Decimal('195.0000'), 'sort_order': 50, 'group_label': 'Surface Treatment', 'updated_at': datetime(2026, 10, 4, 14, 51, 13, 215671)},
    {'id': 28, 'norm_library_id': 1, 'operation_name': 'Sub Transport', 'unit': 'Rs/Kg', 'rate': Decimal('2.5000'), 'sort_order': 10, 'group_label': 'Other', 'updated_at': datetime(2026, 10, 4, 14, 51, 13, 215671)},
    {'id': 29, 'norm_library_id': 1, 'operation_name': 'Machining (VTL)', 'unit': 'Rs/Hr', 'rate': Decimal('500.0000'), 'sort_order': 20, 'group_label': 'Other', 'updated_at': datetime(2026, 10, 4, 14, 51, 13, 215671)},
    {'id': 30, 'norm_library_id': 1, 'operation_name': 'Bush Fitting', 'unit': 'Rs/Nos', 'rate': Decimal('175.0000'), 'sort_order': 30, 'group_label': 'Other', 'updated_at': datetime(2026, 10, 4, 14, 51, 13, 215671)},
    {'id': 31, 'norm_library_id': 2, 'operation_name': 'Process Loss', 'unit': '%', 'rate': Decimal('5.0000'), 'sort_order': 1, 'group_label': 'Material / Cutting', 'updated_at': datetime(2026, 10, 4, 14, 51, 24, 64783)},
    {'id': 32, 'norm_library_id': 2, 'operation_name': 'Plasma Cutting', 'unit': 'Rs/mm/meter', 'rate': Decimal('3.0000'), 'sort_order': 10, 'group_label': 'Material / Cutting', 'updated_at': datetime(2026, 10, 4, 14, 51, 24, 64783)},
    {'id': 33, 'norm_library_id': 2, 'operation_name': 'Laser Cutting', 'unit': 'Rs/mm/meter', 'rate': Decimal('5.5000'), 'sort_order': 20, 'group_label': 'Material / Cutting', 'updated_at': datetime(2026, 10, 4, 14, 51, 24, 64783)},
    {'id': 34, 'norm_library_id': 2, 'operation_name': 'Bevelling', 'unit': 'Rs/slant/meter', 'rate': Decimal('4.0000'), 'sort_order': 30, 'group_label': 'Material / Cutting', 'updated_at': datetime(2026, 10, 4, 14, 51, 24, 64783)},
    {'id': 35, 'norm_library_id': 2, 'operation_name': '1 Bend', 'unit': 'Rs/Kg', 'rate': Decimal('4.0000'), 'sort_order': 10, 'group_label': 'Forming', 'updated_at': datetime(2026, 10, 4, 14, 51, 24, 64783)},
    {'id': 36, 'norm_library_id': 2, 'operation_name': '2 Bend', 'unit': 'Rs/Kg', 'rate': Decimal('6.0000'), 'sort_order': 20, 'group_label': 'Forming', 'updated_at': datetime(2026, 10, 4, 14, 51, 24, 64783)},
    {'id': 37, 'norm_library_id': 2, 'operation_name': '3 Bend', 'unit': 'Rs/Kg', 'rate': Decimal('7.0000'), 'sort_order': 30, 'group_label': 'Forming', 'updated_at': datetime(2026, 10, 4, 14, 51, 24, 64783)},
    {'id': 38, 'norm_library_id': 2, 'operation_name': 'Rolling', 'unit': 'Rs/Kg', 'rate': Decimal('5.0000'), 'sort_order': 40, 'group_label': 'Forming', 'updated_at': datetime(2026, 10, 4, 14, 51, 24, 64783)},
    {'id': 39, 'norm_library_id': 2, 'operation_name': 'Channel Rolling', 'unit': 'Rs/Kg', 'rate': Decimal('11.7000'), 'sort_order': 50, 'group_label': 'Forming', 'updated_at': datetime(2026, 10, 4, 14, 51, 24, 64783)},
    {'id': 40, 'norm_library_id': 2, 'operation_name': 'Drilling', 'unit': 'Rs/Hr', 'rate': Decimal('200.0000'), 'sort_order': 10, 'group_label': 'Drilling', 'updated_at': datetime(2026, 10, 4, 14, 51, 24, 64783)},
    {'id': 41, 'norm_library_id': 2, 'operation_name': 'Drilling (EH/Hiten)', 'unit': 'Rs/Hr', 'rate': Decimal('350.0000'), 'sort_order': 20, 'group_label': 'Drilling', 'updated_at': datetime(2026, 10, 4, 14, 51, 24, 64783)},
    {'id': 42, 'norm_library_id': 2, 'operation_name': 'Drilling (EHC450/EHC500)', 'unit': 'Rs/Hr', 'rate': Decimal('500.0000'), 'sort_order': 30, 'group_label': 'Drilling', 'updated_at': datetime(2026, 10, 4, 14, 51, 24, 64783)},
    {'id': 43, 'norm_library_id': 2, 'operation_name': 'Tack Welding', 'unit': 'Rs/Hr', 'rate': Decimal('300.0000'), 'sort_order': 10, 'group_label': 'Welding / Finishing', 'updated_at': datetime(2026, 10, 4, 14, 51, 24, 64783)},
    {'id': 44, 'norm_library_id': 2, 'operation_name': 'Full Welding (solid wire)', 'unit': 'Rs/Kg', 'rate': Decimal('300.0000'), 'sort_order': 20, 'group_label': 'Welding / Finishing', 'updated_at': datetime(2026, 10, 4, 14, 51, 24, 64783)},
    {'id': 45, 'norm_library_id': 2, 'operation_name': 'Dressing', 'unit': 'Rs/Hr', 'rate': Decimal('225.0000'), 'sort_order': 30, 'group_label': 'Welding / Finishing', 'updated_at': datetime(2026, 10, 4, 14, 51, 24, 64783)},
    {'id': 46, 'norm_library_id': 2, 'operation_name': 'Sandering', 'unit': 'Rs/Hr', 'rate': Decimal('225.0000'), 'sort_order': 40, 'group_label': 'Welding / Finishing', 'updated_at': datetime(2026, 10, 4, 14, 51, 24, 64783)},
    {'id': 47, 'norm_library_id': 2, 'operation_name': 'Gauging', 'unit': 'Rs/Hr', 'rate': Decimal('300.0000'), 'sort_order': 50, 'group_label': 'Welding / Finishing', 'updated_at': datetime(2026, 10, 4, 14, 51, 24, 64783)},
    {'id': 48, 'norm_library_id': 2, 'operation_name': 'Preheating / Heat Correction', 'unit': 'Rs/Hr', 'rate': Decimal('300.0000'), 'sort_order': 60, 'group_label': 'Welding / Finishing', 'updated_at': datetime(2026, 10, 4, 14, 51, 24, 64783)},
    {'id': 49, 'norm_library_id': 2, 'operation_name': 'Straightening', 'unit': 'Rs/Kg', 'rate': Decimal('2.0000'), 'sort_order': 70, 'group_label': 'Welding / Finishing', 'updated_at': datetime(2026, 10, 4, 14, 51, 24, 64783)},
    {'id': 50, 'norm_library_id': 2, 'operation_name': 'Stud Welding', 'unit': 'Rs/Nos', 'rate': Decimal('39.0000'), 'sort_order': 80, 'group_label': 'Welding / Finishing', 'updated_at': datetime(2026, 10, 4, 14, 51, 24, 64783)},
    {'id': 51, 'norm_library_id': 2, 'operation_name': 'Hard Facing Charges', 'unit': 'Rs/Kg', 'rate': Decimal('292.5000'), 'sort_order': 90, 'group_label': 'Welding / Finishing', 'updated_at': datetime(2026, 10, 4, 14, 51, 24, 64783)},
    {'id': 52, 'norm_library_id': 2, 'operation_name': 'Hard Facing', 'unit': 'Rs/Kg', 'rate': Decimal('316.8750'), 'sort_order': 100, 'group_label': 'Welding / Finishing', 'updated_at': datetime(2026, 10, 4, 14, 51, 24, 64783)},
    {'id': 53, 'norm_library_id': 2, 'operation_name': 'Shot Blasting', 'unit': 'Rs/Kg', 'rate': Decimal('1.7500'), 'sort_order': 10, 'group_label': 'Surface Treatment', 'updated_at': datetime(2026, 10, 4, 14, 51, 24, 64783)},
    {'id': 54, 'norm_library_id': 2, 'operation_name': 'Zinc Plating', 'unit': 'Rs/Kg', 'rate': Decimal('30.0000'), 'sort_order': 20, 'group_label': 'Surface Treatment', 'updated_at': datetime(2026, 10, 4, 14, 51, 24, 64783)},
    {'id': 55, 'norm_library_id': 2, 'operation_name': 'Final Painting (Primer + Final Coat)', 'unit': 'Rs/Sqm', 'rate': Decimal('575.0000'), 'sort_order': 30, 'group_label': 'Surface Treatment', 'updated_at': datetime(2026, 10, 4, 14, 51, 24, 64783)},
    {'id': 56, 'norm_library_id': 2, 'operation_name': 'Galvanizing', 'unit': 'Rs/Kg', 'rate': Decimal('40.0000'), 'sort_order': 40, 'group_label': 'Surface Treatment', 'updated_at': datetime(2026, 10, 4, 14, 51, 24, 64783)},
    {'id': 57, 'norm_library_id': 2, 'operation_name': 'Hardening', 'unit': 'Rs/Hr', 'rate': Decimal('195.0000'), 'sort_order': 50, 'group_label': 'Surface Treatment', 'updated_at': datetime(2026, 10, 4, 14, 51, 24, 64783)},
    {'id': 58, 'norm_library_id': 2, 'operation_name': 'Sub Transport', 'unit': 'Rs/Kg', 'rate': Decimal('2.5000'), 'sort_order': 10, 'group_label': 'Other', 'updated_at': datetime(2026, 10, 4, 14, 51, 24, 64783)},
    {'id': 59, 'norm_library_id': 2, 'operation_name': 'Machining (VTL)', 'unit': 'Rs/Hr', 'rate': Decimal('500.0000'), 'sort_order': 20, 'group_label': 'Other', 'updated_at': datetime(2026, 10, 4, 14, 51, 24, 64783)},
    {'id': 60, 'norm_library_id': 2, 'operation_name': 'Bush Fitting', 'unit': 'Rs/Nos', 'rate': Decimal('175.0000'), 'sort_order': 30, 'group_label': 'Other', 'updated_at': datetime(2026, 10, 4, 14, 51, 24, 64783)},
    {'id': 91, 'norm_library_id': 4, 'operation_name': 'Process Loss', 'unit': '%', 'rate': Decimal('5.0000'), 'sort_order': 1, 'group_label': 'Material / Cutting', 'updated_at': datetime(2026, 10, 5, 7, 34, 23, 245449)},
    {'id': 92, 'norm_library_id': 4, 'operation_name': 'Shot Blasting', 'unit': 'Rs/Kg', 'rate': Decimal('1.7500'), 'sort_order': 10, 'group_label': 'Surface Treatment', 'updated_at': datetime(2026, 10, 5, 7, 34, 23, 245449)},
    {'id': 93, 'norm_library_id': 4, 'operation_name': 'Drilling', 'unit': 'Rs/Hr', 'rate': Decimal('200.0000'), 'sort_order': 10, 'group_label': 'Drilling', 'updated_at': datetime(2026, 10, 5, 7, 34, 23, 245449)},
    {'id': 94, 'norm_library_id': 4, 'operation_name': 'Sub Transport', 'unit': 'Rs/Kg', 'rate': Decimal('2.5000'), 'sort_order': 10, 'group_label': 'Other', 'updated_at': datetime(2026, 10, 5, 7, 34, 23, 245449)},
    {'id': 95, 'norm_library_id': 4, 'operation_name': 'Plasma Cutting', 'unit': 'Rs/mm/meter', 'rate': Decimal('3.0000'), 'sort_order': 10, 'group_label': 'Material / Cutting', 'updated_at': datetime(2026, 10, 5, 7, 34, 23, 245449)},
    {'id': 96, 'norm_library_id': 4, 'operation_name': 'Tack Welding', 'unit': 'Rs/Hr', 'rate': Decimal('300.0000'), 'sort_order': 10, 'group_label': 'Welding / Finishing', 'updated_at': datetime(2026, 10, 5, 7, 34, 23, 245449)},
    {'id': 97, 'norm_library_id': 4, 'operation_name': '1 Bend', 'unit': 'Rs/Kg', 'rate': Decimal('4.0000'), 'sort_order': 10, 'group_label': 'Forming', 'updated_at': datetime(2026, 10, 5, 7, 34, 23, 245449)},
    {'id': 98, 'norm_library_id': 4, 'operation_name': 'Laser Cutting', 'unit': 'Rs/mm/meter', 'rate': Decimal('5.5000'), 'sort_order': 20, 'group_label': 'Material / Cutting', 'updated_at': datetime(2026, 10, 5, 7, 34, 23, 245449)},
    {'id': 99, 'norm_library_id': 4, 'operation_name': 'Zinc Plating', 'unit': 'Rs/Kg', 'rate': Decimal('30.0000'), 'sort_order': 20, 'group_label': 'Surface Treatment', 'updated_at': datetime(2026, 10, 5, 7, 34, 23, 245449)},
    {'id': 100, 'norm_library_id': 4, 'operation_name': '2 Bend', 'unit': 'Rs/Kg', 'rate': Decimal('6.0000'), 'sort_order': 20, 'group_label': 'Forming', 'updated_at': datetime(2026, 10, 5, 7, 34, 23, 245449)},
    {'id': 101, 'norm_library_id': 4, 'operation_name': 'Full Welding (solid wire)', 'unit': 'Rs/Kg', 'rate': Decimal('300.0000'), 'sort_order': 20, 'group_label': 'Welding / Finishing', 'updated_at': datetime(2026, 10, 5, 7, 34, 23, 245449)},
    {'id': 102, 'norm_library_id': 4, 'operation_name': 'Machining (VTL)', 'unit': 'Rs/Hr', 'rate': Decimal('500.0000'), 'sort_order': 20, 'group_label': 'Other', 'updated_at': datetime(2026, 10, 5, 7, 34, 23, 245449)},
    {'id': 103, 'norm_library_id': 4, 'operation_name': 'Drilling (EH/Hiten)', 'unit': 'Rs/Hr', 'rate': Decimal('350.0000'), 'sort_order': 20, 'group_label': 'Drilling', 'updated_at': datetime(2026, 10, 5, 7, 34, 23, 245449)},
    {'id': 104, 'norm_library_id': 4, 'operation_name': 'Bush Fitting', 'unit': 'Rs/Nos', 'rate': Decimal('175.0000'), 'sort_order': 30, 'group_label': 'Other', 'updated_at': datetime(2026, 10, 5, 7, 34, 23, 245449)},
    {'id': 105, 'norm_library_id': 4, 'operation_name': 'Bevelling', 'unit': 'Rs/slant/meter', 'rate': Decimal('4.0000'), 'sort_order': 30, 'group_label': 'Material / Cutting', 'updated_at': datetime(2026, 10, 5, 7, 34, 23, 245449)},
    {'id': 106, 'norm_library_id': 4, 'operation_name': '3 Bend', 'unit': 'Rs/Kg', 'rate': Decimal('7.0000'), 'sort_order': 30, 'group_label': 'Forming', 'updated_at': datetime(2026, 10, 5, 7, 34, 23, 245449)},
    {'id': 107, 'norm_library_id': 4, 'operation_name': 'Drilling (EHC450/EHC500)', 'unit': 'Rs/Hr', 'rate': Decimal('500.0000'), 'sort_order': 30, 'group_label': 'Drilling', 'updated_at': datetime(2026, 10, 5, 7, 34, 23, 245449)},
    {'id': 108, 'norm_library_id': 4, 'operation_name': 'Dressing', 'unit': 'Rs/Hr', 'rate': Decimal('225.0000'), 'sort_order': 30, 'group_label': 'Welding / Finishing', 'updated_at': datetime(2026, 10, 5, 7, 34, 23, 245449)},
    {'id': 109, 'norm_library_id': 4, 'operation_name': 'Final Painting (Primer + Final Coat)', 'unit': 'Rs/Sqm', 'rate': Decimal('575.0000'), 'sort_order': 30, 'group_label': 'Surface Treatment', 'updated_at': datetime(2026, 10, 5, 7, 34, 23, 245449)},
    {'id': 110, 'norm_library_id': 4, 'operation_name': 'Galvanizing', 'unit': 'Rs/Kg', 'rate': Decimal('40.0000'), 'sort_order': 40, 'group_label': 'Surface Treatment', 'updated_at': datetime(2026, 10, 5, 7, 34, 23, 245449)},
    {'id': 111, 'norm_library_id': 4, 'operation_name': 'Sandering', 'unit': 'Rs/Hr', 'rate': Decimal('225.0000'), 'sort_order': 40, 'group_label': 'Welding / Finishing', 'updated_at': datetime(2026, 10, 5, 7, 34, 23, 245449)},
    {'id': 112, 'norm_library_id': 4, 'operation_name': 'Rolling', 'unit': 'Rs/Kg', 'rate': Decimal('5.0000'), 'sort_order': 40, 'group_label': 'Forming', 'updated_at': datetime(2026, 10, 5, 7, 34, 23, 245449)},
    {'id': 113, 'norm_library_id': 4, 'operation_name': 'Channel Rolling', 'unit': 'Rs/Kg', 'rate': Decimal('11.7000'), 'sort_order': 50, 'group_label': 'Forming', 'updated_at': datetime(2026, 10, 5, 7, 34, 23, 245449)},
    {'id': 114, 'norm_library_id': 4, 'operation_name': 'Hardening', 'unit': 'Rs/Hr', 'rate': Decimal('195.0000'), 'sort_order': 50, 'group_label': 'Surface Treatment', 'updated_at': datetime(2026, 10, 5, 7, 34, 23, 245449)},
    {'id': 115, 'norm_library_id': 4, 'operation_name': 'Gauging', 'unit': 'Rs/Hr', 'rate': Decimal('300.0000'), 'sort_order': 50, 'group_label': 'Welding / Finishing', 'updated_at': datetime(2026, 10, 5, 7, 34, 23, 245449)},
    {'id': 116, 'norm_library_id': 4, 'operation_name': 'Preheating / Heat Correction', 'unit': 'Rs/Hr', 'rate': Decimal('300.0000'), 'sort_order': 60, 'group_label': 'Welding / Finishing', 'updated_at': datetime(2026, 10, 5, 7, 34, 23, 245449)},
    {'id': 117, 'norm_library_id': 4, 'operation_name': 'Straightening', 'unit': 'Rs/Kg', 'rate': Decimal('2.0000'), 'sort_order': 70, 'group_label': 'Welding / Finishing', 'updated_at': datetime(2026, 10, 5, 7, 34, 23, 245449)},
    {'id': 118, 'norm_library_id': 4, 'operation_name': 'Stud Welding', 'unit': 'Rs/Nos', 'rate': Decimal('39.0000'), 'sort_order': 80, 'group_label': 'Welding / Finishing', 'updated_at': datetime(2026, 10, 5, 7, 34, 23, 245449)},
    {'id': 119, 'norm_library_id': 4, 'operation_name': 'Hard Facing Charges', 'unit': 'Rs/Kg', 'rate': Decimal('292.5000'), 'sort_order': 90, 'group_label': 'Welding / Finishing', 'updated_at': datetime(2026, 10, 5, 7, 34, 23, 245449)},
    {'id': 120, 'norm_library_id': 4, 'operation_name': 'Hard Facing', 'unit': 'Rs/Kg', 'rate': Decimal('316.8750'), 'sort_order': 100, 'group_label': 'Welding / Finishing', 'updated_at': datetime(2026, 10, 5, 7, 34, 23, 245449)},
    {'id': 121, 'norm_library_id': 5, 'operation_name': 'Process Loss', 'unit': '%', 'rate': Decimal('5.0000'), 'sort_order': 1, 'group_label': 'Material / Cutting', 'updated_at': datetime(2026, 10, 5, 9, 6, 8, 780419)},
    {'id': 122, 'norm_library_id': 5, 'operation_name': 'Plasma Cutting', 'unit': 'Rs/mm/meter', 'rate': Decimal('4.0000'), 'sort_order': 2, 'group_label': 'Material / Cutting', 'updated_at': datetime(2026, 10, 5, 9, 6, 8, 801061)},
    {'id': 123, 'norm_library_id': 5, 'operation_name': 'Laser Cutting', 'unit': 'Rs/mm/meter', 'rate': Decimal('8.0000'), 'sort_order': 3, 'group_label': 'Material / Cutting', 'updated_at': datetime(2026, 10, 5, 9, 6, 8, 816598)},
    {'id': 124, 'norm_library_id': 5, 'operation_name': 'Bevelling', 'unit': 'Rs/slant/meter', 'rate': Decimal('2.0000'), 'sort_order': 4, 'group_label': 'Material / Cutting', 'updated_at': datetime(2026, 10, 5, 9, 6, 8, 830920)},
    {'id': 125, 'norm_library_id': 5, 'operation_name': '1 Bend', 'unit': 'Rs/Kg', 'rate': Decimal('4.0000'), 'sort_order': 1, 'group_label': 'Forming', 'updated_at': datetime(2026, 10, 5, 9, 6, 8, 844377)},
    {'id': 126, 'norm_library_id': 5, 'operation_name': '2 Bend', 'unit': 'Rs/Kg', 'rate': Decimal('6.0000'), 'sort_order': 2, 'group_label': 'Forming', 'updated_at': datetime(2026, 10, 5, 9, 6, 8, 857046)},
    {'id': 127, 'norm_library_id': 5, 'operation_name': '3 Bend', 'unit': 'Rs/Kg', 'rate': Decimal('7.0000'), 'sort_order': 3, 'group_label': 'Forming', 'updated_at': datetime(2026, 10, 5, 9, 6, 8, 873097)},
    {'id': 128, 'norm_library_id': 5, 'operation_name': 'Rolling', 'unit': 'Rs/Kg', 'rate': Decimal('4.0000'), 'sort_order': 4, 'group_label': 'Forming', 'updated_at': datetime(2026, 10, 5, 9, 6, 8, 888201)},
    {'id': 129, 'norm_library_id': 5, 'operation_name': 'Drilling', 'unit': 'Rs/Hr', 'rate': Decimal('200.0000'), 'sort_order': 1, 'group_label': 'Drilling', 'updated_at': datetime(2026, 10, 5, 9, 6, 8, 903022)},
    {'id': 130, 'norm_library_id': 5, 'operation_name': 'Drilling (EH/Hiten)', 'unit': 'Rs/Hr', 'rate': Decimal('350.0000'), 'sort_order': 2, 'group_label': 'Drilling', 'updated_at': datetime(2026, 10, 5, 9, 6, 8, 919313)},
    {'id': 131, 'norm_library_id': 5, 'operation_name': 'Drilling (EHC450/EHC500)', 'unit': 'Rs/Hr', 'rate': Decimal('500.0000'), 'sort_order': 3, 'group_label': 'Drilling', 'updated_at': datetime(2026, 10, 5, 9, 6, 8, 934266)},
    {'id': 132, 'norm_library_id': 5, 'operation_name': 'Tack Welding', 'unit': 'Rs/Hr', 'rate': Decimal('300.0000'), 'sort_order': 1, 'group_label': 'Welding / Finishing', 'updated_at': datetime(2026, 10, 5, 9, 6, 8, 949959)},
    {'id': 133, 'norm_library_id': 5, 'operation_name': 'Full Welding (solid wire)', 'unit': 'Rs/Kg', 'rate': Decimal('245.0000'), 'sort_order': 2, 'group_label': 'Welding / Finishing', 'updated_at': datetime(2026, 10, 5, 9, 6, 8, 964964)},
    {'id': 134, 'norm_library_id': 5, 'operation_name': 'Dressing', 'unit': 'Rs/Hr', 'rate': Decimal('200.0000'), 'sort_order': 3, 'group_label': 'Welding / Finishing', 'updated_at': datetime(2026, 10, 5, 9, 6, 8, 981012)},
    {'id': 135, 'norm_library_id': 5, 'operation_name': 'Sandering', 'unit': 'Rs/Hr', 'rate': Decimal('200.0000'), 'sort_order': 4, 'group_label': 'Welding / Finishing', 'updated_at': datetime(2026, 10, 5, 9, 6, 8, 996964)},
    {'id': 136, 'norm_library_id': 5, 'operation_name': 'Gauging', 'unit': 'Rs/Hr', 'rate': Decimal('290.0000'), 'sort_order': 5, 'group_label': 'Welding / Finishing', 'updated_at': datetime(2026, 10, 5, 9, 6, 9, 11574)},
    {'id': 137, 'norm_library_id': 5, 'operation_name': 'Preheating / Heat Correction', 'unit': 'Rs/Hr', 'rate': Decimal('290.0000'), 'sort_order': 6, 'group_label': 'Welding / Finishing', 'updated_at': datetime(2026, 10, 5, 9, 6, 9, 26816)},
    {'id': 138, 'norm_library_id': 5, 'operation_name': 'Straightening', 'unit': 'Rs/Kg', 'rate': Decimal('2.0000'), 'sort_order': 7, 'group_label': 'Welding / Finishing', 'updated_at': datetime(2026, 10, 5, 9, 6, 9, 40671)},
    {'id': 139, 'norm_library_id': 5, 'operation_name': 'Shot Blasting', 'unit': 'Rs/Kg', 'rate': Decimal('1.7500'), 'sort_order': 1, 'group_label': 'Surface Treatment', 'updated_at': datetime(2026, 10, 5, 9, 6, 9, 53946)},
    {'id': 140, 'norm_library_id': 5, 'operation_name': 'Zinc Plating', 'unit': 'Rs/Kg', 'rate': Decimal('25.0000'), 'sort_order': 2, 'group_label': 'Surface Treatment', 'updated_at': datetime(2026, 10, 5, 9, 6, 9, 68060)},
    {'id': 141, 'norm_library_id': 5, 'operation_name': 'Final Painting (Primer + Final Coat)', 'unit': 'Rs/Sqm', 'rate': Decimal('450.0000'), 'sort_order': 3, 'group_label': 'Surface Treatment', 'updated_at': datetime(2026, 10, 5, 9, 6, 9, 81889)},
    {'id': 142, 'norm_library_id': 5, 'operation_name': 'Galvanizing', 'unit': 'Rs/Kg', 'rate': Decimal('40.0000'), 'sort_order': 4, 'group_label': 'Surface Treatment', 'updated_at': datetime(2026, 10, 5, 9, 6, 9, 96072)},
    {'id': 143, 'norm_library_id': 5, 'operation_name': 'Sub Transport', 'unit': 'Rs/Kg', 'rate': Decimal('2.5000'), 'sort_order': 1, 'group_label': 'Other', 'updated_at': datetime(2026, 10, 5, 9, 6, 9, 124769)},
    {'id': 144, 'norm_library_id': 5, 'operation_name': 'Machining (VTL)', 'unit': 'Rs/Hr', 'rate': Decimal('500.0000'), 'sort_order': 2, 'group_label': 'Other', 'updated_at': datetime(2026, 10, 5, 9, 6, 9, 146460)},
    {'id': 145, 'norm_library_id': 5, 'operation_name': 'Bush Fitting', 'unit': 'Rs/Nos', 'rate': Decimal('175.0000'), 'sort_order': 3, 'group_label': 'Other', 'updated_at': datetime(2026, 10, 5, 9, 6, 9, 163132)},
]

COST_OVERHEAD_PARAMS = [
    {'id': 1, 'norm_library_id': 1, 'applies_to': 'raw_material', 'param_name': 'Overhead', 'sort_order': 10, 'param_value': Decimal('0.0000'), 'updated_at': datetime(2026, 10, 4, 14, 51, 13, 215671)},
    {'id': 2, 'norm_library_id': 1, 'applies_to': 'raw_material', 'param_name': 'Rework', 'sort_order': 20, 'param_value': Decimal('0.0000'), 'updated_at': datetime(2026, 10, 4, 14, 51, 13, 215671)},
    {'id': 3, 'norm_library_id': 1, 'applies_to': 'raw_material', 'param_name': 'Inventory', 'sort_order': 30, 'param_value': Decimal('2.5000'), 'updated_at': datetime(2026, 10, 4, 14, 51, 13, 215671)},
    {'id': 4, 'norm_library_id': 1, 'applies_to': 'raw_material', 'param_name': 'Profit', 'sort_order': 40, 'param_value': Decimal('10.0000'), 'updated_at': datetime(2026, 10, 4, 14, 51, 13, 215671)},
    {'id': 5, 'norm_library_id': 1, 'applies_to': 'bought_out', 'param_name': 'Overhead', 'sort_order': 10, 'param_value': Decimal('0.0000'), 'updated_at': datetime(2026, 10, 4, 14, 51, 13, 215671)},
    {'id': 6, 'norm_library_id': 1, 'applies_to': 'bought_out', 'param_name': 'Inventory', 'sort_order': 20, 'param_value': Decimal('2.5000'), 'updated_at': datetime(2026, 10, 4, 14, 51, 13, 215671)},
    {'id': 7, 'norm_library_id': 1, 'applies_to': 'bought_out', 'param_name': 'Profit', 'sort_order': 30, 'param_value': Decimal('5.0000'), 'updated_at': datetime(2026, 10, 4, 14, 51, 13, 215671)},
    {'id': 8, 'norm_library_id': 1, 'applies_to': 'process_cost', 'param_name': 'Overhead', 'sort_order': 10, 'param_value': Decimal('10.0000'), 'updated_at': datetime(2026, 10, 4, 14, 51, 13, 215671)},
    {'id': 9, 'norm_library_id': 1, 'applies_to': 'process_cost', 'param_name': 'Rework', 'sort_order': 20, 'param_value': Decimal('0.0000'), 'updated_at': datetime(2026, 10, 4, 14, 51, 13, 215671)},
    {'id': 10, 'norm_library_id': 1, 'applies_to': 'process_cost', 'param_name': 'Profit', 'sort_order': 30, 'param_value': Decimal('10.0000'), 'updated_at': datetime(2026, 10, 4, 14, 51, 13, 215671)},
    {'id': 11, 'norm_library_id': 2, 'applies_to': 'raw_material', 'param_name': 'Overhead', 'sort_order': 10, 'param_value': Decimal('0.0000'), 'updated_at': datetime(2026, 10, 4, 14, 51, 24, 64783)},
    {'id': 12, 'norm_library_id': 2, 'applies_to': 'raw_material', 'param_name': 'Rework', 'sort_order': 20, 'param_value': Decimal('0.0000'), 'updated_at': datetime(2026, 10, 4, 14, 51, 24, 64783)},
    {'id': 13, 'norm_library_id': 2, 'applies_to': 'raw_material', 'param_name': 'Inventory', 'sort_order': 30, 'param_value': Decimal('2.5000'), 'updated_at': datetime(2026, 10, 4, 14, 51, 24, 64783)},
    {'id': 14, 'norm_library_id': 2, 'applies_to': 'raw_material', 'param_name': 'Profit', 'sort_order': 40, 'param_value': Decimal('10.0000'), 'updated_at': datetime(2026, 10, 4, 14, 51, 24, 64783)},
    {'id': 15, 'norm_library_id': 2, 'applies_to': 'bought_out', 'param_name': 'Overhead', 'sort_order': 10, 'param_value': Decimal('0.0000'), 'updated_at': datetime(2026, 10, 4, 14, 51, 24, 64783)},
    {'id': 16, 'norm_library_id': 2, 'applies_to': 'bought_out', 'param_name': 'Inventory', 'sort_order': 20, 'param_value': Decimal('2.5000'), 'updated_at': datetime(2026, 10, 4, 14, 51, 24, 64783)},
    {'id': 17, 'norm_library_id': 2, 'applies_to': 'bought_out', 'param_name': 'Profit', 'sort_order': 30, 'param_value': Decimal('5.0000'), 'updated_at': datetime(2026, 10, 4, 14, 51, 24, 64783)},
    {'id': 18, 'norm_library_id': 2, 'applies_to': 'process_cost', 'param_name': 'Overhead', 'sort_order': 10, 'param_value': Decimal('10.0000'), 'updated_at': datetime(2026, 10, 4, 14, 51, 24, 64783)},
    {'id': 19, 'norm_library_id': 2, 'applies_to': 'process_cost', 'param_name': 'Rework', 'sort_order': 20, 'param_value': Decimal('0.0000'), 'updated_at': datetime(2026, 10, 4, 14, 51, 24, 64783)},
    {'id': 20, 'norm_library_id': 2, 'applies_to': 'process_cost', 'param_name': 'Profit', 'sort_order': 30, 'param_value': Decimal('10.0000'), 'updated_at': datetime(2026, 10, 4, 14, 51, 24, 64783)},
    {'id': 31, 'norm_library_id': 4, 'applies_to': 'raw_material', 'param_name': 'Overhead', 'sort_order': 10, 'param_value': Decimal('0.0000'), 'updated_at': datetime(2026, 10, 5, 7, 34, 23, 245449)},
    {'id': 32, 'norm_library_id': 4, 'applies_to': 'raw_material', 'param_name': 'Rework', 'sort_order': 20, 'param_value': Decimal('0.0000'), 'updated_at': datetime(2026, 10, 5, 7, 34, 23, 245449)},
    {'id': 33, 'norm_library_id': 4, 'applies_to': 'raw_material', 'param_name': 'Inventory', 'sort_order': 30, 'param_value': Decimal('2.5000'), 'updated_at': datetime(2026, 10, 5, 7, 34, 23, 245449)},
    {'id': 34, 'norm_library_id': 4, 'applies_to': 'raw_material', 'param_name': 'Profit', 'sort_order': 40, 'param_value': Decimal('10.0000'), 'updated_at': datetime(2026, 10, 5, 7, 34, 23, 245449)},
    {'id': 35, 'norm_library_id': 4, 'applies_to': 'bought_out', 'param_name': 'Overhead', 'sort_order': 10, 'param_value': Decimal('0.0000'), 'updated_at': datetime(2026, 10, 5, 7, 34, 23, 245449)},
    {'id': 36, 'norm_library_id': 4, 'applies_to': 'bought_out', 'param_name': 'Inventory', 'sort_order': 20, 'param_value': Decimal('2.5000'), 'updated_at': datetime(2026, 10, 5, 7, 34, 23, 245449)},
    {'id': 37, 'norm_library_id': 4, 'applies_to': 'bought_out', 'param_name': 'Profit', 'sort_order': 30, 'param_value': Decimal('5.0000'), 'updated_at': datetime(2026, 10, 5, 7, 34, 23, 245449)},
    {'id': 38, 'norm_library_id': 4, 'applies_to': 'process_cost', 'param_name': 'Overhead', 'sort_order': 10, 'param_value': Decimal('10.0000'), 'updated_at': datetime(2026, 10, 5, 7, 34, 23, 245449)},
    {'id': 39, 'norm_library_id': 4, 'applies_to': 'process_cost', 'param_name': 'Rework', 'sort_order': 20, 'param_value': Decimal('0.0000'), 'updated_at': datetime(2026, 10, 5, 7, 34, 23, 245449)},
    {'id': 40, 'norm_library_id': 4, 'applies_to': 'process_cost', 'param_name': 'Profit', 'sort_order': 30, 'param_value': Decimal('10.0000'), 'updated_at': datetime(2026, 10, 5, 7, 34, 23, 245449)},
    {'id': 41, 'norm_library_id': 5, 'applies_to': 'raw_material', 'param_name': 'Overhead', 'sort_order': 1, 'param_value': Decimal('0.0000'), 'updated_at': datetime(2026, 10, 5, 9, 6, 9, 181326)},
    {'id': 42, 'norm_library_id': 5, 'applies_to': 'raw_material', 'param_name': 'Rework', 'sort_order': 2, 'param_value': Decimal('0.0000'), 'updated_at': datetime(2026, 10, 5, 9, 6, 9, 199973)},
    {'id': 43, 'norm_library_id': 5, 'applies_to': 'raw_material', 'param_name': 'Inventory Carry', 'sort_order': 3, 'param_value': Decimal('2.5000'), 'updated_at': datetime(2026, 10, 5, 9, 6, 9, 217870)},
    {'id': 44, 'norm_library_id': 5, 'applies_to': 'raw_material', 'param_name': 'Profit', 'sort_order': 4, 'param_value': Decimal('10.0000'), 'updated_at': datetime(2026, 10, 5, 9, 6, 9, 232246)},
    {'id': 45, 'norm_library_id': 5, 'applies_to': 'bought_out', 'param_name': 'Overhead', 'sort_order': 1, 'param_value': Decimal('0.0000'), 'updated_at': datetime(2026, 10, 5, 9, 6, 9, 245642)},
    {'id': 46, 'norm_library_id': 5, 'applies_to': 'bought_out', 'param_name': 'Inventory Carry', 'sort_order': 2, 'param_value': Decimal('2.5000'), 'updated_at': datetime(2026, 10, 5, 9, 6, 9, 260313)},
    {'id': 47, 'norm_library_id': 5, 'applies_to': 'bought_out', 'param_name': 'Profit', 'sort_order': 3, 'param_value': Decimal('5.0000'), 'updated_at': datetime(2026, 10, 5, 9, 6, 9, 275721)},
    {'id': 48, 'norm_library_id': 5, 'applies_to': 'process_cost', 'param_name': 'Overhead', 'sort_order': 1, 'param_value': Decimal('10.0000'), 'updated_at': datetime(2026, 10, 5, 9, 6, 9, 291286)},
    {'id': 49, 'norm_library_id': 5, 'applies_to': 'process_cost', 'param_name': 'Rework', 'sort_order': 2, 'param_value': Decimal('0.0000'), 'updated_at': datetime(2026, 10, 5, 9, 6, 9, 307636)},
    {'id': 50, 'norm_library_id': 5, 'applies_to': 'process_cost', 'param_name': 'Profit', 'sort_order': 3, 'param_value': Decimal('10.0000'), 'updated_at': datetime(2026, 10, 5, 9, 6, 9, 323965)},
]

STEEL_PRICE_BUILDUPS = [
    {'id': 1, 'norm_library_id': 2, 'grade_id': 1, 'thickness_band': '<10mm', 'basic_price_per_tonne': Decimal('58000.0000'), 'ust_amount': Decimal('500.0000'), 'trimming_amount': Decimal('300.0000'), 'normalising_amount': Decimal('200.0000'), 'trader_transport_constant': Decimal('1500.0000'), 'updated_at': datetime(2026, 10, 5, 4, 52, 32, 819932)},
    {'id': 3, 'norm_library_id': 4, 'grade_id': 1, 'thickness_band': '<10mm', 'basic_price_per_tonne': Decimal('58000.0000'), 'ust_amount': Decimal('500.0000'), 'trimming_amount': Decimal('300.0000'), 'normalising_amount': Decimal('200.0000'), 'trader_transport_constant': Decimal('1500.0000'), 'updated_at': datetime(2026, 10, 5, 7, 34, 23, 245449)},
]

GRADE_EQUIVALENCES = [
    {'id': 1, 'norm_library_id': 2, 'customer_spec': 'S235J2', 'material_grade_id': 1, 'notes': 'EU structural steel equivalent', 'updated_at': datetime(2026, 10, 5, 4, 52, 32, 993109)},
    {'id': 3, 'norm_library_id': 4, 'customer_spec': 'S235J2', 'material_grade_id': 1, 'notes': 'EU structural steel equivalent', 'updated_at': datetime(2026, 10, 5, 7, 34, 23, 245449)},
    {'id': 4, 'norm_library_id': 5, 'customer_spec': 'S235J2', 'material_grade_id': 1, 'notes': 'EU structural steel, used across TLD chassis/hitch BOMs', 'updated_at': datetime(2026, 10, 5, 9, 6, 8, 740212)},
    {'id': 5, 'norm_library_id': 5, 'customer_spec': 'A36/44W', 'material_grade_id': 1, 'notes': 'ASTM structural steel, seen on Brake Pedal Support BOM', 'updated_at': datetime(2026, 10, 5, 9, 6, 8, 761786)},
]

SECTION_CATALOG_ITEMS = [
    {'id': 1, 'norm_library_id': 2, 'category': 'channel', 'designation': 'ISMC 100', 'kg_per_m': Decimal('9.5600'), 'rate_per_kg': Decimal('62.5000'), 'updated_at': datetime(2026, 10, 5, 4, 52, 33, 231405)},
    {'id': 3, 'norm_library_id': 4, 'category': 'channel', 'designation': 'ISMC 100', 'kg_per_m': Decimal('9.5600'), 'rate_per_kg': Decimal('62.5000'), 'updated_at': datetime(2026, 10, 5, 7, 34, 23, 245449)},
]

BO_CATALOG_ITEMS = [
    {'id': 1, 'norm_library_id': 2, 'name': 'M10 Hex Bolt', 'category': 'Fastener', 'unit_weight_kg': Decimal('0.0300'), 'rate': Decimal('5.5000'), 'updated_at': datetime(2026, 10, 5, 4, 52, 33, 381607)},
    {'id': 3, 'norm_library_id': 4, 'name': 'M10 Hex Bolt', 'category': 'Fastener', 'unit_weight_kg': Decimal('0.0300'), 'rate': Decimal('5.5000'), 'updated_at': datetime(2026, 10, 5, 7, 34, 23, 245449)},
]

COST_WORKBOOKS = [
    {'id': 1, 'client_id': 1, 'name': 'Demo WB', 'description': None, 'created_at': datetime(2026, 10, 5, 4, 53, 18, 902782), 'sets_count': 3},
    {'id': 2, 'client_id': 2, 'name': 'TLD Costing 06-04-2026', 'description': None, 'created_at': datetime(2026, 10, 5, 9, 6, 9, 355583), 'sets_count': 1},
]

COST_SHEETS = [
    {'id': 1, 'workbook_id': 1, 'name': 'Demo Part', 'part_no': None, 'description': None, 'drawing_no': None, 'benchmark_price': Decimal('1800.0000'), 'supply_version': 'V1', 'discount_pct': Decimal('0.0000'), 'transport_cost': Decimal('0.0000'), 'created_at': datetime(2026, 10, 5, 4, 53, 19, 53786), 'image_url': '/static/uploads/2c8dfa5382fc46f8af852be13ca89a1c.png', 'qty_per_set': Decimal('2.0000'), 'is_optional': False, 'status': 'Approved by MD', 'remarks': 'Stock on hand', 'first_supply_price': Decimal('2006.1120'), 'first_supply_date': date(2026, 10, 5), 'first_supply_rm_reference': Decimal('64.0000')},
    {'id': 2, 'workbook_id': 1, 'name': 'Optional Guard Cover', 'part_no': None, 'description': None, 'drawing_no': None, 'benchmark_price': None, 'supply_version': 'V1', 'discount_pct': Decimal('0.0000'), 'transport_cost': Decimal('0.0000'), 'created_at': datetime(2026, 10, 5, 6, 45, 31, 793311), 'image_url': None, 'qty_per_set': Decimal('1.0000'), 'is_optional': True, 'status': 'No orders', 'remarks': 'Hold until approved', 'first_supply_price': None, 'first_supply_date': None, 'first_supply_rm_reference': None},
    {'id': 3, 'workbook_id': 2, 'name': 'PLATE', 'part_no': '9207833', 'description': None, 'drawing_no': None, 'benchmark_price': None, 'supply_version': 'V1', 'discount_pct': Decimal('0.0000'), 'transport_cost': Decimal('0.0000'), 'created_at': datetime(2026, 10, 5, 9, 6, 9, 369442), 'image_url': None, 'qty_per_set': Decimal('1.0000'), 'is_optional': False, 'status': 'No orders', 'remarks': None, 'first_supply_price': Decimal('455.5922'), 'first_supply_date': date(2026, 10, 5), 'first_supply_rm_reference': Decimal('65.5000')},
    {'id': 4, 'workbook_id': 2, 'name': 'TOW CLEVIS', 'part_no': '4100011', 'description': 'Plate sub-parts only — round-bar pin sub-lines omitted (see note)', 'drawing_no': None, 'benchmark_price': None, 'supply_version': 'V1', 'discount_pct': Decimal('0.0000'), 'transport_cost': Decimal('0.0000'), 'created_at': datetime(2026, 10, 5, 9, 6, 9, 506608), 'image_url': None, 'qty_per_set': Decimal('1.0000'), 'is_optional': False, 'status': None, 'remarks': None, 'first_supply_price': Decimal('1411.1559'), 'first_supply_date': date(2026, 10, 5), 'first_supply_rm_reference': Decimal('65.5000')},
    {'id': 5, 'workbook_id': 2, 'name': 'BRAKE PEDAL SUPPORT', 'part_no': '1136024', 'description': 'Base/Side plate children shown — round-bar bushing sub-line omitted (see note)', 'drawing_no': None, 'benchmark_price': None, 'supply_version': 'V1', 'discount_pct': Decimal('0.0000'), 'transport_cost': Decimal('0.0000'), 'created_at': datetime(2026, 10, 5, 9, 6, 9, 729864), 'image_url': None, 'qty_per_set': Decimal('1.0000'), 'is_optional': False, 'status': None, 'remarks': None, 'first_supply_price': Decimal('1024.7200'), 'first_supply_date': date(2026, 10, 5), 'first_supply_rm_reference': Decimal('65.5000')},
]

COSTING_LINES = [
    {'id': 1, 'cost_sheet_id': 1, 'sl_no': 1, 'description': 'Main Assembly', 'spec': None, 'grade_id': 1, 'thickness_band': '<10mm', 'thickness_mm': None, 'qty': Decimal('1.0000'), 'part_weight': Decimal('10.0000'), 'efficiency_pct': Decimal('100.0000'), 'parent_line_id': None},
    {'id': 2, 'cost_sheet_id': 1, 'sl_no': 2, 'description': 'Side Plate LH', 'spec': None, 'grade_id': 1, 'thickness_band': '<10mm', 'thickness_mm': Decimal('10.00'), 'qty': Decimal('1.0000'), 'part_weight': Decimal('2.0000'), 'efficiency_pct': Decimal('100.0000'), 'parent_line_id': 1},
    {'id': 3, 'cost_sheet_id': 1, 'sl_no': 3, 'description': 'Side Plate RH', 'spec': None, 'grade_id': 1, 'thickness_band': '<10mm', 'thickness_mm': None, 'qty': Decimal('1.0000'), 'part_weight': Decimal('2.0000'), 'efficiency_pct': Decimal('100.0000'), 'parent_line_id': 1},
    {'id': 4, 'cost_sheet_id': 1, 'sl_no': 4, 'description': 'Standalone Bracket', 'spec': None, 'grade_id': 1, 'thickness_band': '<10mm', 'thickness_mm': None, 'qty': Decimal('1.0000'), 'part_weight': Decimal('1.0000'), 'efficiency_pct': Decimal('100.0000'), 'parent_line_id': None},
    {'id': 5, 'cost_sheet_id': 3, 'sl_no': 1, 'description': 'PLATE', 'spec': 'IS2062 E250BR', 'grade_id': 1, 'thickness_band': '20mm', 'thickness_mm': Decimal('20.00'), 'qty': Decimal('1.0000'), 'part_weight': Decimal('2.0000'), 'efficiency_pct': Decimal('58.0000'), 'parent_line_id': None},
    {'id': 6, 'cost_sheet_id': 4, 'sl_no': 1, 'description': 'PLATE-001', 'spec': 'IS2062 E250BR', 'grade_id': 1, 'thickness_band': '>12-19mm', 'thickness_mm': Decimal('16.00'), 'qty': Decimal('1.0000'), 'part_weight': Decimal('2.3000'), 'efficiency_pct': Decimal('53.0000'), 'parent_line_id': None},
    {'id': 7, 'cost_sheet_id': 4, 'sl_no': 2, 'description': 'PLATE-002', 'spec': 'IS2062 E250BR', 'grade_id': 1, 'thickness_band': '20mm', 'thickness_mm': Decimal('20.00'), 'qty': Decimal('2.0000'), 'part_weight': Decimal('0.6000'), 'efficiency_pct': Decimal('53.0000'), 'parent_line_id': None},
    {'id': 8, 'cost_sheet_id': 5, 'sl_no': 1, 'description': 'BRAKE PEDAL SUPPORT (assembly)', 'spec': None, 'grade_id': 1, 'thickness_band': '<10mm', 'thickness_mm': None, 'qty': Decimal('1.0000'), 'part_weight': Decimal('0.0000'), 'efficiency_pct': Decimal('100.0000'), 'parent_line_id': None},
    {'id': 9, 'cost_sheet_id': 5, 'sl_no': 2, 'description': 'BASE PLATE', 'spec': 'A36/44W', 'grade_id': 1, 'thickness_band': '<10mm', 'thickness_mm': Decimal('8.00'), 'qty': Decimal('1.0000'), 'part_weight': Decimal('1.9000'), 'efficiency_pct': Decimal('51.0000'), 'parent_line_id': 8},
    {'id': 10, 'cost_sheet_id': 5, 'sl_no': 3, 'description': 'SIDE PLATE', 'spec': 'A36/44W', 'grade_id': 1, 'thickness_band': '<10mm', 'thickness_mm': Decimal('8.00'), 'qty': Decimal('2.0000'), 'part_weight': Decimal('0.7000'), 'efficiency_pct': Decimal('51.0000'), 'parent_line_id': 8},
]

COSTING_RESULTS = [
    {'id': 1, 'costing_line_id': 1, 'norm_library_id': 2, 'calculated_at': datetime(2026, 10, 5, 7, 33, 19, 583247), 'total_part_weight': Decimal('10.000000'), 'blank_weight': Decimal('10.000000'), 'total_blank_weight': Decimal('10.000000'), 'blank_rate': Decimal('75.000000'), 'blank_cost': Decimal('750.0000'), 'process_loss_pct': Decimal('5.0000'), 'process_loss_weight': Decimal('0.500000'), 'scrap_weight': Decimal('-0.500000'), 'scrap_cost': Decimal('-15.0000'), 'rm_cost': Decimal('765.0000'), 'line_process_cost': Decimal('0.0000')},
    {'id': 2, 'costing_line_id': 2, 'norm_library_id': 2, 'calculated_at': datetime(2026, 10, 5, 7, 33, 19, 583247), 'total_part_weight': Decimal('2.000000'), 'blank_weight': Decimal('2.000000'), 'total_blank_weight': Decimal('2.000000'), 'blank_rate': Decimal('75.000000'), 'blank_cost': Decimal('150.0000'), 'process_loss_pct': Decimal('5.0000'), 'process_loss_weight': Decimal('0.100000'), 'scrap_weight': Decimal('-0.100000'), 'scrap_cost': Decimal('-3.0000'), 'rm_cost': Decimal('153.0000'), 'line_process_cost': Decimal('244.2600')},
    {'id': 3, 'costing_line_id': 3, 'norm_library_id': 2, 'calculated_at': datetime(2026, 10, 5, 7, 33, 19, 583247), 'total_part_weight': Decimal('2.000000'), 'blank_weight': Decimal('2.000000'), 'total_blank_weight': Decimal('2.000000'), 'blank_rate': Decimal('75.000000'), 'blank_cost': Decimal('150.0000'), 'process_loss_pct': Decimal('5.0000'), 'process_loss_weight': Decimal('0.100000'), 'scrap_weight': Decimal('-0.100000'), 'scrap_cost': Decimal('-3.0000'), 'rm_cost': Decimal('153.0000'), 'line_process_cost': Decimal('0.0000')},
    {'id': 4, 'costing_line_id': 4, 'norm_library_id': 2, 'calculated_at': datetime(2026, 10, 5, 7, 33, 19, 583247), 'total_part_weight': Decimal('1.000000'), 'blank_weight': Decimal('1.000000'), 'total_blank_weight': Decimal('1.000000'), 'blank_rate': Decimal('75.000000'), 'blank_cost': Decimal('75.0000'), 'process_loss_pct': Decimal('5.0000'), 'process_loss_weight': Decimal('0.050000'), 'scrap_weight': Decimal('-0.050000'), 'scrap_cost': Decimal('-1.5000'), 'rm_cost': Decimal('76.5000'), 'line_process_cost': Decimal('0.0000')},
    {'id': 5, 'costing_line_id': 5, 'norm_library_id': 5, 'calculated_at': datetime(2026, 10, 5, 9, 24, 20, 504084), 'total_part_weight': Decimal('2.000000'), 'blank_weight': Decimal('3.448276'), 'total_blank_weight': Decimal('3.448276'), 'blank_rate': Decimal('72.000000'), 'blank_cost': Decimal('248.2759'), 'process_loss_pct': Decimal('5.0000'), 'process_loss_weight': Decimal('0.172414'), 'scrap_weight': Decimal('1.275862'), 'scrap_cost': Decimal('37.6379'), 'rm_cost': Decimal('210.6379'), 'line_process_cost': Decimal('203.2000')},
    {'id': 6, 'costing_line_id': 6, 'norm_library_id': 5, 'calculated_at': datetime(2026, 10, 5, 9, 24, 20, 514719), 'total_part_weight': Decimal('2.300000'), 'blank_weight': Decimal('4.339623'), 'total_blank_weight': Decimal('4.339623'), 'blank_rate': Decimal('71.000000'), 'blank_cost': Decimal('308.1132'), 'process_loss_pct': Decimal('5.0000'), 'process_loss_weight': Decimal('0.216981'), 'scrap_weight': Decimal('1.822642'), 'scrap_cost': Decimal('53.7679'), 'rm_cost': Decimal('254.3453'), 'line_process_cost': Decimal('181.6640')},
    {'id': 7, 'costing_line_id': 7, 'norm_library_id': 5, 'calculated_at': datetime(2026, 10, 5, 9, 24, 20, 514719), 'total_part_weight': Decimal('1.200000'), 'blank_weight': Decimal('1.132075'), 'total_blank_weight': Decimal('2.264151'), 'blank_rate': Decimal('72.000000'), 'blank_cost': Decimal('163.0189'), 'process_loss_pct': Decimal('5.0000'), 'process_loss_weight': Decimal('0.113208'), 'scrap_weight': Decimal('0.950943'), 'scrap_cost': Decimal('28.0528'), 'rm_cost': Decimal('134.9660'), 'line_process_cost': Decimal('203.5200')},
    {'id': 8, 'costing_line_id': 8, 'norm_library_id': 5, 'calculated_at': datetime(2026, 10, 5, 9, 24, 20, 525944), 'total_part_weight': Decimal('0.000000'), 'blank_weight': Decimal('0.000000'), 'total_blank_weight': Decimal('0.000000'), 'blank_rate': Decimal('70.000000'), 'blank_cost': Decimal('0.0000'), 'process_loss_pct': Decimal('5.0000'), 'process_loss_weight': Decimal('0.000000'), 'scrap_weight': Decimal('0.000000'), 'scrap_cost': Decimal('0.0000'), 'rm_cost': Decimal('0.0000'), 'line_process_cost': Decimal('0.0000')},
    {'id': 9, 'costing_line_id': 9, 'norm_library_id': 5, 'calculated_at': datetime(2026, 10, 5, 9, 24, 20, 525944), 'total_part_weight': Decimal('1.900000'), 'blank_weight': Decimal('3.725490'), 'total_blank_weight': Decimal('3.725490'), 'blank_rate': Decimal('70.000000'), 'blank_cost': Decimal('260.7843'), 'process_loss_pct': Decimal('5.0000'), 'process_loss_weight': Decimal('0.186275'), 'scrap_weight': Decimal('1.639216'), 'scrap_cost': Decimal('48.3569'), 'rm_cost': Decimal('212.4275'), 'line_process_cost': Decimal('82.8800')},
    {'id': 10, 'costing_line_id': 10, 'norm_library_id': 5, 'calculated_at': datetime(2026, 10, 5, 9, 24, 20, 525944), 'total_part_weight': Decimal('1.400000'), 'blank_weight': Decimal('1.372549'), 'total_blank_weight': Decimal('2.745098'), 'blank_rate': Decimal('70.000000'), 'blank_cost': Decimal('192.1569'), 'process_loss_pct': Decimal('5.0000'), 'process_loss_weight': Decimal('0.137255'), 'scrap_weight': Decimal('1.207843'), 'scrap_cost': Decimal('35.6314'), 'rm_cost': Decimal('156.5255'), 'line_process_cost': Decimal('162.4320')},
]

BO_LINE_ITEMS = [
    {'id': 1, 'cost_sheet_id': 4, 'sl_no': 1, 'description': 'Chain', 'qty': Decimal('1.0000'), 'unit_price': Decimal('50.0000'), 'catalog_item_id': None, 'unit_weight_kg': None},
    {'id': 2, 'cost_sheet_id': 4, 'sl_no': 2, 'description': 'Key', 'qty': Decimal('2.0000'), 'unit_price': Decimal('15.0000'), 'catalog_item_id': None, 'unit_weight_kg': None},
    {'id': 3, 'cost_sheet_id': 4, 'sl_no': 3, 'description': 'Pin', 'qty': Decimal('1.0000'), 'unit_price': Decimal('6.0000'), 'catalog_item_id': None, 'unit_weight_kg': None},
]

COSTING_LINE_OPERATIONS = [
    {'id': 1, 'costing_line_id': 2, 'operation_type': 'Plasma Cutting', 'input_data': {'length_mm': 8142, 'length_mm_expr': '8022+60+60'}, 'operation_cost': Decimal('244.2600')},
    {'id': 2, 'costing_line_id': 5, 'operation_type': 'Laser Cutting', 'input_data': {'length_mm': 520}, 'operation_cost': Decimal('83.2000')},
    {'id': 3, 'costing_line_id': 5, 'operation_type': 'Drilling', 'input_data': {'hours': 0.5, 'drilling_type': 'regular'}, 'operation_cost': Decimal('100.0000')},
    {'id': 4, 'costing_line_id': 5, 'operation_type': 'Dressing', 'input_data': {'hours': 0.1}, 'operation_cost': Decimal('20.0000')},
    {'id': 5, 'costing_line_id': 6, 'operation_type': 'Laser Cutting', 'input_data': {'length_mm': 638}, 'operation_cost': Decimal('81.6640')},
    {'id': 6, 'costing_line_id': 6, 'operation_type': 'Drilling', 'input_data': {'hours': 0.5, 'drilling_type': 'regular'}, 'operation_cost': Decimal('100.0000')},
    {'id': 7, 'costing_line_id': 7, 'operation_type': 'Laser Cutting', 'input_data': {'length_mm': 386}, 'operation_cost': Decimal('123.5200')},
    {'id': 8, 'costing_line_id': 7, 'operation_type': 'Drilling', 'input_data': {'hours': 0.2, 'drilling_type': 'regular'}, 'operation_cost': Decimal('80.0000')},
    {'id': 9, 'costing_line_id': 9, 'operation_type': 'Laser Cutting', 'input_data': {'length_mm': 1295}, 'operation_cost': Decimal('82.8800')},
    {'id': 10, 'costing_line_id': 10, 'operation_type': 'Laser Cutting', 'input_data': {'length_mm': 1269}, 'operation_cost': Decimal('162.4320')},
]

SHEET_FINISHING_OPS = [
    {'id': 1, 'cost_sheet_id': 1, 'operation_name': 'Final Painting (Primer + Final Coat)', 'input_qty': Decimal('1.0000'), 'computed_cost': Decimal('575.0000')},
    {'id': 2, 'cost_sheet_id': 4, 'operation_name': 'Tack Welding', 'input_qty': Decimal('1.0000'), 'computed_cost': Decimal('300.0000')},
    {'id': 3, 'cost_sheet_id': 4, 'operation_name': 'Full Welding (solid wire)', 'input_qty': Decimal('0.2000'), 'computed_cost': Decimal('49.0000')},
    {'id': 4, 'cost_sheet_id': 4, 'operation_name': 'Dressing', 'input_qty': Decimal('0.2000'), 'computed_cost': Decimal('40.0000')},
    {'id': 5, 'cost_sheet_id': 5, 'operation_name': 'Tack Welding', 'input_qty': Decimal('0.5000'), 'computed_cost': Decimal('150.0000')},
    {'id': 6, 'cost_sheet_id': 5, 'operation_name': 'Full Welding (solid wire)', 'input_qty': Decimal('0.2000'), 'computed_cost': Decimal('49.0000')},
    {'id': 7, 'cost_sheet_id': 5, 'operation_name': 'Dressing', 'input_qty': Decimal('0.1000'), 'computed_cost': Decimal('20.0000')},
    {'id': 8, 'cost_sheet_id': 5, 'operation_name': 'Sandering', 'input_qty': Decimal('0.1000'), 'computed_cost': Decimal('20.0000')},
    {'id': 9, 'cost_sheet_id': 5, 'operation_name': 'Shot Blasting', 'input_qty': Decimal('3.5000'), 'computed_cost': Decimal('6.1250')},
    {'id': 10, 'cost_sheet_id': 5, 'operation_name': 'Final Painting (Primer + Final Coat)', 'input_qty': Decimal('0.1200'), 'computed_cost': Decimal('54.0000')},
]

COST_SHEET_RESULTS = [
    {'id': 2, 'cost_sheet_id': 1, 'norm_library_id': 2, 'calculated_at': datetime(2026, 10, 5, 7, 33, 19, 583247), 'total_rm_cost': Decimal('1147.5000'), 'overhead_rm': Decimal('0.0000'), 'rework_rm': Decimal('0.0000'), 'inventory_rm': Decimal('0.0000'), 'profit_rm': Decimal('114.7500'), 'rm_grand_total': Decimal('1262.2500'), 'total_bo_cost': Decimal('0.0000'), 'overhead_bo': Decimal('0.0000'), 'inventory_bo': Decimal('0.0000'), 'profit_bo': Decimal('0.0000'), 'bo_grand_total': Decimal('0.0000'), 'total_process_cost': Decimal('819.2600'), 'overhead_proc': Decimal('81.9260'), 'rework_proc': Decimal('0.0000'), 'profit_proc': Decimal('81.9260'), 'process_grand_total': Decimal('983.1120'), 'unit_price': Decimal('2245.3620'), 'transport_cost_snap': Decimal('0.0000'), 'discount_pct_snap': Decimal('0.0000'), 'price_after_discount': Decimal('2245.3620'), 'pct_change_vs_previous': None, 'bal_margin': Decimal('1097.8620'), 'bal_margin_per_kg': Decimal('73.1908'), 'total_part_weight': Decimal('15.000000')},
    {'id': 3, 'cost_sheet_id': 3, 'norm_library_id': 5, 'calculated_at': datetime(2026, 10, 5, 9, 24, 20, 504084), 'total_rm_cost': Decimal('210.6379'), 'overhead_rm': Decimal('0.0000'), 'rework_rm': Decimal('0.0000'), 'inventory_rm': Decimal('5.2659'), 'profit_rm': Decimal('21.0638'), 'rm_grand_total': Decimal('236.9677'), 'total_bo_cost': Decimal('0.0000'), 'overhead_bo': Decimal('0.0000'), 'inventory_bo': Decimal('0.0000'), 'profit_bo': Decimal('0.0000'), 'bo_grand_total': Decimal('0.0000'), 'total_process_cost': Decimal('203.2000'), 'overhead_proc': Decimal('20.3200'), 'rework_proc': Decimal('0.0000'), 'profit_proc': Decimal('20.3200'), 'process_grand_total': Decimal('243.8400'), 'unit_price': Decimal('480.8077'), 'transport_cost_snap': Decimal('0.0000'), 'discount_pct_snap': Decimal('0.0000'), 'price_after_discount': Decimal('480.8077'), 'pct_change_vs_previous': None, 'bal_margin': Decimal('270.1697'), 'bal_margin_per_kg': Decimal('135.0849'), 'total_part_weight': Decimal('2.000000')},
    {'id': 4, 'cost_sheet_id': 4, 'norm_library_id': 5, 'calculated_at': datetime(2026, 10, 5, 9, 24, 20, 514719), 'total_rm_cost': Decimal('389.3113'), 'overhead_rm': Decimal('0.0000'), 'rework_rm': Decimal('0.0000'), 'inventory_rm': Decimal('9.7328'), 'profit_rm': Decimal('38.9311'), 'rm_grand_total': Decimal('437.9752'), 'total_bo_cost': Decimal('86.0000'), 'overhead_bo': Decimal('0.0000'), 'inventory_bo': Decimal('2.1500'), 'profit_bo': Decimal('4.3000'), 'bo_grand_total': Decimal('92.4500'), 'total_process_cost': Decimal('774.1840'), 'overhead_proc': Decimal('77.4184'), 'rework_proc': Decimal('0.0000'), 'profit_proc': Decimal('77.4184'), 'process_grand_total': Decimal('929.0208'), 'unit_price': Decimal('1459.4460'), 'transport_cost_snap': Decimal('0.0000'), 'discount_pct_snap': Decimal('0.0000'), 'price_after_discount': Decimal('1459.4460'), 'pct_change_vs_previous': None, 'bal_margin': Decimal('984.1347'), 'bal_margin_per_kg': Decimal('281.1813'), 'total_part_weight': Decimal('3.500000')},
    {'id': 5, 'cost_sheet_id': 5, 'norm_library_id': 5, 'calculated_at': datetime(2026, 10, 5, 9, 24, 20, 525944), 'total_rm_cost': Decimal('368.9529'), 'overhead_rm': Decimal('0.0000'), 'rework_rm': Decimal('0.0000'), 'inventory_rm': Decimal('9.2238'), 'profit_rm': Decimal('36.8953'), 'rm_grand_total': Decimal('415.0721'), 'total_bo_cost': Decimal('0.0000'), 'overhead_bo': Decimal('0.0000'), 'inventory_bo': Decimal('0.0000'), 'profit_bo': Decimal('0.0000'), 'bo_grand_total': Decimal('0.0000'), 'total_process_cost': Decimal('544.4370'), 'overhead_proc': Decimal('54.4437'), 'rework_proc': Decimal('0.0000'), 'profit_proc': Decimal('54.4437'), 'process_grand_total': Decimal('653.3244'), 'unit_price': Decimal('1068.3965'), 'transport_cost_snap': Decimal('0.0000'), 'discount_pct_snap': Decimal('0.0000'), 'price_after_discount': Decimal('1068.3965'), 'pct_change_vs_previous': None, 'bal_margin': Decimal('699.4435'), 'bal_margin_per_kg': Decimal('211.9526'), 'total_part_weight': Decimal('3.300000')},
]

PROCESS_COST_ROWS = [
    {'id': 1, 'costing_line_id': 1, 'equi_spec': None, 'thk': None, 'unit_cut_length': None, 'use_laser': False, 'machining_rate': None, 'bev_slant': None, 'bev_length': None, 'bend_num_bends': None, 'drill_size': None, 'drill_hours': None, 'drill_type': 'regular', 'has_rolling': False},
    {'id': 2, 'costing_line_id': 2, 'equi_spec': None, 'thk': None, 'unit_cut_length': None, 'use_laser': False, 'machining_rate': None, 'bev_slant': None, 'bev_length': None, 'bend_num_bends': None, 'drill_size': None, 'drill_hours': None, 'drill_type': 'regular', 'has_rolling': False},
    {'id': 3, 'costing_line_id': 3, 'equi_spec': None, 'thk': None, 'unit_cut_length': None, 'use_laser': False, 'machining_rate': None, 'bev_slant': None, 'bev_length': None, 'bend_num_bends': None, 'drill_size': None, 'drill_hours': None, 'drill_type': 'regular', 'has_rolling': False},
    {'id': 4, 'costing_line_id': 4, 'equi_spec': None, 'thk': None, 'unit_cut_length': None, 'use_laser': False, 'machining_rate': None, 'bev_slant': None, 'bev_length': None, 'bend_num_bends': None, 'drill_size': None, 'drill_hours': None, 'drill_type': 'regular', 'has_rolling': False},
    {'id': 5, 'costing_line_id': 5, 'equi_spec': None, 'thk': Decimal('20.00'), 'unit_cut_length': None, 'use_laser': False, 'machining_rate': None, 'bev_slant': None, 'bev_length': None, 'bend_num_bends': None, 'drill_size': None, 'drill_hours': None, 'drill_type': 'regular', 'has_rolling': False},
    {'id': 6, 'costing_line_id': 6, 'equi_spec': None, 'thk': Decimal('16.00'), 'unit_cut_length': None, 'use_laser': False, 'machining_rate': None, 'bev_slant': None, 'bev_length': None, 'bend_num_bends': None, 'drill_size': None, 'drill_hours': None, 'drill_type': 'regular', 'has_rolling': False},
    {'id': 7, 'costing_line_id': 7, 'equi_spec': None, 'thk': Decimal('20.00'), 'unit_cut_length': None, 'use_laser': False, 'machining_rate': None, 'bev_slant': None, 'bev_length': None, 'bend_num_bends': None, 'drill_size': None, 'drill_hours': None, 'drill_type': 'regular', 'has_rolling': False},
    {'id': 8, 'costing_line_id': 8, 'equi_spec': None, 'thk': None, 'unit_cut_length': None, 'use_laser': False, 'machining_rate': None, 'bev_slant': None, 'bev_length': None, 'bend_num_bends': None, 'drill_size': None, 'drill_hours': None, 'drill_type': 'regular', 'has_rolling': False},
    {'id': 9, 'costing_line_id': 9, 'equi_spec': None, 'thk': Decimal('8.00'), 'unit_cut_length': None, 'use_laser': False, 'machining_rate': None, 'bev_slant': None, 'bev_length': None, 'bend_num_bends': None, 'drill_size': None, 'drill_hours': None, 'drill_type': 'regular', 'has_rolling': False},
    {'id': 10, 'costing_line_id': 10, 'equi_spec': None, 'thk': Decimal('8.00'), 'unit_cut_length': None, 'use_laser': False, 'machining_rate': None, 'bev_slant': None, 'bev_length': None, 'bend_num_bends': None, 'drill_size': None, 'drill_hours': None, 'drill_type': 'regular', 'has_rolling': False},
]

PRICE_HISTORY_ENTRIES = [
    {'id': 1, 'cost_sheet_id': 1, 'change_no': 1, 'price': Decimal('2006.1120'), 'rm_reference_price': Decimal('64.0000'), 'discount_pct': Decimal('0.0000'), 'pct_change_vs_last_supplied': None, 'recorded_at': datetime(2026, 10, 5, 7, 32, 27, 287650)},
    {'id': 2, 'cost_sheet_id': 1, 'change_no': 2, 'price': Decimal('2162.8620'), 'rm_reference_price': Decimal('64.0000'), 'discount_pct': Decimal('0.0000'), 'pct_change_vs_last_supplied': Decimal('7.813622'), 'recorded_at': datetime(2026, 10, 5, 7, 32, 47, 860969)},
    {'id': 3, 'cost_sheet_id': 1, 'change_no': 3, 'price': Decimal('2245.3620'), 'rm_reference_price': Decimal('64.0000'), 'discount_pct': Decimal('0.0000'), 'pct_change_vs_last_supplied': Decimal('3.814390'), 'recorded_at': datetime(2026, 10, 5, 7, 33, 19, 567987)},
    {'id': 4, 'cost_sheet_id': 3, 'change_no': 1, 'price': Decimal('455.5922'), 'rm_reference_price': Decimal('65.5000'), 'discount_pct': Decimal('0.0000'), 'pct_change_vs_last_supplied': None, 'recorded_at': datetime(2026, 10, 5, 9, 6, 9, 471094)},
    {'id': 5, 'cost_sheet_id': 4, 'change_no': 1, 'price': Decimal('1411.1559'), 'rm_reference_price': Decimal('65.5000'), 'discount_pct': Decimal('0.0000'), 'pct_change_vs_last_supplied': None, 'recorded_at': datetime(2026, 10, 5, 9, 6, 9, 699496)},
    {'id': 6, 'cost_sheet_id': 5, 'change_no': 1, 'price': Decimal('1024.7200'), 'rm_reference_price': Decimal('65.5000'), 'discount_pct': Decimal('0.0000'), 'pct_change_vs_last_supplied': None, 'recorded_at': datetime(2026, 10, 5, 9, 7, 22, 457464)},
    {'id': 7, 'cost_sheet_id': 3, 'change_no': 2, 'price': Decimal('480.8077'), 'rm_reference_price': Decimal('72.0000'), 'discount_pct': Decimal('0.0000'), 'pct_change_vs_last_supplied': Decimal('5.534658'), 'recorded_at': datetime(2026, 10, 5, 9, 10, 9, 141592)},
    {'id': 8, 'cost_sheet_id': 4, 'change_no': 2, 'price': Decimal('1459.4460'), 'rm_reference_price': Decimal('72.0000'), 'discount_pct': Decimal('0.0000'), 'pct_change_vs_last_supplied': Decimal('3.422027'), 'recorded_at': datetime(2026, 10, 5, 9, 10, 9, 141592)},
    {'id': 9, 'cost_sheet_id': 5, 'change_no': 2, 'price': Decimal('1068.3965'), 'rm_reference_price': Decimal('72.0000'), 'discount_pct': Decimal('0.0000'), 'pct_change_vs_last_supplied': Decimal('4.262282'), 'recorded_at': datetime(2026, 10, 5, 9, 10, 9, 141592)},
    {'id': 10, 'cost_sheet_id': 3, 'change_no': 3, 'price': Decimal('480.8077'), 'rm_reference_price': Decimal('72.0000'), 'discount_pct': Decimal('0.0000'), 'pct_change_vs_last_supplied': Decimal('-0.000006'), 'recorded_at': datetime(2026, 10, 5, 9, 24, 20, 491275)},
    {'id': 11, 'cost_sheet_id': 4, 'change_no': 3, 'price': Decimal('1459.4460'), 'rm_reference_price': Decimal('72.0000'), 'discount_pct': Decimal('0.0000'), 'pct_change_vs_last_supplied': Decimal('0.000002'), 'recorded_at': datetime(2026, 10, 5, 9, 24, 20, 491275)},
    {'id': 12, 'cost_sheet_id': 5, 'change_no': 3, 'price': Decimal('1068.3965'), 'rm_reference_price': Decimal('72.0000'), 'discount_pct': Decimal('0.0000'), 'pct_change_vs_last_supplied': Decimal('-0.000004'), 'recorded_at': datetime(2026, 10, 5, 9, 24, 20, 491275)},
]


def _seed(conn, table: str, columns: list[str], rows: list[dict]) -> None:
    if not rows:
        return
    cols = ", ".join(columns)
    placeholders = ", ".join(f":{c}" for c in columns)
    updates = ", ".join(f"{c} = EXCLUDED.{c}" for c in columns if c != "id")
    sql = text(
        f"INSERT INTO {table} ({cols}) VALUES ({placeholders}) "
        f"ON CONFLICT (id) DO UPDATE SET {updates}"
    )
    for row in rows:
        bound = {k: (json.dumps(v) if isinstance(v, (dict, list)) else v) for k, v in row.items()}
        conn.execute(sql, bound)
    conn.execute(text(
        f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), "
        f"COALESCE((SELECT MAX(id) FROM {table}), 1))"
    ))


def main() -> None:
    with engine.begin() as conn:
        _seed(conn, 'clients', ['id', 'name', 'created_at'], CLIENTS)
        _seed(conn, 'material_grades', ['id', 'name', 'base_grade_id', 'premium_amount', 'updated_at'], MATERIAL_GRADES)
        _seed(conn, 'norm_libraries', ['id', 'client_id', 'label', 'effective_date', 'is_current', 'is_draft', 'created_at'], NORM_LIBRARIES)
        _seed(conn, 'rm_price_bands', ['id', 'norm_library_id', 'grade_id', 'thickness_band', 'price_per_kg', 'updated_at'], RM_PRICE_BANDS)
        _seed(conn, 'scrap_rates', ['id', 'norm_library_id', 'rate_per_kg', 'updated_at'], SCRAP_RATES)
        _seed(conn, 'process_rates', ['id', 'norm_library_id', 'operation_name', 'unit', 'rate', 'sort_order', 'group_label', 'updated_at'], PROCESS_RATES)
        _seed(conn, 'cost_overhead_params', ['id', 'norm_library_id', 'applies_to', 'param_name', 'sort_order', 'param_value', 'updated_at'], COST_OVERHEAD_PARAMS)
        _seed(conn, 'steel_price_buildups', ['id', 'norm_library_id', 'grade_id', 'thickness_band', 'basic_price_per_tonne', 'ust_amount', 'trimming_amount', 'normalising_amount', 'trader_transport_constant', 'updated_at'], STEEL_PRICE_BUILDUPS)
        _seed(conn, 'grade_equivalences', ['id', 'norm_library_id', 'customer_spec', 'material_grade_id', 'notes', 'updated_at'], GRADE_EQUIVALENCES)
        _seed(conn, 'section_catalog_items', ['id', 'norm_library_id', 'category', 'designation', 'kg_per_m', 'rate_per_kg', 'updated_at'], SECTION_CATALOG_ITEMS)
        _seed(conn, 'bo_catalog_items', ['id', 'norm_library_id', 'name', 'category', 'unit_weight_kg', 'rate', 'updated_at'], BO_CATALOG_ITEMS)
        _seed(conn, 'cost_workbooks', ['id', 'client_id', 'name', 'description', 'created_at', 'sets_count'], COST_WORKBOOKS)
        _seed(conn, 'cost_sheets', ['id', 'workbook_id', 'name', 'part_no', 'description', 'drawing_no', 'benchmark_price', 'supply_version', 'discount_pct', 'transport_cost', 'created_at', 'image_url', 'qty_per_set', 'is_optional', 'status', 'remarks', 'first_supply_price', 'first_supply_date', 'first_supply_rm_reference'], COST_SHEETS)
        _seed(conn, 'costing_lines', ['id', 'cost_sheet_id', 'sl_no', 'description', 'spec', 'grade_id', 'thickness_band', 'thickness_mm', 'qty', 'part_weight', 'efficiency_pct', 'parent_line_id'], COSTING_LINES)
        _seed(conn, 'costing_results', ['id', 'costing_line_id', 'norm_library_id', 'calculated_at', 'total_part_weight', 'blank_weight', 'total_blank_weight', 'blank_rate', 'blank_cost', 'process_loss_pct', 'process_loss_weight', 'scrap_weight', 'scrap_cost', 'rm_cost', 'line_process_cost'], COSTING_RESULTS)
        _seed(conn, 'bo_line_items', ['id', 'cost_sheet_id', 'sl_no', 'description', 'qty', 'unit_price', 'catalog_item_id', 'unit_weight_kg'], BO_LINE_ITEMS)
        _seed(conn, 'costing_line_operations', ['id', 'costing_line_id', 'operation_type', 'input_data', 'operation_cost'], COSTING_LINE_OPERATIONS)
        _seed(conn, 'sheet_finishing_ops', ['id', 'cost_sheet_id', 'operation_name', 'input_qty', 'computed_cost'], SHEET_FINISHING_OPS)
        _seed(conn, 'cost_sheet_results', ['id', 'cost_sheet_id', 'norm_library_id', 'calculated_at', 'total_rm_cost', 'overhead_rm', 'rework_rm', 'inventory_rm', 'profit_rm', 'rm_grand_total', 'total_bo_cost', 'overhead_bo', 'inventory_bo', 'profit_bo', 'bo_grand_total', 'total_process_cost', 'overhead_proc', 'rework_proc', 'profit_proc', 'process_grand_total', 'unit_price', 'transport_cost_snap', 'discount_pct_snap', 'price_after_discount', 'pct_change_vs_previous', 'bal_margin', 'bal_margin_per_kg', 'total_part_weight'], COST_SHEET_RESULTS)
        _seed(conn, 'process_cost_rows', ['id', 'costing_line_id', 'equi_spec', 'thk', 'unit_cut_length', 'use_laser', 'machining_rate', 'bev_slant', 'bev_length', 'bend_num_bends', 'drill_size', 'drill_hours', 'drill_type', 'has_rolling'], PROCESS_COST_ROWS)
        _seed(conn, 'price_history_entries', ['id', 'cost_sheet_id', 'change_no', 'price', 'rm_reference_price', 'discount_pct', 'pct_change_vs_last_supplied', 'recorded_at'], PRICE_HISTORY_ENTRIES)
    print("Seed complete.")


if __name__ == "__main__":
    main()
