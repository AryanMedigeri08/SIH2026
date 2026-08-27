"""
locations.py — REST API Router for LGD 6-Tier Administrative Location Hierarchy.
"""

from __future__ import annotations
from typing import Optional
from fastapi import APIRouter, Query, HTTPException

from app.database import db_manager
from app.models.schemas import StateInfo, DistrictInfo, BlockInfo, VillageInfo

router = APIRouter(prefix="/locations", tags=["LGD Location Hierarchy"])


@router.get("/states", response_model=list[StateInfo])
async def list_states():
    """Returns all 36 Indian States and Union Territories from LGD."""
    states_data = await db_manager.get_states()
    return [StateInfo(**s) for s in states_data]


@router.get("/districts", response_model=list[DistrictInfo])
async def list_districts(
    state_code: Optional[int] = Query(None, description="LGD State Code (e.g. 19 for WB, 29 for KA, 9 for UP)"),
    state_name: Optional[str] = Query(None, description="State Name (e.g. West Bengal, Karnataka)"),
):
    """Returns districts for a given state code or state name."""
    districts_data = await db_manager.get_districts(state_code=state_code, state_name=state_name)
    return [DistrictInfo(**d) for d in districts_data]


@router.get("/blocks", response_model=list[BlockInfo])
async def list_blocks(
    district_code: Optional[int] = Query(None, description="LGD District Code"),
    district_name: Optional[str] = Query(None, description="District Name"),
    state_name: Optional[str] = Query(None, description="Optional State Name"),
):
    """Returns development blocks for a given district code or district name."""
    blocks_data = await db_manager.get_blocks(district_code=district_code, district_name=district_name, state_name=state_name)
    return [BlockInfo(**b) for b in blocks_data]


@router.get("/villages", response_model=list[VillageInfo])
async def list_villages(
    district_code: Optional[int] = Query(None, description="LGD District Code"),
    block_code: Optional[int] = Query(None, description="Optional Development Block Code"),
    district_name: Optional[str] = Query(None, description="District Name"),
    block_name: Optional[str] = Query(None, description="Block Name"),
    search: Optional[str] = Query(None, description="Search query string"),
):
    """Returns villages for a given district, block code, or name."""
    villages_data = await db_manager.get_villages(
        district_code=district_code,
        block_code=block_code,
        district_name=district_name,
        block_name=block_name,
        search=search,
    )
    return [VillageInfo(**v) for v in villages_data]
