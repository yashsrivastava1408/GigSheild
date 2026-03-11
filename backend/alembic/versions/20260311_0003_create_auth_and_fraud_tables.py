"""create auth and fraud tables

Revision ID: 20260311_0003
Revises: 20260311_0002
Create Date: 2026-03-11
"""

from alembic import op
import sqlalchemy as sa


revision = "20260311_0003"
down_revision = "20260311_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "otp_challenges",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("phone", sa.String(length=10), nullable=False),
        sa.Column("otp_code", sa.String(length=6), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_otp_challenges_phone", "otp_challenges", ["phone"], unique=False)

    op.create_table(
        "auth_sessions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("worker_id", sa.String(length=36), nullable=False),
        sa.Column("token", sa.String(length=255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["worker_id"], ["workers.id"]),
        sa.UniqueConstraint("token"),
    )

    claim_status_enum = sa.Enum("auto_approved", "manual_review", "rejected", "paid", name="claimstatus", create_type=False)
    op.create_table(
        "fraud_logs",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("worker_id", sa.String(length=36), nullable=False),
        sa.Column("claim_id", sa.String(length=36), nullable=False),
        sa.Column("fraud_type", sa.String(length=100), nullable=False),
        sa.Column("fraud_score", sa.Numeric(5, 2), nullable=False),
        sa.Column("signals", sa.JSON(), nullable=False),
        sa.Column("action_taken", claim_status_enum, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["worker_id"], ["workers.id"]),
        sa.ForeignKeyConstraint(["claim_id"], ["claims.id"]),
    )


def downgrade() -> None:
    op.drop_table("fraud_logs")
    op.drop_table("auth_sessions")
    op.drop_index("ix_otp_challenges_phone", table_name="otp_challenges")
    op.drop_table("otp_challenges")
