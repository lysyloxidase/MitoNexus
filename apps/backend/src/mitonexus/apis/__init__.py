"""External API client package."""

from mitonexus.apis.base import BaseAPIClient
from mitonexus.apis.biorxiv import BioRxivClient
from mitonexus.apis.clinicaltrials import ClinicalTrialsClient
from mitonexus.apis.europe_pmc import EuropePMCClient
from mitonexus.apis.pubmed import PubMedClient
from mitonexus.apis.semantic_scholar import SemanticScholarClient

__all__ = [
    "BaseAPIClient",
    "BioRxivClient",
    "ClinicalTrialsClient",
    "EuropePMCClient",
    "PubMedClient",
    "SemanticScholarClient",
]
