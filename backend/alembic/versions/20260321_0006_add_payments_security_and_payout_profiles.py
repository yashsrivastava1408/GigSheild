"""add payments security and payout profiles

Revision ID: 20260321_0006
Revises: 20260311_0005
Create Date: 2026-03-21
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260321_0006"
down_revision = "20260311_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    payout_profile_status = postgresql.ENUM(
        "missing", "pending", "verified", "rejected", name="payoutprofilestatus", create_type=False
    )
    policy_payment_status = postgresql.ENUM(
        "created", "verified", "paid", "failed", name="policypaymentstatus", create_type=False
    )
    payment_method = postgresql.ENUM("upi", "bank_transfer", name="paymentmethod", create_type=False)
    bind = op.get_bind()
    payout_profile_status.create(bind, checkfirst=True)
    policy_payment_status.create(bind, checkfirst=True)
    payment_method.create(bind, checkfirst=True)

    with op.batch_alter_table("otp_challenges") as batch_op:
        batch_op.add_column(sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"))

    with op.batch_alter_table("workers") as batch_op:
        batch_op.add_column(sa.Column("payout_method", payment_method, nullable=True))
        batch_op.add_column(sa.Column("payout_upi_id", sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column("payout_bank_account_name", sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column("payout_bank_account_number", sa.String(length=32), nullable=True))
        batch_op.add_column(sa.Column("payout_bank_ifsc", sa.String(length=16), nullable=True))
        batch_op.add_column(sa.Column("payout_contact_name", sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column("payout_contact_phone", sa.String(length=10), nullable=True))
        batch_op.add_column(sa.Column("payout_fund_account_id", sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column("payout_profile_status", payout_profile_status, nullable=False, server_default="missing"))
        batch_op.add_column(sa.Column("payout_profile_review_notes", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("payout_profile_reviewed_at", sa.DateTime(timezone=True), nullable=True))

    with op.batch_alter_table("payouts") as batch_op:
        batch_op.add_column(sa.Column("idempotency_key", sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column("failure_reason", sa.String(length=255), nullable=True))
        batch_op.create_unique_constraint("uq_payouts_idempotency_key", ["idempotency_key"])

    op.create_table(
        "policy_payments",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("worker_id", sa.String(length=36), nullable=False),
        sa.Column("policy_id", sa.String(length=36), nullable=True),
        sa.Column(
            "coverage_tier",
            postgresql.ENUM("basic", "standard", "premium", name="coveragetier", create_type=False),
            nullable=False,
        ),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("currency", sa.String(length=8), nullable=False),
        sa.Column("razorpay_order_id", sa.String(length=100), nullable=False),
        sa.Column("razorpay_payment_id", sa.String(length=100), nullable=True),
        sa.Column("idempotency_key", sa.String(length=100), nullable=False),
        sa.Column("status", policy_payment_status, nullable=False),
        sa.Column("signature_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("raw_payload", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["worker_id"], ["workers.id"]),
        sa.ForeignKeyConstraint(["policy_id"], ["policies.id"]),
        sa.UniqueConstraint("razorpay_order_id"),
        sa.UniqueConstraint("razorpay_payment_id"),
        sa.UniqueConstraint("idempotency_key"),
    )

    op.create_table(
        "webhook_events",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("provider_event_id", sa.String(length=100), nullable=False),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("provider_event_id"),
    )


def downgrade() -> None:
    op.drop_table("webhook_events")
    op.drop_table("policy_payments")
    op.drop_constraint("uq_payouts_idempotency_key", "payouts", type_="unique")
    op.drop_column("payouts", "failure_reason")
    op.drop_column("payouts", "idempotency_key")
    op.drop_column("workers", "payout_profile_reviewed_at")
    op.drop_column("workers", "payout_profile_review_notes")
    op.drop_column("workers", "payout_profile_status")
    op.drop_column("workers", "payout_fund_account_id")
    op.drop_column("workers", "payout_contact_phone")
    op.drop_column("workers", "payout_contact_name")
    op.drop_column("workers", "payout_bank_ifsc")
    op.drop_column("workers", "payout_bank_account_number")
    op.drop_column("workers", "payout_bank_account_name")
    op.drop_column("workers", "payout_upi_id")
    op.drop_column("workers", "payout_method")
    op.drop_column("otp_challenges", "attempt_count")
