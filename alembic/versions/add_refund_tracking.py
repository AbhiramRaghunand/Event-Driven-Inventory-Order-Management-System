
"""Add refund tracking to payments.

Revision ID: c81a4d2e7f90
Revises: f36c612db2a9
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c81a4d2e7f90"
down_revision: Union[str, Sequence[str], None] = "f36c612db2a9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "payments",
        sa.Column(
            "provider_refund_id",
            sa.String(length=100),
            nullable=True,
        ),
    )

    op.add_column(
        "payments",
        sa.Column(
            "refund_amount",
            sa.Numeric(precision=10, scale=2),
            nullable=True,
        ),
    )

    op.add_column(
        "payments",
        sa.Column(
            "refund_status",
            sa.String(length=20),
            server_default="not_required",
            nullable=False,
        ),
    )

    op.add_column(
        "payments",
        sa.Column(
            "refund_idempotency_key",
            sa.String(length=100),
            nullable=True,
        ),
    )

    op.add_column(
        "payments",
        sa.Column(
            "refund_error",
            sa.String(length=500),
            nullable=True,
        ),
    )

    op.add_column(
        "payments",
        sa.Column(
            "refund_created_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    op.add_column(
        "payments",
        sa.Column(
            "refund_updated_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    op.create_unique_constraint(
        "uq_payment_provider_refund_id",
        "payments",
        ["provider_refund_id"],
    )

    op.create_unique_constraint(
        "uq_payment_refund_idempotency_key",
        "payments",
        ["refund_idempotency_key"],
    )

    op.create_check_constraint(
        "ck_payment_refund_amount_positive",
        "payments",
        "refund_amount IS NULL OR refund_amount > 0",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_payment_refund_amount_positive",
        "payments",
        type_="check",
    )

    op.drop_constraint(
        "uq_payment_refund_idempotency_key",
        "payments",
        type_="unique",
    )

    op.drop_constraint(
        "uq_payment_provider_refund_id",
        "payments",
        type_="unique",
    )

    op.drop_column("payments", "refund_updated_at")
    op.drop_column("payments", "refund_created_at")
    op.drop_column("payments", "refund_error")
    op.drop_column("payments", "refund_idempotency_key")
    op.drop_column("payments", "refund_status")
    op.drop_column("payments", "refund_amount")
    op.drop_column("payments", "provider_refund_id")
