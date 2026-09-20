"""
snapshot.py — Data Snapshotting & Analytical Reproducibility Subsystem.

Document 3, Sections 6 & 7 (Gates 3 & 4).

A live external API call is not a reproducible dataset.
This module provides:
    1. Immutable snapshotting of retrieved raw government records (SHA-256 hashed).
    2. Analysis run tracking pinning snapshot_id, engine_version, ontology_version,
       and geographic master version.
    3. Pinned replay: Same Snapshot + Same Parameters = Exactly Same Output.
"""

from __future__ import annotations
import json
import hashlib
import logging
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Any

logger = logging.getLogger("udyam_saathi.snapshot")

_DEFAULT_SNAPSHOT_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "snapshots"


def compute_sha256(data: Any) -> str:
    """Compute a deterministic SHA-256 hex digest for any JSON-serializable structure."""
    canonical_json = json.dumps(data, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


@dataclass
class DataSnapshot:
    """Immutable record snapshot per Document 3, Section 7."""
    snapshot_id: str
    source: str
    source_version: str
    retrieved_at: str
    query_parameters: dict[str, Any]
    response_hash: str
    record_count: int
    schema_hash: str
    records: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self, include_records: bool = True) -> dict[str, Any]:
        d = asdict(self)
        if not include_records:
            d["records"] = []
        return d


@dataclass
class AnalysisRun:
    """Audit lineage for an analytical run per Document 3, Section 7."""
    analysis_id: str
    snapshot_id: str
    engine_version: str = "2.0-deterministic"
    ontology_version: str = "2026.1"
    gazetteer_version: str = "2026.1-sqlite"
    demand_source_versions: dict[str, str] = field(default_factory=dict)
    parameters: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    result_hash: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class SnapshotStore:
    """Filesystem-backed persistent snapshot and run repository."""

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or _DEFAULT_SNAPSHOT_DIR
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def create_snapshot(
        self,
        source: str,
        query_parameters: dict[str, Any],
        records: list[dict[str, Any]],
        source_version: str = "1.0",
    ) -> DataSnapshot:
        """Create and hash an immutable DataSnapshot."""
        response_hash = compute_sha256(records)
        fields = sorted(list(records[0].keys())) if records else []
        schema_hash = compute_sha256(fields)
        now_iso = datetime.now(timezone.utc).isoformat()
        
        # Deterministic snapshot ID based on query and response hash
        snap_token = compute_sha256({"query": query_parameters, "resp_hash": response_hash})[:12]
        snapshot_id = f"SNAP-{snap_token.upper()}"

        snapshot = DataSnapshot(
            snapshot_id=snapshot_id,
            source=source,
            source_version=source_version,
            retrieved_at=now_iso,
            query_parameters=query_parameters,
            response_hash=response_hash,
            record_count=len(records),
            schema_hash=schema_hash,
            records=records,
        )
        self.save(snapshot)
        return snapshot

    def save(self, snapshot: DataSnapshot) -> Path:
        """Save snapshot to disk as JSON."""
        file_path = self.base_dir / f"{snapshot.snapshot_id}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(snapshot.to_dict(include_records=True), f, indent=2, default=str)
        logger.info(f"Saved snapshot {snapshot.snapshot_id} ({snapshot.record_count} records) to {file_path}")
        return file_path

    def load(self, snapshot_id: str) -> Optional[DataSnapshot]:
        """Load snapshot by ID."""
        file_path = self.base_dir / f"{snapshot_id}.json"
        if not file_path.exists():
            return None
        with open(file_path, "r", encoding="utf-8") as f:
            d = json.load(f)
        return DataSnapshot(**d)

    def list_snapshots(self) -> list[dict[str, Any]]:
        """List metadata for all available snapshots."""
        results = []
        for p in self.base_dir.glob("SNAP-*.json"):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                    meta.pop("records", None)
                    results.append(meta)
            except Exception as e:
                logger.warning(f"Error reading snapshot {p}: {e}")
        return results


# Global singleton snapshot store
snapshot_store = SnapshotStore()
