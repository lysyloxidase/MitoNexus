from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from mitonexus.models import AgentRun, AnalysisReport, BloodTest, Patient, Publication


async def test_patient_report_agent_run_crud(db_session: AsyncSession) -> None:
    patient = Patient(
        age=42,
        sex="F",
        test_date=datetime(2026, 4, 16, tzinfo=UTC),
        blood_test=BloodTest(
            raw_values={"glucose": 91.0, "ast": 18.0},
            derived_values={"homa_ir": 1.3, "de_ritis": 0.9},
        ),
        reports=[
            AnalysisReport(
                mitoscore=81.2,
                mitoscore_components={"etc": 32.0, "stress": 49.2},
                affected_cascades=["ampk"],
                therapy_plan={"focus": "recovery"},
                pdf_path="/tmp/report.pdf",
                visualization_data={"layout": "hybrid"},
                agent_runs=[
                    AgentRun(
                        agent_name="mito-analyzer",
                        state={"step": "complete"},
                        tool_calls=[{"tool": "pubmed"}],
                        output={"summary": "stable"},
                        duration_ms=275,
                        langfuse_trace_id="trace-001",
                    )
                ],
            )
        ],
    )

    db_session.add(patient)
    await db_session.commit()

    statement = (
        select(Patient)
        .options(
            selectinload(Patient.blood_test),
            selectinload(Patient.reports).selectinload(AnalysisReport.agent_runs),
        )
        .where(Patient.id == patient.id)
    )
    saved_patient = await db_session.scalar(statement)

    assert saved_patient is not None
    assert saved_patient.blood_test is not None
    assert saved_patient.blood_test.raw_values["glucose"] == 91.0
    assert saved_patient.reports[0].agent_runs[0].agent_name == "mito-analyzer"
    agent_run_id = saved_patient.reports[0].agent_runs[0].id

    saved_patient.age = 43
    await db_session.commit()

    updated_patient = await db_session.scalar(statement)

    assert updated_patient is not None
    assert updated_patient.age == 43

    agent_run = await db_session.scalar(select(AgentRun).where(AgentRun.id == agent_run_id))

    assert agent_run is not None

    await db_session.delete(agent_run)
    await db_session.commit()

    agent_run_count = await db_session.scalar(select(func.count(AgentRun.id)))

    assert agent_run_count == 0


async def test_publication_crud(db_session: AsyncSession) -> None:
    publication = Publication(
        source="pubmed",
        external_id="PMID-100",
        doi="10.1000/mito",
        title="Mitochondrial resilience markers",
        abstract="Study of mitochondrial resilience in adults.",
        authors=["Alice Example", "Bob Example"],
        publication_date=datetime(2025, 1, 1, tzinfo=UTC),
        mesh_terms=["Mitochondria", "Biomarkers"],
        embedding=[0.0] * 768,
        content_hash="a" * 64,
    )

    db_session.add(publication)
    await db_session.commit()

    saved_publication = await db_session.scalar(
        select(Publication).where(Publication.external_id == "PMID-100")
    )

    assert saved_publication is not None
    assert saved_publication.title == "Mitochondrial resilience markers"

    saved_publication.title = "Updated mitochondrial resilience markers"
    await db_session.commit()
    await db_session.refresh(saved_publication)

    assert saved_publication.title == "Updated mitochondrial resilience markers"

    await db_session.delete(saved_publication)
    await db_session.commit()

    deleted_publication = await db_session.scalar(
        select(Publication).where(Publication.external_id == "PMID-100")
    )

    assert deleted_publication is None
