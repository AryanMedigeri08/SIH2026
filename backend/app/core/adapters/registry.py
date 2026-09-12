"""
registry.py — Government Data Source Registry.

Document 2, Section 60.

Maintains an immutable, centralized catalog of official government datasets
used across the Udyam Saathi platform. Every demand and supply feature links
back to an entry in this registry.
"""

from __future__ import annotations
from typing import Optional
from .base import DatasetMetadata

DATA_SOURCES: dict[str, DatasetMetadata] = {
    "UDYAM_MSME": DatasetMetadata(
        source_id="UDYAM_MSME",
        dataset_name="List of MSME Registered Units under UDYAM",
        publisher="Ministry of Micro, Small and Medium Enterprises (MSME)",
        url="https://api.data.gov.in/resource/8b68ae56-84cf-4728-a0a6-1be11028dea7",
        coverage="National (36 States & UTs)",
        geographic_level="district_and_pincode",
        reference_period="2020-Present (Daily/Live OGD API)",
        license="Open Government Data (OGD) License - India",
        notes="Official registry of enterprises registered under the Udyam portal.",
    ),
    "CENSUS_2011_POPULATION": DatasetMetadata(
        source_id="CENSUS_2011_POPULATION",
        dataset_name="Primary Census Abstract (PCA) 2011",
        publisher="Office of the Registrar General & Census Commissioner, India (ORGI)",
        url="https://censusindia.gov.in/",
        coverage="National (640 Districts, 6.4L Villages)",
        geographic_level="village",
        reference_period="2011 (Projected to 2026 via State-specific CAGR)",
        license="Government of India Public Domain",
        notes="Base demographic population and household counts projected to current period.",
    ),
    "MISSION_ANTYODAYA": DatasetMetadata(
        source_id="MISSION_ANTYODAYA",
        dataset_name="Mission Antyodaya 613 Village Infrastructure & Amenities Dataset",
        publisher="Ministry of Rural Development (MoRD) / Data.gov.in",
        url="https://api.data.gov.in/resource/",
        coverage="National (613 Rural Districts, ~2.5L Gram Panchayats)",
        geographic_level="village_and_gram_panchayat",
        reference_period="2019-2020",
        license="Open Government Data (OGD) License - India",
        notes="Village-level indicators on power hours, paved road, banking, internet, and storage.",
    ),
    "ODOP_REGISTRY": DatasetMetadata(
        source_id="ODOP_REGISTRY",
        dataset_name="One District One Product (ODOP) Focus Registry",
        publisher="Department for Promotion of Industry and Internal Trade (DPIIT) & Ministry of Commerce",
        url="https://www.investindia.gov.in/one-district-one-product",
        coverage="765+ Districts Nationwide",
        geographic_level="district",
        reference_period="2022-2026",
        license="Government of India Initiative",
        notes="District-level priority and GI-tagged agricultural, craft, and manufacturing products.",
    ),
}


def get_source_metadata(source_id: str) -> Optional[DatasetMetadata]:
    """Retrieve metadata for a registered data source."""
    return DATA_SOURCES.get(source_id)


def list_all_sources() -> list[dict]:
    """Return all registered source metadata objects as dicts."""
    return [meta.to_dict() for meta in DATA_SOURCES.values()]
