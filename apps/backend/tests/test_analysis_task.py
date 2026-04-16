from __future__ import annotations

import asyncio

from mitonexus.tasks.analysis import run_analysis_workflow
from mitonexus.tasks.runtime import run_async_in_worker


async def _current_loop_id() -> int:
    return id(asyncio.get_running_loop())


def test_run_async_in_worker_reuses_same_event_loop_per_thread() -> None:
    first_loop_id = run_async_in_worker(_current_loop_id())
    second_loop_id = run_async_in_worker(_current_loop_id())

    assert first_loop_id == second_loop_id


def test_run_analysis_workflow_marks_failed_only_after_final_error(monkeypatch) -> None:
    observed_failures: list[tuple[str, str]] = []

    async def fail_workflow(
        *,
        patient_id: str,
        blood_test_id: str,
        report_id: str,
    ) -> dict[str, object]:
        del patient_id, blood_test_id, report_id
        msg = "workflow boom"
        raise RuntimeError(msg)

    async def fake_mark_report_failed(report_id: str, error_message: str) -> None:
        observed_failures.append((report_id, error_message))

    monkeypatch.setattr("mitonexus.tasks.analysis._run_analysis_workflow_async", fail_workflow)
    monkeypatch.setattr("mitonexus.tasks.analysis._mark_report_failed", fake_mark_report_failed)
    monkeypatch.setattr(run_analysis_workflow, "max_retries", 0, raising=False)

    result = run_analysis_workflow.apply(
        kwargs={
            "patient_id": "patient-1",
            "blood_test_id": "blood-test-1",
            "report_id": "report-1",
        },
        throw=False,
    )

    assert result.failed()
    assert observed_failures == [("report-1", "workflow boom")]
