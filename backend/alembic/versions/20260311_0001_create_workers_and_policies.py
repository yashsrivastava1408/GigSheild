"""create workers and policies

Revision ID: 20260311_0001
Revises: None
Create Date: 2026-03-11
"""

from alembic import op
import sqlalchemy as sa


revision = "20260311_0001"
down_revision = None
branch_labels = None
depends_on = None


platform_enum = sa.Enum("zomato", "swiggy", "zepto", "blinkit", name="platform")
coverage_tier_enum = sa.Enum("basic", "standard", "premium", name="coveragetier")
policy_status_enum = sa.Enum("active", "expired", "cancelled", name="policystatus")


def upgrade() -> None:
    op.create_table(
        "workers",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("phone", sa.String(length=10), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("platform", platform_enum, nullable=False),
        sa.Column("zone_id", sa.String(length=64), nullable=False),
        sa.Column("trust_score", sa.Numeric(5, 2), nullable=False, server_default="75.00"),
        sa.Column("avg_weekly_earnings", sa.Numeric(10, 2), nullable=False),
        sa.Column("tenure_days", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("kyc_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_workers_phone", "workers", ["phone"], unique=True)
    op.create_index("ix_workers_zone_id", "workers", ["zone_id"], unique=False)

    op.create_table(
        "policies",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("worker_id", sa.String(length=36), nullable=False),
        sa.Column("coverage_tier", coverage_tier_enum, nullable=False),
        sa.Column("weekly_premium", sa.Numeric(8, 2), nullable=False),
        sa.Column("coverage_amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("status", policy_status_enum, nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["worker_id"], ["workers.id"]),
    )


def downgrade() -> None:
    op.drop_table("policies")
    op.drop_index("ix_workers_zone_id", table_name="workers")
    op.drop_index("ix_workers_phone", table_name="workers")
    op.drop_table("workers")
