from __future__ import annotations

from datetime import UTC, datetime

from mitonexus.apis.base import BaseAPIClient
from mitonexus.schemas import ClinicalTrial


class ClinicalTrialsClient(BaseAPIClient):
    """ClinicalTrials.gov v2 API client."""

    base_url = "https://clinicaltrials.gov/api/v2"
    rate_limit_per_second = 2.0

    async def search_mito_trials(
        self,
        conditions: list[str],
        status: str = "RECRUITING",
    ) -> list[ClinicalTrial]:
        """Search mitochondrial clinical trials using condition and status filters."""
        page_token: str | None = None
        trials: list[ClinicalTrial] = []

        while True:
            params: dict[str, str | int] = {
                "query.cond": " OR ".join(conditions),
                "pageSize": 100,
                "format": "json",
                "filter.overallStatus": status,
            }
            if page_token is not None:
                params["pageToken"] = page_token

            response = await self._request("GET", "/studies", params=params)
            payload = response.json()
            for study in payload.get("studies", []):
                trial = self._parse_trial(study)
                if trial is not None:
                    trials.append(trial)

            next_page_token = payload.get("nextPageToken")
            if not isinstance(next_page_token, str) or not next_page_token:
                break
            page_token = next_page_token

        return trials

    def _parse_trial(self, study: dict[object, object]) -> ClinicalTrial | None:
        protocol = study.get("protocolSection")
        if not isinstance(protocol, dict):
            return None

        identification = protocol.get("identificationModule")
        status_module = protocol.get("statusModule")
        description = protocol.get("descriptionModule")
        conditions_module = protocol.get("conditionsModule")
        arms_module = protocol.get("armsInterventionsModule")

        if not isinstance(identification, dict) or not isinstance(status_module, dict):
            return None

        nct_id = identification.get("nctId")
        title = identification.get("briefTitle")
        overall_status = status_module.get("overallStatus")
        if not isinstance(nct_id, str) or not isinstance(title, str) or not isinstance(
            overall_status, str
        ):
            return None

        summary = None
        if isinstance(description, dict):
            brief_summary = description.get("briefSummary")
            if isinstance(brief_summary, str):
                summary = brief_summary

        conditions: list[str] = []
        if isinstance(conditions_module, dict):
            condition_list = conditions_module.get("conditions")
            if isinstance(condition_list, list):
                conditions = [str(condition) for condition in condition_list if str(condition).strip()]

        interventions: list[str] = []
        if isinstance(arms_module, dict):
            intervention_list = arms_module.get("interventions")
            if isinstance(intervention_list, list):
                for item in intervention_list:
                    if isinstance(item, dict):
                        intervention_name = item.get("name")
                        if isinstance(intervention_name, str) and intervention_name.strip():
                            interventions.append(intervention_name)

        return ClinicalTrial(
            nct_id=nct_id,
            title=title,
            summary=summary,
            status=overall_status,
            conditions=conditions,
            interventions=interventions,
            url=f"https://clinicaltrials.gov/study/{nct_id}",
            start_date=self._parse_start_date(status_module),
            metadata=study,
        )

    def _parse_start_date(self, status_module: dict[object, object]) -> datetime | None:
        start_date = status_module.get("startDateStruct")
        if not isinstance(start_date, dict):
            return None
        date_value = start_date.get("date")
        if not isinstance(date_value, str) or not date_value:
            return None
        for fmt in ("%Y-%m-%d", "%Y-%m", "%Y"):
            try:
                parsed = datetime.strptime(date_value, fmt)
                return parsed.replace(tzinfo=UTC)
            except ValueError:
                continue
        return None
