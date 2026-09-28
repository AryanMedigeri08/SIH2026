"""
odop.py — One District One Product (ODOP) Focus Registry Adapter.

Document 2, Sections 17-21 & 59.

Extracts official ODOP priority products for a given district, assesses
alignment between proposed business category and government priority sectors,
and exposes cluster/export advantages.
"""

from __future__ import annotations
import json
import logging
from pathlib import Path
from typing import Optional, Any

from .base import GovernmentDatasetAdapter, DatasetMetadata
from .registry import DATA_SOURCES

logger = logging.getLogger("udyam_saathi.adapters.odop")


class ODOPAdapter(GovernmentDatasetAdapter):
    """
    Adapter for Ministry of Commerce / DPIIT ODOP Focus Registry.
    """

    def __init__(self, registry_path: Optional[Path] = None):
        self._meta = DATA_SOURCES["ODOP_REGISTRY"]
        if registry_path is None:
            registry_path = Path(__file__).parent.parent.parent / "data" / "odop_registry.json"
        self.registry_path = registry_path
        self._data: dict = {}
        self._load_registry()

    def _load_registry(self) -> None:
        try:
            if self.registry_path.exists():
                with open(self.registry_path, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load ODOP registry from {self.registry_path}: {e}")
            self._data = {}

    def metadata(self) -> DatasetMetadata:
        return self._meta

    def fetch_features(
        self,
        state: str,
        district: str,
        village: str = "",
        pincode: Optional[str] = None,
        target_category: str = "",
    ) -> dict[str, Any]:
        """
        Check if district has an ODOP priority and whether target_category matches it.
        """
        states_dict = self._data.get("states", {})

        # Find matching state (case-insensitive)
        matched_state_data = None
        for s_key, dist_map in states_dict.items():
            if s_key.lower() == state.lower():
                matched_state_data = dist_map
                break

        district_entry = None
        if matched_state_data:
            for d_key, d_val in matched_state_data.items():
                if d_key.lower() == district.lower():
                    district_entry = d_val
                    break

        if not district_entry:
            return {
                "source_id": self._meta.source_id,
                "data_available": False,
                "data_year": "2022-2026",
                "odop_product": None,
                "secondary_product": None,
                "odop_category": None,
                "is_odop_aligned": False,
                "cfc_available": False,
                "key_benefits": [],
            }

        product = district_entry.get("odop_product") or ""
        category = district_entry.get("category") or ""
        matching_sectors = [s.upper() for s in district_entry.get("matching_sectors") or []]
        cfc = bool(district_entry.get("cfc_available"))
        benefits = district_entry.get("key_benefits") or []

        # Check alignment with target category
        is_aligned = False
        target_cat_upper = target_category.upper().strip()
        if target_cat_upper:
            if any(target_cat_upper in s or s in target_cat_upper for s in matching_sectors):
                is_aligned = True
            elif target_cat_upper in category.upper():
                is_aligned = True
            elif target_cat_upper in product.upper():
                is_aligned = True

        return {
            "source_id": self._meta.source_id,
            "data_available": True,
            "data_year": "2022-2026",
            "odop_product": product,
            "secondary_product": district_entry.get("secondary_product"),
            "odop_category": category,
            "is_odop_aligned": is_aligned,
            "cfc_available": cfc,
            "key_benefits": benefits,
        }
