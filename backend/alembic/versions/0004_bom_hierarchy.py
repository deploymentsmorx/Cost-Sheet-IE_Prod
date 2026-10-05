"""multi-level BOM: self-referential parent_line_id on costing_lines

Revision ID: 0004
Revises: 0003
Create Date: 2026-10-05
"""
from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("costing_lines", sa.Column("parent_line_id", sa.Integer, sa.ForeignKey("costing_lines.id"), nullable=True))


def downgrade() -> None:
    op.drop_column("costing_lines", "parent_line_id")
