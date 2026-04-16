import re
from datetime import UTC, datetime

from pytest_httpx import HTTPXMock

from mitonexus.apis.clinicaltrials import ClinicalTrialsClient


async def test_clinical_trials_search(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        method="GET",
        url=re.compile(r"^https://clinicaltrials\.gov/api/v2/studies"),
        json={
            "studies": [
                {
                    "protocolSection": {
                        "identificationModule": {
                            "nctId": "NCT01234567",
                            "briefTitle": "Mitochondrial therapy trial",
                        },
                        "statusModule": {
                            "overallStatus": "RECRUITING",
                            "startDateStruct": {"date": "2025-03-01"},
                        },
                        "descriptionModule": {"briefSummary": "Trial summary."},
                        "conditionsModule": {"conditions": ["Mitochondrial Disease"]},
                        "armsInterventionsModule": {
                            "interventions": [{"name": "Elamipretide"}]
                        },
                    }
                }
            ]
        },
    )

    async with ClinicalTrialsClient() as client:
        trials = await client.search_mito_trials(["mitochondrial disease"])

    assert len(trials) == 1
    trial = trials[0]
    assert trial.nct_id == "NCT01234567"
    assert trial.status == "RECRUITING"
    assert trial.conditions == ["Mitochondrial Disease"]
    assert trial.start_date == datetime(2025, 3, 1, tzinfo=UTC)
