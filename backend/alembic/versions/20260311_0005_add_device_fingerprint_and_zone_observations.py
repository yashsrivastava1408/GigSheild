"""add device fingerprint and worker zone observations

Revision ID: 20260311_0005
Revises: 20260311_0004
Create Date: 2026-03-21
"""

from alembic import op
import sqlalchemy as sa


revision = "20260311_0005"
down_revision = "20260311_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("workers") as batch_op:
        batch_op.add_column(sa.Column("device_fingerprint", sa.String(length=128), nullable=True))
        batch_op.create_index("ix_workers_device_fingerprint", ["device_fingerprint"], unique=False)

    op.create_table(
        "worker_zone_observations",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("worker_id", sa.String(length=36), nullable=False),
        sa.Column("zone_id", sa.String(length=64), nullable=False),
        sa.Column("source", sa.String(length=50), nullable=False),
        sa.Column(
            "observed_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(["worker_id"], ["workers.id"]),
    )
    op.create_index("ix_worker_zone_observations_worker_id", "worker_zone_observations", ["worker_id"], unique=False)
    op.create_index("ix_worker_zone_observations_zone_id", "worker_zone_observations", ["zone_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_worker_zone_observations_zone_id", table_name="worker_zone_observations")
    op.drop_index("ix_worker_zone_observations_worker_id", table_name="worker_zone_observations")
    op.drop_table("worker_zone_observations")
    op.drop_index("ix_workers_device_fingerprint", table_name="workers")
    op.drop_column("workers", "device_fingerprint")
