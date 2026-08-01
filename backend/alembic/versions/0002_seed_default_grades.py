"""seed default material grades

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-11
"""
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        INSERT INTO material_grades (name, base_grade_id, premium_amount, updated_at)
        VALUES ('IS2062 E250BR', NULL, NULL, NOW())
        ON CONFLICT (name) DO NOTHING
    """)
    op.execute("""
        INSERT INTO material_grades (name, base_grade_id, premium_amount, updated_at)
        SELECT 'IS2062 E350C', id, 5.0, NOW()
        FROM material_grades WHERE name = 'IS2062 E250BR'
        ON CONFLICT (name) DO NOTHING
    """)


def downgrade() -> None:
    op.execute("DELETE FROM material_grades WHERE name IN ('IS2062 E250BR', 'IS2062 E350C')")
