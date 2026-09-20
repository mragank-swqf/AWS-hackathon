"""Store a person's applicability decision so refresh does not overwrite it.

Revision ID: 0003_applicability_review
Revises: 0002_rbi_intelligence
Create Date: 2026-09-19
"""

from __future__ import annotations

from alembic import op

revision = "0003_applicability_review"
down_revision = "0002_rbi_intelligence"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE regulation_applicability
            ADD COLUMN IF NOT EXISTS reviewer_applicability TEXT,
            ADD COLUMN IF NOT EXISTS reviewer_decided_at TIMESTAMP
        """
    )


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE regulation_applicability
            DROP COLUMN IF EXISTS reviewer_decided_at,
            DROP COLUMN IF EXISTS reviewer_applicability
        """
    )
