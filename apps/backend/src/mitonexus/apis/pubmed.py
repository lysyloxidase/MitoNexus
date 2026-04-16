from __future__ import annotations

from datetime import UTC, datetime
from xml.etree import ElementTree

from mitonexus.apis.base import BaseAPIClient
from mitonexus.config import get_settings
from mitonexus.models import Publication

MONTHS: dict[str, int] = {
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}


class PubMedClient(BaseAPIClient):
    """NCBI PubMed E-utilities client."""

    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    rate_limit_per_second = 3.0

    def __init__(self) -> None:
        super().__init__()
        settings = get_settings()
        self._api_key = settings.pubmed_api_key
        if self._api_key:
            self.rate_limit_per_second = 10.0

    async def search_recent(
        self,
        mesh_terms: list[str],
        from_date: str,
        to_date: str,
    ) -> list[str]:
        """Get PMIDs matching MeSH terms within a date range."""
        query = " AND ".join(f'"{term}"[MeSH]' for term in mesh_terms)
        params = {
            "db": "pubmed",
            "term": f'{query} AND ("{from_date}"[EDAT]:"{to_date}"[EDAT])',
            "retmode": "json",
            "retmax": 200,
        }
        if self._api_key:
            params["api_key"] = self._api_key

        response = await self._request("GET", "/esearch.fcgi", params=params)
        payload = response.json()
        id_list = payload.get("esearchresult", {}).get("idlist", [])
        return [str(identifier) for identifier in id_list]

    async def fetch_abstracts(self, pmids: list[str]) -> list[Publication]:
        """Fetch PubMed abstracts in XML and normalize them into publications."""
        if not pmids:
            return []

        publications: list[Publication] = []
        for batch_start in range(0, len(pmids), 100):
            batch = pmids[batch_start : batch_start + 100]
            params = {
                "db": "pubmed",
                "id": ",".join(batch),
                "retmode": "xml",
            }
            if self._api_key:
                params["api_key"] = self._api_key

            response = await self._request("GET", "/efetch.fcgi", params=params)
            publications.extend(self._parse_publications(response.text))

        return publications

    def _parse_publications(self, xml_payload: str) -> list[Publication]:
        root = ElementTree.fromstring(xml_payload)
        publications: list[Publication] = []

        for article in root.findall(".//PubmedArticle"):
            pmid = article.findtext(".//MedlineCitation/PMID")
            title = article.findtext(".//Article/ArticleTitle")
            if not pmid or not title:
                continue

            abstract_parts = []
            for abstract_node in article.findall(".//Article/Abstract/AbstractText"):
                label = abstract_node.attrib.get("Label")
                text = "".join(abstract_node.itertext()).strip()
                if not text:
                    continue
                abstract_parts.append(f"{label}: {text}" if label else text)

            authors = []
            for author_node in article.findall(".//AuthorList/Author"):
                last_name = author_node.findtext("LastName")
                fore_name = author_node.findtext("ForeName")
                collective = author_node.findtext("CollectiveName")
                if collective:
                    authors.append(collective)
                elif last_name and fore_name:
                    authors.append(f"{fore_name} {last_name}")
                elif last_name:
                    authors.append(last_name)

            mesh_terms = [
                descriptor.text.strip()
                for descriptor in article.findall(".//MeshHeadingList/MeshHeading/DescriptorName")
                if descriptor.text
            ]
            doi = self._extract_doi(article)
            publication_date = self._extract_publication_date(article)
            abstract = " ".join(abstract_parts) if abstract_parts else None

            publications.append(
                Publication(
                    source="pubmed",
                    external_id=pmid,
                    doi=doi,
                    title=" ".join(title.split()),
                    abstract=abstract,
                    authors=authors,
                    publication_date=publication_date,
                    mesh_terms=mesh_terms,
                    embedding=None,
                    content_hash="",
                )
            )

        return publications

    def _extract_doi(self, article: ElementTree.Element) -> str | None:
        for identifier in article.findall(".//PubmedData/ArticleIdList/ArticleId"):
            if identifier.attrib.get("IdType") == "doi" and identifier.text:
                return identifier.text.strip()
        for location in article.findall(".//ELocationID"):
            if location.attrib.get("EIdType") == "doi" and location.text:
                return location.text.strip()
        return None

    def _extract_publication_date(self, article: ElementTree.Element) -> datetime | None:
        pub_date = article.find(".//Article/Journal/JournalIssue/PubDate")
        if pub_date is None:
            return None

        year_text = pub_date.findtext("Year")
        medline_date = pub_date.findtext("MedlineDate")
        if year_text is None and medline_date:
            year_text = medline_date[:4]
        if year_text is None:
            return None

        year = int(year_text)
        month_text = pub_date.findtext("Month")
        day_text = pub_date.findtext("Day")
        month = self._parse_month(month_text)
        day = int(day_text) if day_text and day_text.isdigit() else 1
        return datetime(year, month, day, tzinfo=UTC)

    def _parse_month(self, month_text: str | None) -> int:
        if month_text is None:
            return 1
        if month_text.isdigit():
            return min(max(int(month_text), 1), 12)
        return MONTHS.get(month_text[:3].lower(), 1)
