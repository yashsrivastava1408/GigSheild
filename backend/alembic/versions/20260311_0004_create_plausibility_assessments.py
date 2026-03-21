"""create plausibility assessments

Revision ID: 20260311_0004
Revises: 20260311_0003
Create Date: 2026-03-11
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260311_0004"
down_revision = "20260311_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    risk_tier = postgresql.ENUM("low", "medium", "high", name="risktier", create_type=False)
    routing_decision = postgresql.ENUM("approve", "manual_review", "reject", name="routingdecision", create_type=False)
    bind = op.get_bind()
    risk_tier.create(bind, checkfirst=True)
    routing_decision.create(bind, checkfirst=True)
    op.create_table(
        "plausibility_assessments",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("claim_id", sa.String(length=36), nullable=False, unique=True),
        sa.Column("plausibility_score", sa.Integer(), nullable=False),
        sa.Column("risk_tier", risk_tier, nullable=False),
        sa.Column("signals", sa.JSON(), nullable=False),
        sa.Column("routing_decision", routing_decision, nullable=False),
        sa.Column("assessed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["claim_id"], ["claims.id"]),
    )


def downgrade() -> None:
    op.drop_table("plausibility_assessments")
