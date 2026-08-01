"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-07-11
"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # clients
    op.create_table(
        "clients",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(200), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )

    # norm_libraries
    op.create_table(
        "norm_libraries",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("client_id", sa.Integer, sa.ForeignKey("clients.id"), nullable=False),
        sa.Column("label", sa.String(100), nullable=False),
        sa.Column("effective_date", sa.Date, nullable=False),
        sa.Column("is_current", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("is_draft", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )

    # material_grades
    op.create_table(
        "material_grades",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("base_grade_id", sa.Integer, sa.ForeignKey("material_grades.id"), nullable=True),
        sa.Column("premium_amount", sa.Numeric(12, 4), nullable=True),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )

    # rm_price_bands
    op.create_table(
        "rm_price_bands",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("norm_library_id", sa.Integer, sa.ForeignKey("norm_libraries.id"), nullable=False),
        sa.Column("grade_id", sa.Integer, sa.ForeignKey("material_grades.id"), nullable=False),
        sa.Column(
            "thickness_band",
            sa.String(20),
            sa.CheckConstraint(
                "thickness_band IN ('<10mm','12mm','>12-19mm','20mm','>20-40mm','>40-63mm','80mm')",
                name="ck_rm_price_bands_thickness_band",
            ),
            nullable=False,
        ),
        sa.Column("price_per_kg", sa.Numeric(12, 4), nullable=False),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )

    # scrap_rates
    op.create_table(
        "scrap_rates",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("norm_library_id", sa.Integer, sa.ForeignKey("norm_libraries.id"), nullable=False, unique=True),
        sa.Column("rate_per_kg", sa.Numeric(12, 4), nullable=False),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )

    # process_rates
    op.create_table(
        "process_rates",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("norm_library_id", sa.Integer, sa.ForeignKey("norm_libraries.id"), nullable=False),
        sa.Column("operation_name", sa.String(200), nullable=False),
        sa.Column(
            "unit",
            sa.Enum("Rs/Kg", "Rs/Hr", "Rs/mm/meter", "Rs/slant/meter", "Rs/Nos", "Rs/Sqm", "%", name="process_unit"),
            nullable=False,
        ),
        sa.Column("rate", sa.Numeric(12, 4), nullable=False),
        sa.Column("sort_order", sa.Integer, nullable=False, server_default="0"),
        sa.Column("group_label", sa.String(100), nullable=False, server_default=""),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )

    # cost_overhead_params
    op.create_table(
        "cost_overhead_params",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("norm_library_id", sa.Integer, sa.ForeignKey("norm_libraries.id"), nullable=False),
        sa.Column(
            "applies_to",
            sa.Enum("raw_material", "bought_out", "process_cost", name="applies_to_enum"),
            nullable=False,
        ),
        sa.Column("param_name", sa.String(100), nullable=False),
        sa.Column("sort_order", sa.Integer, nullable=False, server_default="0"),
        sa.Column("param_value", sa.Numeric(8, 4), nullable=True),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )

    # cost_workbooks
    op.create_table(
        "cost_workbooks",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("client_id", sa.Integer, sa.ForeignKey("clients.id"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )

    # cost_sheets (merged part + costing_sheet)
    op.create_table(
        "cost_sheets",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("workbook_id", sa.Integer, sa.ForeignKey("cost_workbooks.id"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("part_no", sa.String(100), nullable=True),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("drawing_no", sa.String(100), nullable=True),
        sa.Column("benchmark_price", sa.Numeric(14, 4), nullable=True),
        sa.Column("supply_version", sa.String(100), nullable=False, server_default="V1"),
        sa.Column("discount_pct", sa.Numeric(8, 4), nullable=False, server_default="0"),
        sa.Column("transport_cost", sa.Numeric(14, 4), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )

    # costing_lines
    op.create_table(
        "costing_lines",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("cost_sheet_id", sa.Integer, sa.ForeignKey("cost_sheets.id"), nullable=False),
        sa.Column("sl_no", sa.Integer, nullable=False),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("spec", sa.String(200), nullable=True),
        sa.Column("grade_id", sa.Integer, sa.ForeignKey("material_grades.id"), nullable=True),
        sa.Column("thickness_band", sa.String(20), nullable=True),
        sa.Column("thickness_mm", sa.Numeric(8, 2), nullable=True),
        sa.Column("qty", sa.Numeric(10, 4), nullable=False, server_default="1"),
        sa.Column("part_weight", sa.Numeric(12, 4), nullable=False, server_default="0"),
        sa.Column("efficiency_pct", sa.Numeric(8, 4), nullable=False, server_default="100"),
    )

    # costing_results
    op.create_table(
        "costing_results",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("costing_line_id", sa.Integer, sa.ForeignKey("costing_lines.id"), unique=True, nullable=False),
        sa.Column("norm_library_id", sa.Integer, sa.ForeignKey("norm_libraries.id"), nullable=False),
        sa.Column("calculated_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("total_part_weight", sa.Numeric(14, 6), nullable=True),
        sa.Column("blank_weight", sa.Numeric(14, 6), nullable=True),
        sa.Column("total_blank_weight", sa.Numeric(14, 6), nullable=True),
        sa.Column("blank_rate", sa.Numeric(14, 6), nullable=True),
        sa.Column("blank_cost", sa.Numeric(14, 4), nullable=True),
        sa.Column("process_loss_pct", sa.Numeric(8, 4), nullable=True),
        sa.Column("process_loss_weight", sa.Numeric(14, 6), nullable=True),
        sa.Column("scrap_weight", sa.Numeric(14, 6), nullable=True),
        sa.Column("scrap_cost", sa.Numeric(14, 4), nullable=True),
        sa.Column("rm_cost", sa.Numeric(14, 4), nullable=True),
        sa.Column("line_process_cost", sa.Numeric(14, 4), nullable=True),
    )

    # bo_line_items
    op.create_table(
        "bo_line_items",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("cost_sheet_id", sa.Integer, sa.ForeignKey("cost_sheets.id"), nullable=False),
        sa.Column("sl_no", sa.Integer, nullable=False, server_default="1"),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("qty", sa.Numeric(10, 4), nullable=False, server_default="1"),
        sa.Column("unit_price", sa.Numeric(14, 4), nullable=False, server_default="0"),
        sa.Column("bo_line_cost", sa.Numeric(14, 4), sa.Computed("qty * unit_price", persisted=True)),
    )

    # costing_line_operations
    op.create_table(
        "costing_line_operations",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("costing_line_id", sa.Integer, sa.ForeignKey("costing_lines.id"), nullable=False),
        sa.Column("operation_type", sa.String(50), nullable=False),
        sa.Column("input_data", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("operation_cost", sa.Numeric(14, 4), nullable=False, server_default="0"),
    )

    # sheet_finishing_ops
    op.create_table(
        "sheet_finishing_ops",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("cost_sheet_id", sa.Integer, sa.ForeignKey("cost_sheets.id"), nullable=False),
        sa.Column("operation_name", sa.String(100), nullable=False),
        sa.Column("input_qty", sa.Numeric(14, 4), nullable=False, server_default="0"),
        sa.Column("computed_cost", sa.Numeric(14, 4), nullable=False, server_default="0"),
    )

    # cost_sheet_results
    op.create_table(
        "cost_sheet_results",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("cost_sheet_id", sa.Integer, sa.ForeignKey("cost_sheets.id"), unique=True, nullable=False),
        sa.Column("norm_library_id", sa.Integer, sa.ForeignKey("norm_libraries.id"), nullable=False),
        sa.Column("calculated_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("total_rm_cost", sa.Numeric(14, 4), nullable=True),
        sa.Column("overhead_rm", sa.Numeric(14, 4), nullable=True),
        sa.Column("rework_rm", sa.Numeric(14, 4), nullable=True),
        sa.Column("inventory_rm", sa.Numeric(14, 4), nullable=True),
        sa.Column("profit_rm", sa.Numeric(14, 4), nullable=True),
        sa.Column("rm_grand_total", sa.Numeric(14, 4), nullable=True),
        sa.Column("total_bo_cost", sa.Numeric(14, 4), nullable=True),
        sa.Column("overhead_bo", sa.Numeric(14, 4), nullable=True),
        sa.Column("inventory_bo", sa.Numeric(14, 4), nullable=True),
        sa.Column("profit_bo", sa.Numeric(14, 4), nullable=True),
        sa.Column("bo_grand_total", sa.Numeric(14, 4), nullable=True),
        sa.Column("total_process_cost", sa.Numeric(14, 4), nullable=True),
        sa.Column("overhead_proc", sa.Numeric(14, 4), nullable=True),
        sa.Column("rework_proc", sa.Numeric(14, 4), nullable=True),
        sa.Column("profit_proc", sa.Numeric(14, 4), nullable=True),
        sa.Column("process_grand_total", sa.Numeric(14, 4), nullable=True),
        sa.Column("unit_price", sa.Numeric(14, 4), nullable=True),
        sa.Column("transport_cost_snap", sa.Numeric(14, 4), nullable=True),
        sa.Column("discount_pct_snap", sa.Numeric(8, 4), nullable=True),
        sa.Column("price_after_discount", sa.Numeric(14, 4), nullable=True),
        sa.Column("pct_change_vs_previous", sa.Numeric(10, 6), nullable=True),
        sa.Column("bal_margin", sa.Numeric(14, 4), nullable=True),
        sa.Column("bal_margin_per_kg", sa.Numeric(14, 4), nullable=True),
        sa.Column("total_part_weight", sa.Numeric(14, 6), nullable=True),
    )

    # process_cost_rows
    op.create_table(
        "process_cost_rows",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("costing_line_id", sa.Integer, sa.ForeignKey("costing_lines.id"), unique=True, nullable=False),
        sa.Column("equi_spec", sa.String(200), nullable=True),
        sa.Column("thk", sa.Numeric(8, 2), nullable=True),
        sa.Column("unit_cut_length", sa.Numeric(10, 4), nullable=True),
        sa.Column("use_laser", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("machining_rate", sa.Numeric(14, 4), nullable=True),
        sa.Column("bev_slant", sa.Numeric(8, 4), nullable=True),
        sa.Column("bev_length", sa.Numeric(10, 4), nullable=True),
        sa.Column("bend_num_bends", sa.Integer, nullable=True),
        sa.Column("drill_size", sa.String(50), nullable=True),
        sa.Column("drill_hours", sa.Numeric(10, 4), nullable=True),
        sa.Column("drill_type", sa.String(20), nullable=False, server_default="regular"),
        sa.Column("has_rolling", sa.Boolean, nullable=False, server_default="false"),
    )


def downgrade() -> None:
    op.drop_table("process_cost_rows")
    op.drop_table("cost_sheet_results")
    op.drop_table("sheet_finishing_ops")
    op.drop_table("costing_line_operations")
    op.drop_table("bo_line_items")
    op.drop_table("costing_results")
    op.drop_table("costing_lines")
    op.drop_table("cost_sheets")
    op.drop_table("cost_workbooks")
    op.drop_table("cost_overhead_params")
    op.drop_table("process_rates")
    op.drop_table("scrap_rates")
    op.drop_table("rm_price_bands")
    op.drop_table("material_grades")
    op.drop_table("norm_libraries")
    op.drop_table("clients")
    op.execute("DROP TYPE IF EXISTS process_unit")
    op.execute("DROP TYPE IF EXISTS applies_to_enum")
