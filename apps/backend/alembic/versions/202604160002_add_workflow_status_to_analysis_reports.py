"""Add workflow status metadata to analysis reports."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "202604160002"
down_revision = "202604160001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "analysis_reports",
        sa.Column("status", sa.String(length=32), server_default="processing", nullable=False),
    )
    op.add_column(
        "analysis_reports",
        sa.Column("workflow_task_id", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "analysis_reports",
        sa.Column("error_message", sa.String(), nullable=True),
    )
    op.add_column(
        "analysis_reports",
        sa.Column(
            "literature_evidence",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
    )
    op.alter_column("analysis_reports", "status", server_default=None)


def downgrade() -> None:
    op.drop_column("analysis_reports", "literature_evidence")
    op.drop_column("analysis_reports", "error_message")
    op.drop_column("analysis_reports", "workflow_task_id")
    op.drop_column("analysis_reports", "status")
