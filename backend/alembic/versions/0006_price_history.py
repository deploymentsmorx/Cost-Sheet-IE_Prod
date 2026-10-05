"""price history & repricing: first-supply snapshot + per-sheet change log

Revision ID: 0006
Revises: 0005
Create Date: 2026-10-05
"""
from alembic import op
import sqlalchemy as sa

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("cost_sheets", sa.Column("first_supply_price", sa.Numeric(14, 4), nullable=True))
    op.add_column("cost_sheets", sa.Column("first_supply_date", sa.Date, nullable=True))
    op.add_column("cost_sheets", sa.Column("first_supply_rm_reference", sa.Numeric(12, 4), nullable=True))

    op.create_table(
        "price_history_entries",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("cost_sheet_id", sa.Integer, sa.ForeignKey("cost_sheets.id"), nullable=False),
        sa.Column("change_no", sa.Integer, nullable=False),
        sa.Column("price", sa.Numeric(14, 4), nullable=False),
        sa.Column("rm_reference_price", sa.Numeric(12, 4), nullable=True),
        sa.Column("discount_pct", sa.Numeric(8, 4), nullable=False, server_default="0"),
        sa.Column("pct_change_vs_last_supplied", sa.Numeric(10, 6), nullable=True),
        sa.Column("recorded_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("cost_sheet_id", "change_no", name="uq_price_history_sheet_change"),
    )


def downgrade() -> None:
    op.drop_table("price_history_entries")
    op.drop_column("cost_sheets", "first_supply_rm_reference")
    op.drop_column("cost_sheets", "first_supply_date")
    op.drop_column("cost_sheets", "first_supply_price")
