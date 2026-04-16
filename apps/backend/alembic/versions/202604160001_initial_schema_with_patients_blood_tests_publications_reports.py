"""Initial schema with patients, blood_tests, publications, reports."""

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

revision = "202604160001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "patients",
        sa.Column("age", sa.Integer(), nullable=False),
        sa.Column("sex", sa.String(length=1), nullable=False),
        sa.Column("test_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.CheckConstraint("age >= 18 AND age <= 120", name=op.f("ck_patients_patients_age_range")),
        sa.CheckConstraint("sex IN ('M', 'F')", name=op.f("ck_patients_patients_sex_valid")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_patients")),
    )

    op.create_table(
        "publications",
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("external_id", sa.String(length=255), nullable=False),
        sa.Column("doi", sa.String(length=255), nullable=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("abstract", sa.Text(), nullable=True),
        sa.Column(
            "authors",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column("publication_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "mesh_terms",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column("embedding", Vector(768), nullable=True),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_publications")),
    )
    op.create_index(
        op.f("ix_publications_content_hash"), "publications", ["content_hash"], unique=False
    )
    op.create_index(op.f("ix_publications_doi"), "publications", ["doi"], unique=False)
    op.create_index(
        op.f("ix_publications_external_id"), "publications", ["external_id"], unique=True
    )

    op.create_table(
        "blood_tests",
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "raw_values",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "derived_values",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["patient_id"],
            ["patients.id"],
            name=op.f("fk_blood_tests_patient_id_patients"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_blood_tests")),
        sa.UniqueConstraint("patient_id", name=op.f("uq_blood_tests_patient_id")),
    )

    op.create_table(
        "analysis_reports",
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("mitoscore", sa.Float(), nullable=True),
        sa.Column("mitoscore_components", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "affected_cascades",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column("therapy_plan", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("pdf_path", sa.String(), nullable=True),
        sa.Column("visualization_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["patient_id"],
            ["patients.id"],
            name=op.f("fk_analysis_reports_patient_id_patients"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_analysis_reports")),
    )

    op.create_table(
        "agent_runs",
        sa.Column("report_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("agent_name", sa.String(length=255), nullable=False),
        sa.Column(
            "state",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "tool_calls",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column("output", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("langfuse_trace_id", sa.String(length=255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["report_id"],
            ["analysis_reports.id"],
            name=op.f("fk_agent_runs_report_id_analysis_reports"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_agent_runs")),
    )


def downgrade() -> None:
    op.drop_table("agent_runs")
    op.drop_table("analysis_reports")
    op.drop_table("blood_tests")
    op.drop_index(op.f("ix_publications_external_id"), table_name="publications")
    op.drop_index(op.f("ix_publications_doi"), table_name="publications")
    op.drop_index(op.f("ix_publications_content_hash"), table_name="publications")
    op.drop_table("publications")
    op.drop_table("patients")
