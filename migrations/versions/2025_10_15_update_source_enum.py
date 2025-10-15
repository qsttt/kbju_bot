"""update source_enum to include preset

Revision ID: b1f2a7e4c9d0
Revises: a5d6eb0938d3
Create Date: 2025-10-15
"""
from alembic import op
import sqlalchemy as sa

revision = "b1f2a7e4c9d0"
down_revision = "a5d6eb0938d3"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.execute("ALTER TYPE source_enum ADD VALUE IF NOT EXISTS 'preset';")

def downgrade() -> None:
    # ENUM значения в Postgres безопасно не удаляем
    pass