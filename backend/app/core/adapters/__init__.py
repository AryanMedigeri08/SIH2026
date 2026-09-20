"""
adapters — Government Dataset Ingestion & Lineage Subsystem.
"""

from .base import GovernmentDatasetAdapter, DatasetMetadata
from .registry import DATA_SOURCES, get_source_metadata, list_all_sources
from .population import PopulationAdapter
from .amenities import AmenitiesAdapter
from .odop import ODOPAdapter

__all__ = [
    "GovernmentDatasetAdapter",
    "DatasetMetadata",
    "DATA_SOURCES",
    "get_source_metadata",
    "list_all_sources",
    "PopulationAdapter",
    "AmenitiesAdapter",
    "ODOPAdapter",
]
