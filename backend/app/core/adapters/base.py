"""
base.py — Abstract Base Class for Government Dataset Adapters.

Document 2, Sections 17-20 & 59-61.

Every external dataset (Census, Mission Antyodaya, ODOP, etc.) must implement
this adapter contract. Every feature must have an identifiable source,
reference period/year, geographic join level, and documented limitations.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict, field
from typing import Optional, Any
from datetime import datetime, timezone


@dataclass
class DatasetMetadata:
    """Metadata describing a government data source per Section 60."""
    source_id: str
    dataset_name: str
    publisher: str
    url: str = ""
    coverage: str = "National"
    geographic_level: str = "village"  # village | subdistrict | district | state
    reference_period: str = ""         # e.g. "2011", "2019-2020", "2026-projected"
    license: str = "Open Government Data (OGD) License - India"
    last_verified: str = field(default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    schema_version: str = "1.0"
    notes: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


class GovernmentDatasetAdapter(ABC):
    """
    Abstract contract for government data ingestion and feature exposure.
    Section 59: Adapters decouple the intelligence engine from raw source providers.
    """

    @abstractmethod
    def metadata(self) -> DatasetMetadata:
        """Return provenance and lineage metadata."""
        pass

    @abstractmethod
    def fetch_features(
        self,
        state: str,
        district: str,
        village: str = "",
        pincode: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Fetch and return normalized features for the target location.
        Returns empty or graceful defaults if data is missing, setting
        data_available=False in the returned dictionary.
        """
        pass
