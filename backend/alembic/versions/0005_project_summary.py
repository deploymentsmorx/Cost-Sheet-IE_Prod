"""project/quotation summary: sets, qty/set, optional scope, status/remarks

Revision ID: 0005
Revises: 0004
Create Date: 2026-10-05
"""
from alembic import op
import sqlalchemy as sa

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("cost_workbooks", sa.Column("sets_count", sa.Integer, nullable=False, server_default="1"))
    op.add_column("cost_sheets", sa.Column("qty_per_set", sa.Numeric(10, 4), nullable=False, server_default="1"))
    op.add_column("cost_sheets", sa.Column("is_optional", sa.Boolean, nullable=False, server_default="false"))
    op.add_column("cost_sheets", sa.Column("status", sa.String(100), nullable=True))
    op.add_column("cost_sheets", sa.Column("remarks", sa.String(1000), nullable=True))


def downgrade() -> None:
    op.drop_column("cost_sheets", "remarks")
    op.drop_column("cost_sheets", "status")
    op.drop_column("cost_sheets", "is_optional")
    op.drop_column("cost_sheets", "qty_per_set")
    op.drop_column("cost_workbooks", "sets_count")
