import httpx
import pytest

from mitonexus.main import app


def _sample_payload() -> dict[str, object]:
    return {
        "patient_age": 42,
        "patient_sex": "M",
        "test_date": "2026-04-16",
        "markers": [
            {"marker_id": "glucose", "value": 109.0, "unit": "mg/dL"},
            {"marker_id": "insulin", "value": 16.0, "unit": "uIU/mL"},
            {"marker_id": "homocysteine", "value": 16.8, "unit": "umol/L"},
            {"marker_id": "vitamin_d", "value": 24.0, "unit": "ng/mL"},
            {"marker_id": "ggtp", "value": 36.0, "unit": "U/L"},
        ],
    }


@pytest.mark.anyio
async def test_blood_test_analysis_flow() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        analyze_response = await client.post("/api/v1/blood-test/analyze", json=_sample_payload())

        assert analyze_response.status_code == 200
        body = analyze_response.json()
        assert body["report_id"]

        markers_response = await client.get("/api/v1/blood-test/markers")
        assert markers_response.status_code == 200
        markers = markers_response.json()
        assert len(markers) == 41
        assert any(marker["id"] == "homocysteine" for marker in markers)

        detail_response = await client.get("/api/v1/blood-test/marker/homocysteine")
        assert detail_response.status_code == 200
        assert detail_response.json()["mito_cascades"] == ["uprmt", "nrf2_keap1", "transsulfuration"]

        report_response = await client.get(f"/api/v1/report/{body['report_id']}")
        assert report_response.status_code == 200
        report = report_response.json()
        assert report["marker_analyses"]
        assert report["cascade_assessments"]
        assert report["therapy_plan"]["priority_therapies"]

        visualization_response = await client.get(f"/api/v1/report/{body['report_id']}/visualization")
        assert visualization_response.status_code == 200
        visualization = visualization_response.json()
        assert "knowledge_graph" in visualization
        assert "mitochondrion" in visualization
