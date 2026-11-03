"""Owner-authenticated, revision-checked Mira onboarding API."""
from __future__ import annotations

import hashlib
import json
import logging
import re
import time
import uuid
from datetime import datetime, timezone
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.auth_dependency import AuthenticatedUser, get_current_user
from app.database import db_manager
from app.models.onboarding import Turn, LocationSelection, GPSRequest, new_session
from app.models.schemas import ProjectCreate, ProjectModel
from app.core.onboarding import advance, apply_updates, invalidate, question, report_input, value
from app.core.onboarding_understanding import understand
from app.core.onboarding_location import OnboardingLocation, LocationUnavailable

router = APIRouter(prefix="/onboarding", tags=["Mira conversational onboarding"])
logger = logging.getLogger(__name__)


async def load(user):
    state = await db_manager.get_onboarding(user.uid)
    if state:
        return state
    profile = await db_manager.get_user(user.uid)
    if not profile:
        profile = await db_manager.upsert_user(user.uid, user.email or f"{user.uid}@udyam.gov.in", user.name or "")
    state = new_session(profile)
    await advance(state)
    await db_manager.save_onboarding(user.uid, state)
    return await db_manager.get_onboarding(user.uid)


def check_revision(state, revision):
    if revision != state["revision"]:
        raise HTTPException(409, "Your saved answers changed in another window. Reload the saved conversation; your unsent text is still here.")


def check_editable(state):
    if state.get("completed_project_id"):
        raise HTTPException(409, "This plan already has a saved report. Start another plan to collect new answers.")
    if time.time() - state.get("submission_started_at", 0) < 300:
        raise HTTPException(409, "Your report is being generated. Give it a moment, then reload your saved conversation.")


def apply_valid_answers(state, updates, source, correction=False):
    try:
        apply_updates(state, updates, source, correction=correction)
    except ValueError:
        raise HTTPException(422, "I couldn’t use those answers. Check the wording and amounts. If you entered setup costs, their total must be positive.")


async def save(user, state, revision):
    state["revision"] = revision + 1
    state["updated_at"] = datetime.now(timezone.utc).isoformat()
    try:
        saved = await db_manager.save_onboarding(user.uid, state, revision)
    except Exception as exc:
        logger.warning("Onboarding save failed (%s)", type(exc).__name__)
        raise HTTPException(503, "I couldn’t save this answer. Your last saved answers are safe; retry this answer when connected.") from exc
    if not saved:
        raise HTTPException(409, "Another answer was saved first. Reload your conversation and try again.")
    return state


async def response(state, language="en", reply=None):
    # Translated presentation never replaces canonical state or financial amounts.
    text = reply or state["next"]["text"]
    if language != "en":
        try:
            from app.core.translation_service import TranslationService
            translated = await TranslationService.get_instance().translate_text(text, language)
            text = translated.get("translated_text") or text
        except Exception:
            pass
    return {"state": state, "reply": text, "language": language}


@router.get("/session")
async def get_session(language: str = Query("en", pattern="^(en|hi|mr|ta|te|kn)$"), user: AuthenticatedUser = Depends(get_current_user)):
    return await response(await load(user), language)


@router.post("/turn")
async def turn(turn: Turn, user: AuthenticatedUser = Depends(get_current_user)):
    state = await load(user)
    if turn.request_id in state.get("processed_requests", []):
        return await response(state, turn.language)
    check_revision(state, turn.revision)
    check_editable(state)
    profile_before = {k: value(state, k) for k in ("name", "gender", "promoter_category")}
    text = turn.text.strip()
    action = turn.action
    current = state["next"]["field"]
    lower = text.lower().strip(" .?!।")
    controls = {"repeat": "repeat", "say that again": "repeat", "please repeat": "repeat", "explain": "explain",
                "what does that mean": "explain", "pause": "pause", "resume": "resume", "suggest names": "suggest_names",
                "alternatives": "alternatives", "reject all": "alternatives"}
    controls.update({"दोहराएं": "repeat", "पुन्हा सांगा": "repeat", "மீண்டும் சொல்லுங்கள்": "repeat", "మళ్ళీ చెప్పండి": "repeat", "ಮತ್ತೆ ಹೇಳಿ": "repeat",
        "रुकें": "pause", "थांबा": "pause", "நிறுத்து": "pause", "ఆపు": "pause", "ನಿಲ್ಲಿಸಿ": "pause",
        "जारी रखें": "resume", "पुढे सुरू करा": "resume", "தொடரவும்": "resume", "కొనసాగించండి": "resume", "ಮುಂದುವರಿಸಿ": "resume",
        "change my location": "change_location", "change business location": "change_location"})
    if action == "answer" and lower in controls:
        action = controls[lower]
    if action == "answer" and lower in ("yes", "correct", "confirm", "that's right", "हाँ", "हां", "हो", "ஆம்", "అవును", "ಹೌದು"):
        action = {"location_confirmation": "confirm_location", "business_confirmation": "confirm_business", "pending_changes": "confirm_change"}.get(current, action)
    if action == "answer" and lower in ("no", "incorrect", "नहीं", "नाही", "இல்லை", "కాదు", "ಇಲ್ಲ") and current == "location_confirmation":
        action = "change_location"
    elif action == "answer" and lower in ("no", "keep the old answer", "नहीं", "नाही", "இல்லை", "కాదు", "ಇಲ್ಲ") and current == "pending_changes":
        action = "discard_change"
    reply = None
    if action == "repeat":
        return await response(state, turn.language)
    if action == "explain":
        return await response(state, turn.language, state["next"].get("explanation") or "You can answer in your own words, use a choice below, or correct an earlier answer. " + state["next"]["text"])
    if action == "pause":
        state["paused"] = True
    elif action == "resume":
        state["paused"] = False
    elif state["paused"]:
        return await response(state, turn.language)
    elif action == "confirm_change":
        changes = dict(state["pending_changes"])
        state["pending_changes"] = {}
        apply_valid_answers(state, changes, turn.source, correction=True)
    elif action == "discard_change":
        state["pending_changes"] = {}
    elif action == "change_location":
        invalidate(state, {"location"})
        state["location"] = None
        state["location_confirmed"] = False
    elif action == "confirm_location":
        if not state["location"] or state["location"].get("is_rural") is None:
            raise HTTPException(422, "Please verify the business location and area classification first.")
        state["location_confirmed"] = True
    elif action == "confirm_business":
        if not state["classification"] or not all(value(state, k) for k in ("products", "activity", "operations", "scale")):
            raise HTTPException(422, "Please clarify the activity, products, requirements and capacity first.")
        state["business_confirmed"] = True
    elif action == "alternatives":
        state["rejected"] = list(set(state["rejected"] + [r["id"] for r in state["recommendations"]]))
        apply_valid_answers(state, {"idea_status": "explore"}, turn.source, correction=True)
    elif action == "suggest_names":
        product = value(state, "products", "Enterprise").split(",")[0].title()
        reply = f"Some names to consider: Saathi {product}, Pragati {product}, or Navjeevan {product}. Tell me which name you want, or give your own. I haven’t selected one."
    elif turn.recommendation_id or (current == "recommendations" and re.fullmatch(r"(?:option |idea |recommendation )?[123]|first|second|third", lower)):
        match = re.search(r"[123]", lower)
        index = int(match[0]) - 1 if match else {"first": 0, "second": 1, "third": 2}.get(lower, -1)
        selected = next((r for r in state["recommendations"] if r["id"] == turn.recommendation_id), None) if turn.recommendation_id else (state["recommendations"][index] if 0 <= index < len(state["recommendations"]) else None)
        if not selected:
            raise HTTPException(422, "That recommendation has changed. Please choose from the current list.")
        apply_valid_answers(state, {"idea": selected["idea"], "idea_status": "known"}, turn.source, correction=True)
    else:
        state.pop("language_ambiguities", None)
        if turn.updates:
            updates = turn.updates.model_dump(exclude_none=True)
            ambiguities, model = [], "structured_control"
        elif text:
            updates, ambiguities, model = await understand(text, state)
        else:
            updates, ambiguities, model = {}, [], "local"
        if current == "odop_explore" and updates.get("odop_preference") in ("keep", "reject"):
            state["odop_explained"] = True
        apply_valid_answers(state, updates, turn.source, correction=turn.correction)
        state["understanding_source"] = model
        if ambiguities:
            # Essential missing facts remain missing; clarification cannot override a prerequisite.
            state["language_ambiguities"] = ambiguities
        if text and not updates:
            reply = "I haven’t changed your answers because I’m not sure I understood. " + state["next"]["text"]
    await advance(state)
    if text or turn.updates:
        # Authentication credentials are never sent to this endpoint. Do not echo profile demographics into the transcript.
        profile_turn = current in ("name", "gender", "promoter_category") or bool(re.search(r"\bmy (?:caste|gender|name)\b", text, re.I))
        state["history"].append({"role": "user", "text": "Profile detail updated" if profile_turn else text or "Answer selected", "source": turn.source})
    state["history"].append({"role": "assistant", "text": reply or state["next"]["text"]})
    state["history"] = state["history"][-80:]
    state["processed_requests"] = (state["processed_requests"] + [turn.request_id])[-80:]
    await save(user, state, turn.revision)
    # Reuse the authenticated profile store; known fields seed future onboarding sessions.
    profile_changes = {k: value(state, k) for k, previous in profile_before.items() if value(state, k) is not None and value(state, k) != previous}
    if profile_changes:
        await db_manager.update_user(user.uid, profile_changes)
    return await response(state, turn.language, reply)


@router.get("/locations/{level}")
async def location_options(level: str, parent: int | None = None, search: str = Query("", max_length=100), user: AuthenticatedUser = Depends(get_current_user)):
    try:
        return await OnboardingLocation(db_manager).options(level, parent, search)
    except LocationUnavailable as exc:
        raise HTTPException(503, str(exc))
    except ValueError as exc:
        raise HTTPException(422, str(exc))
    except Exception as exc:
        raise HTTPException(503, "The official location directory is temporarily unavailable. Your progress is saved; please retry.") from exc


@router.put("/location")
async def choose_location(selection: LocationSelection, user: AuthenticatedUser = Depends(get_current_user)):
    state = await load(user)
    check_revision(state, selection.revision)
    check_editable(state)
    try:
        loc = await OnboardingLocation(db_manager).select(selection)
    except LocationUnavailable as exc:
        raise HTTPException(503, str(exc))
    except ValueError as exc:
        raise HTTPException(422, str(exc))
    except Exception as exc:
        raise HTTPException(503, "I couldn’t verify that location just now. Your answers are saved; please retry.") from exc
    invalidate(state, {"location"})
    state.update(location=loc, location_confirmed=False)
    await advance(state)
    await save(user, state, selection.revision)
    return await response(state, selection.language)


@router.post("/location/detect")
async def detect_location(gps: GPSRequest, user: AuthenticatedUser = Depends(get_current_user)):
    state = await load(user)
    check_revision(state, gps.revision)
    check_editable(state)
    try:
        physical, candidate = await OnboardingLocation(db_manager).detect(gps)
    except ValueError as exc:
        raise HTTPException(422, str(exc))
    except Exception:
        raise HTTPException(503, "I couldn’t verify the GPS address. Try again or choose your business location below.")
    state["physical_location"] = physical
    if candidate:
        invalidate(state, {"location"})
        state.update(location=candidate, location_confirmed=False)
    await advance(state)
    await save(user, state, gps.revision)
    return await response(state, gps.language, reply=None if candidate else "I found your current position but could not verify a unique LGD village and development block. Please choose the intended business location below.")


class Revision(BaseModel):
    revision: int = Field(..., ge=0)


class Complete(Revision):
    language: Literal["en", "hi", "mr", "ta", "te", "kn"] = "en"


@router.post("/report-input")
async def get_report_input(command: Revision, user: AuthenticatedUser = Depends(get_current_user)):
    state = await load(user)
    check_revision(state, command.revision)
    try:
        return report_input(state)
    except ValueError as exc:
        raise HTTPException(422, str(exc))


@router.post("/new-session")
async def restart(command: Revision, user: AuthenticatedUser = Depends(get_current_user)):
    old = await load(user)
    check_revision(old, command.revision)
    if time.time() - old.get("submission_started_at", 0) < 300:
        raise HTTPException(409, "Wait for the current report to finish first.")
    state = new_session(await db_manager.get_user(user.uid) or {})
    for key in ("name", "gender", "promoter_category"):
        if key in old["fields"]:
            state["fields"][key] = old["fields"][key]
    state["location"] = old["location"]
    state["location_confirmed"] = False
    await advance(state)
    await save(user, state, command.revision)
    return await response(state)


@router.post("/complete", response_model=ProjectModel)
async def complete(command: Complete, user: AuthenticatedUser = Depends(get_current_user)):
    """Only server-validated, current facts may create the report. Retries reuse its project ID."""
    state = await load(user)
    if state.get("completed_project_id"):
        saved = await db_manager.get_project(state["completed_project_id"])
        if saved and saved["user_id"] == user.uid:
            return ProjectModel(**saved)
        raise HTTPException(409, "The saved report was removed. Start another plan to continue.")
    check_revision(state, command.revision)
    check_editable(state)
    try:
        inputs = report_input(state, command.language)
        project = ProjectCreate(**inputs, business_name=inputs["enterprise_name"], investment_amount=inputs["project_cost"])
    except ValueError:
        raise HTTPException(422, "Finish confirming the current business, location and costs before generating the report.")

    fingerprint = hashlib.sha256(json.dumps(inputs, sort_keys=True).encode()).hexdigest()
    project_id = state.get("submission_project_id") if state.get("submission_fingerprint") == fingerprint else None
    project_id = project_id or f"proj_{uuid.uuid4().hex}"
    state.update(submission_project_id=project_id, submission_fingerprint=fingerprint, submission_started_at=time.time())
    await save(user, state, command.revision)
    claimed_revision = state["revision"]
    try:
        from app.routers.projects import analyze_new_project
        saved = await db_manager.get_project(project_id)
        if saved and saved["user_id"] != user.uid:
            raise HTTPException(409, "The project could not be safely resumed.")
        completed = ProjectModel(**saved) if saved and saved.get("analysis_result") else await analyze_new_project(project, user, project_id=project_id)
    except Exception as exc:
        logger.warning("Onboarding report could not finish (%s)", type(exc).__name__)
        state.pop("submission_started_at", None)
        await save(user, state, claimed_revision)
        raise HTTPException(503, "The report could not finish. Your confirmed answers are saved. Reload your plan and try again.") from exc
    state.pop("submission_started_at", None)
    state["completed_project_id"] = completed.project_id
    state["next"] = question("complete", "Your report is saved. You can open it from your business plan or start another plan.")
    await save(user, state, claimed_revision)
    return completed
