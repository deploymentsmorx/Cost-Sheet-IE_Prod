"""master data catalogues: steel price build-up, grade equivalence, section/bar/tube, bought-out master, part image

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-05
"""
from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # steel_price_buildups
    op.create_table(
        "steel_price_buildups",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("norm_library_id", sa.Integer, sa.ForeignKey("norm_libraries.id"), nullable=False),
        sa.Column("grade_id", sa.Integer, sa.ForeignKey("material_grades.id"), nullable=False),
        sa.Column(
            "thickness_band",
            sa.String(20),
            sa.CheckConstraint(
                "thickness_band IN ('<10mm','12mm','>12-19mm','20mm','>20-40mm','>40-63mm','80mm')",
                name="ck_steel_price_buildups_thickness_band",
            ),
            nullable=False,
        ),
        sa.Column("basic_price_per_tonne", sa.Numeric(12, 4), nullable=False, server_default="0"),
        sa.Column("ust_amount", sa.Numeric(12, 4), nullable=False, server_default="0"),
        sa.Column("trimming_amount", sa.Numeric(12, 4), nullable=False, server_default="0"),
        sa.Column("normalising_amount", sa.Numeric(12, 4), nullable=False, server_default="0"),
        sa.Column("trader_transport_constant", sa.Numeric(12, 4), nullable=False, server_default="0"),
        sa.Column(
            "price_per_kg", sa.Numeric(12, 4),
            sa.Computed(
                "(basic_price_per_tonne + ust_amount + trimming_amount + normalising_amount + trader_transport_constant) / 1000",
                persisted=True,
            ),
        ),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("norm_library_id", "grade_id", "thickness_band", name="uq_steel_buildup_grade_band"),
    )

    # grade_equivalences
    op.create_table(
        "grade_equivalences",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("norm_library_id", sa.Integer, sa.ForeignKey("norm_libraries.id"), nullable=False),
        sa.Column("customer_spec", sa.String(100), nullable=False),
        sa.Column("material_grade_id", sa.Integer, sa.ForeignKey("material_grades.id"), nullable=False),
        sa.Column("notes", sa.String(300), nullable=True),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("norm_library_id", "customer_spec", name="uq_grade_equiv_spec"),
    )

    # section_catalog_items
    op.create_table(
        "section_catalog_items",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("norm_library_id", sa.Integer, sa.ForeignKey("norm_libraries.id"), nullable=False),
        sa.Column(
            "category", sa.String(20),
            sa.CheckConstraint(
                "category IN ('channel','angle','round_bar','square_bar','flat_bar','pipe')",
                name="ck_section_catalog_category",
            ),
            nullable=False,
        ),
        sa.Column("designation", sa.String(100), nullable=False),
        sa.Column("kg_per_m", sa.Numeric(10, 4), nullable=False, server_default="0"),
        sa.Column("rate_per_kg", sa.Numeric(12, 4), nullable=False, server_default="0"),
        sa.Column(
            "rate_per_m", sa.Numeric(14, 4),
            sa.Computed("kg_per_m * rate_per_kg", persisted=True),
        ),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("norm_library_id", "designation", name="uq_section_catalog_designation"),
    )

    # bo_catalog_items (reusable bought-out item master)
    op.create_table(
        "bo_catalog_items",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("norm_library_id", sa.Integer, sa.ForeignKey("norm_libraries.id"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column("unit_weight_kg", sa.Numeric(10, 4), nullable=True),
        sa.Column("rate", sa.Numeric(14, 4), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("norm_library_id", "name", name="uq_bo_catalog_name"),
    )

    # cost_sheets.image_url (part master image)
    op.add_column("cost_sheets", sa.Column("image_url", sa.String(500), nullable=True))

    # bo_line_items: optional link back to catalogue + weight (for future total-weight rollup)
    op.add_column("bo_line_items", sa.Column("catalog_item_id", sa.Integer, sa.ForeignKey("bo_catalog_items.id"), nullable=True))
    op.add_column("bo_line_items", sa.Column("unit_weight_kg", sa.Numeric(10, 4), nullable=True))


def downgrade() -> None:
    op.drop_column("bo_line_items", "unit_weight_kg")
    op.drop_column("bo_line_items", "catalog_item_id")
    op.drop_column("cost_sheets", "image_url")
    op.drop_table("bo_catalog_items")
    op.drop_table("section_catalog_items")
    op.drop_table("grade_equivalences")
    op.drop_table("steel_price_buildups")
