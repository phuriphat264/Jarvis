"""
Personalization API — Phase 17

Endpoints:
  GET    /profile                         — Current preference profile
  GET    /preferences                     — All active preferences
  POST   /preferences                     — Create explicit preference
  PATCH  /preferences/{id}                — Update preference value
  DELETE /preferences/{id}                — Archive preference
  GET    /suggestions                     — Pending candidates awaiting approval
  POST   /suggestions/{id}/approve        — Approve candidate → active preference
  POST   /suggestions/{id}/reject         — Reject candidate
  POST   /reset                           — Reset all BEHAVIOR-sourced preferences
  POST   /behavior                        — Record a behavior event (from frontend)
  POST   /feedback                        — Submit thumbs-up/down feedback
"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime, timezone

from app.database.session import get_db
from app.database.models.user import User
from app.database.models.personalization import (
    UserPreference, PreferenceCandidate, BehaviorEvent, PersonalizationFeedback
)
from app.personalization.preference_service import PreferenceService
from app.personalization.preference_extractor import PreferenceExtractor
from app.personalization.adaptation_engine import AdaptationEngine
from app.personalization.behavior_tracker import BehaviorTracker
from app.core.dependencies import get_current_user

logger = logging.getLogger("jarvis.api.personalization")
router = APIRouter()


# ── Profile ──────────────────────────────────────────────────────────────────

@router.get("/profile")
async def get_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    profile = await AdaptationEngine.get_profile(current_user.id, db)
    return {"success": True, "data": profile}


# ── Preferences ───────────────────────────────────────────────────────────────

@router.get("/preferences")
async def list_preferences(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    prefs = await PreferenceService.get_all(db, current_user.id)
    return {
        "success": True,
        "data": [
            {
                "id": p.id, "key": p.key, "value": p.value,
                "scope": p.scope, "source": p.source,
                "confidence": p.confidence, "priority": p.priority,
                "created_at": p.created_at.isoformat(),
            }
            for p in prefs
        ],
    }


@router.post("/preferences")
async def create_preference(
    payload: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    key = payload.get("key")
    value = payload.get("value")
    scope = payload.get("scope", "GLOBAL")
    scope_id = payload.get("scope_id")

    if not key or not value:
        raise HTTPException(status_code=400, detail="key and value are required")

    pref = await PreferenceService.create_explicit(db, current_user.id, key, value, scope, scope_id)
    return {"success": True, "data": {"id": pref.id, "key": pref.key, "value": pref.value}}


@router.patch("/preferences/{pref_id}")
async def update_preference(
    pref_id: int,
    payload: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    value = payload.get("value")
    if not value:
        raise HTTPException(status_code=400, detail="value is required")

    pref = await PreferenceService.update(db, current_user.id, pref_id, value)
    if not pref:
        raise HTTPException(status_code=404, detail="Preference not found")
    return {"success": True, "data": {"id": pref.id, "key": pref.key, "value": pref.value}}


@router.delete("/preferences/{pref_id}")
async def delete_preference(
    pref_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ok = await PreferenceService.delete(db, current_user.id, pref_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Preference not found")
    return {"success": True}


# ── Candidates / Suggestions ──────────────────────────────────────────────────

@router.get("/suggestions")
async def list_suggestions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Trigger extractor on demand so suggestions are fresh
    await PreferenceExtractor.run(db, current_user.id)

    res = await db.execute(
        select(PreferenceCandidate).where(
            PreferenceCandidate.user_id == current_user.id,
            PreferenceCandidate.status == "PENDING",
        ).order_by(PreferenceCandidate.confidence.desc())
    )
    candidates = res.scalars().all()
    return {
        "success": True,
        "data": [
            {
                "id": c.id, "key": c.key, "value": c.value,
                "confidence": c.confidence, "evidence_count": c.evidence_count,
                "created_at": c.created_at.isoformat(),
            }
            for c in candidates
        ],
    }


@router.post("/suggestions/{candidate_id}/approve")
async def approve_suggestion(
    candidate_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(
        select(PreferenceCandidate).where(
            PreferenceCandidate.id == candidate_id,
            PreferenceCandidate.user_id == current_user.id,
            PreferenceCandidate.status == "PENDING",
        )
    )
    candidate = res.scalars().first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    pref = await PreferenceService.create_from_candidate(
        db, current_user.id, candidate.key, candidate.value, candidate.confidence
    )
    candidate.status = "APPROVED"
    await db.commit()
    logger.info(f"Candidate {candidate_id} approved → preference {pref.id}")
    return {"success": True, "data": {"preference_id": pref.id}}


@router.post("/suggestions/{candidate_id}/reject")
async def reject_suggestion(
    candidate_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(
        select(PreferenceCandidate).where(
            PreferenceCandidate.id == candidate_id,
            PreferenceCandidate.user_id == current_user.id,
        )
    )
    candidate = res.scalars().first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    candidate.status = "REJECTED"
    await db.commit()
    return {"success": True}


# ── Reset ─────────────────────────────────────────────────────────────────────

@router.post("/reset")
async def reset_learned_preferences(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    count = await PreferenceService.reset_learned(db, current_user.id)
    logger.info(f"User {current_user.id} reset {count} learned preferences")
    return {"success": True, "data": {"archived_count": count}}


# ── Behavior Events (from frontend) ──────────────────────────────────────────

@router.post("/behavior")
async def record_behavior(
    payload: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    event_type = payload.get("event_type")
    if not event_type:
        raise HTTPException(status_code=400, detail="event_type is required")

    await BehaviorTracker.record(
        db=db,
        user_id=current_user.id,
        event_type=event_type,
        context=payload.get("context"),
        entity_type=payload.get("entity_type"),
        entity_id=payload.get("entity_id"),
        metadata=payload.get("metadata"),
    )
    return {"success": True}


# ── Feedback ──────────────────────────────────────────────────────────────────

@router.post("/feedback")
async def submit_feedback(
    payload: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    feedback_type = payload.get("feedback_type")
    if not feedback_type:
        raise HTTPException(status_code=400, detail="feedback_type is required")

    fb = PersonalizationFeedback(
        user_id=current_user.id,
        preference_id=payload.get("preference_id"),
        feedback_type=feedback_type,
        context=payload.get("context"),
    )
    db.add(fb)
    await db.commit()
    return {"success": True}
