"""create disruptions claims and payouts

Revision ID: 20260311_0002
Revises: 20260311_0001
Create Date: 2026-03-11
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260311_0002"
down_revision = "20260311_0001"
branch_labels = None
depends_on = None


disruption_event_type_enum = postgresql.ENUM(
    "heavy_rain",
    "extreme_heat",
    "flood",
    "aqi",
    "curfew",
    "outage",
    name="disruptioneventtype",
)
claim_status_enum = postgresql.ENUM(
    "auto_approved",
    "manual_review",
    "rejected",
    "paid",
    name="claimstatus",
)
payout_status_enum = postgresql.ENUM("pending", "processing", "completed", "failed", name="payoutstatus", create_type=False)
payment_method_enum = postgresql.ENUM("upi", "bank_transfer", name="paymentmethod", create_type=False)


def upgrade() -> None:
    bind = op.get_bind()
    disruption_event_type_enum.create(bind, checkfirst=True)
    claim_status_enum.create(bind, checkfirst=True)
    payout_status_enum.create(bind, checkfirst=True)
    payment_method_enum.create(bind, checkfirst=True)

    op.create_table(
        "disruption_events",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("event_type", disruption_event_type_enum, nullable=False),
        sa.Column("zone_id", sa.String(length=64), nullable=False),
        sa.Column("severity", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("weather_api_raw", sa.JSON(), nullable=True),
        sa.Column("verified", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_disruption_events_zone_id", "disruption_events", ["zone_id"], unique=False)

    op.create_table(
        "claims",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("policy_id", sa.String(length=36), nullable=False),
        sa.Column("worker_id", sa.String(length=36), nullable=False),
        sa.Column("disruption_event_id", sa.String(length=36), nullable=False),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("status", claim_status_enum, nullable=False),
        sa.Column("fraud_score", sa.Numeric(5, 2), nullable=False),
        sa.Column("trust_score_at_claim", sa.Numeric(5, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["policy_id"], ["policies.id"]),
        sa.ForeignKeyConstraint(["worker_id"], ["workers.id"]),
        sa.ForeignKeyConstraint(["disruption_event_id"], ["disruption_events.id"]),
    )

    op.create_table(
        "payouts",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("claim_id", sa.String(length=36), nullable=False),
        sa.Column("worker_id", sa.String(length=36), nullable=False),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("payment_method", payment_method_enum, nullable=False),
        sa.Column("razorpay_payment_id", sa.String(length=100), nullable=False),
        sa.Column("status", payout_status_enum, nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["claim_id"], ["claims.id"]),
        sa.ForeignKeyConstraint(["worker_id"], ["workers.id"]),
        sa.UniqueConstraint("claim_id"),
    )


def downgrade() -> None:
    op.drop_table("payouts")
    op.drop_table("claims")
    op.drop_index("ix_disruption_events_zone_id", table_name="disruption_events")
    op.drop_table("disruption_events")
