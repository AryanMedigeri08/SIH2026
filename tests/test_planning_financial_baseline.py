"""Frozen external evidence; all bank calculations run through the real pipeline.

These snapshots were captured at 77afa90 before adding the planning paths.
"""
import asyncio
import json
import sys
from contextlib import ExitStack, contextmanager
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend/app/core"))
from app.models.schemas import UserInput
from app.routers import feasibility
from amenities_client import VillageAmenitiesResult
from executive_synthesizer import ExecutiveSynthesis
from inference import ViabilityPrediction
from machinery_engine import extract_contextual_machinery


@contextmanager
def frozen_evidence():
    """No network, DB writes, paid model calls, or machine-specific ML model."""
    with ExitStack() as stack:
        for name, value in {
            "get_census_demographics": {"base_population_2011": 5000, "district_population_2011": 1500000},
            "get_district_msme_stats": {"total_msme": 1200},
            "get_state_cpi_inflation": 4.5,
            "get_weather_risk_score": 0.25,
        }.items():
            stack.enter_context(patch.object(feasibility.db_manager, name, AsyncMock(return_value=value)))
        stack.enter_context(patch.object(feasibility, "fetch_village_amenities", return_value=
            VillageAmenitiesResult(7, 20, True, True, True, False, "synthetic_test_fixture")))
        stack.enter_context(patch.object(feasibility, "predict_viability", return_value=
            ViabilityPrediction("SUITABLE", 80, {"SUITABLE": .8}, [], [], {}, True, "test")))
        stack.enter_context(patch.object(feasibility, "generate_executive_synthesis", return_value=
            ExecutiveSynthesis("Test evidence only", [], "Test", "en", False, True, 0, "test", "test")))
        stack.enter_context(patch.object(feasibility, "extract_contextual_machinery", side_effect=
            lambda **kw: extract_contextual_machinery(**{**kw, "use_ai": False})))
        yield


CASES = {
    "below_micro": {"project_cost": 139000},
    "micro_boundary": {"project_cost": 140000},
    "above_micro": {"project_cost": 141000},
    "general_owned": {"project_cost": 1000000, "premise_type": "owned"},
    "reserved_rented": {"project_cost": 1000000, "promoter_category": "sc", "monthly_rent": 4000},
    "female_general": {"project_cost": 1000000, "gender": "Female"},
    "explicit_zero": {"project_cost": 1000000, "available_margin_capital": 0},
    "unknown_cash": {"project_cost": 1000000, "available_margin_capital": None},
    "large_project": {"project_cost": 5001000},
}


def make_input(**overrides):
    return UserInput(**{
        "enterprise_name": "Test dairy", "state_name": "West Bengal", "district_name": "Bankura",
        "village_name": "Test village", "latitude": 23, "longitude": 87,
        "tenure_years": 7, "moratorium_months": 6, "available_margin_capital": 50000,
        **overrides,
    })


def baseline_results():
    with frozen_evidence():
        return {name: asyncio.run(feasibility._run_pipeline(make_input(**inputs)))[0].financial_analysis
                for name, inputs in CASES.items()}


def test_existing_financial_pipeline_matches_pre_planning_snapshot():
    expected = json.loads(Path(__file__).with_name("fixtures").joinpath("planning_financial_77afa90.json").read_text())
    assert baseline_results() == expected
