"""AI Coach API — chat, session management, usage tracking."""
from __future__ import annotations

import json
import logging
import time
import uuid
from datetime import UTC, date, datetime, timedelta

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    Query,
    Request,
    UploadFile,
    status,
)
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, ConfigDict
from sqlalchemy import desc, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.authentication import get_current_user
from app.core.config import get_settings
from app.core.middleware import get_request_id
from app.db.dependencies import get_db_session
from app.models.ai_coach import AIUsageTracker, ChatMessage, ChatSession
from app.models.body_weight import BodyWeight
from app.models.enums import ChatRole, GoalStatus
from app.models.goal import Goal
from app.models.nutrition_log import NutritionLog
from app.models.nutrition_profile import NutritionProfile
from app.models.user import User
from app.services.ai_coach import get_ai_coach_service
from app.services.food_recognition import FoodRecognitionService
from app.services.memory_retriever import get_memory_retriever

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ai-coach", tags=["AI Coach"])

DAILY_MESSAGE_LIMIT = 25
DAILY_IMAGE_LIMIT = 5


# ── Pydantic schemas ──────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    session_id: uuid.UUID | None = None
    stream: bool = False


class ChatMessageFeedbackRequest(BaseModel):
    is_helpful: bool | None = None
    is_not_helpful: bool | None = None
    was_copied: bool | None = None
    was_regenerated: bool | None = None

class ChatSessionCreate(BaseModel):
    title: str


class ChatSessionUpdate(BaseModel):
    title: str | None = None
    pinned: bool | None = None
    archived: bool | None = None


class ChatSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    title: str
    pinned: bool
    archived: bool
    message_count: int
    last_active_at: datetime | None
    created_at: datetime
    updated_at: datetime


class ChatMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    role: str
    content: str
    model_used: str | None
    response_time_ms: int | None
    is_helpful: bool | None
    is_not_helpful: bool | None
    was_regenerated: bool
    was_copied: bool
    created_at: datetime


class AIUsageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    messages_used: int
    images_used: int
    meal_plans_used: int
    tokens_used: int
    usage_date: date
    messages_limit: int = DAILY_MESSAGE_LIMIT
    images_limit: int = DAILY_IMAGE_LIMIT
    reset_at: str  # ISO timestamp of next midnight UTC


class AIUsageHistoryEntry(BaseModel):
    usage_date: date
    messages_used: int
    images_used: int


class AIUsageHistoryResponse(BaseModel):
    entries: list[AIUsageHistoryEntry]
    total_messages: int
    total_sessions: int
    avg_response_time_ms: float | None


# ── Helpers ───────────────────────────────────────────────────────────────────

def _next_reset_utc() -> str:
    """ISO timestamp of next UTC midnight."""
    now = datetime.now(UTC)
    tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    return tomorrow.isoformat()


async def _upsert_usage_tracker(
    user_id: uuid.UUID,
    session: AsyncSession,
    *,
    messages_delta: int = 0,
    images_delta: int = 0,
) -> AIUsageTracker:
    """Atomically upsert today's usage row using ON CONFLICT DO UPDATE.
    This is the auto-daily-reset mechanism: a new row is created each day,
    so yesterday's counts are automatically left behind."""
    today = date.today()
    stmt = (
        pg_insert(AIUsageTracker)
        .values(
            user_id=user_id,
            usage_date=today,
            messages_used=messages_delta,
            images_used=0,
            meal_plans_used=0,
            tokens_used=0,
        )
        .on_conflict_do_update(
            constraint="uq_ai_usage_user_date",
            set_={
                "messages_used": AIUsageTracker.messages_used + messages_delta,
                "images_used": AIUsageTracker.images_used + images_delta,
                "updated_at": func.now(),
            },
        )
        .returning(AIUsageTracker)
    )
    result = await session.execute(stmt)
    await session.flush()
    row = result.scalars().first()
    if row is None:
        # Fallback for non-PostgreSQL (tests with SQLite)
        sel = select(AIUsageTracker).where(
            AIUsageTracker.user_id == user_id,
            AIUsageTracker.usage_date == today,
        )
        row = (await session.execute(sel)).scalars().first()
        if row is None:
            row = AIUsageTracker(
                user_id=user_id,
                usage_date=today,
                messages_used=messages_delta,
                images_used=0,
                meal_plans_used=0,
                tokens_used=0,
            )
            session.add(row)
            await session.flush()
    return row

async def _extract_memory_background(user_id: uuid.UUID, message: str, ai_response: str) -> None:
    """Background task to extract facts from user message and store them in AIUserMemory."""
    try:
        service = get_ai_coach_service()

        prompt = f"""Analyze the following message from a user to their AI nutrition coach.
If the user mentions any long-term facts about themselves (e.g. allergies, preferences, medical conditions, diet type, goals, habits), extract them.
Ignore transient statements like "I ate an apple today". Focus on persistent facts like "I am vegan" or "I am allergic to peanuts".
Return a JSON array of objects with keys: memory_type (string), content (string). If nothing, return empty array [].
User Message: {message}"""

        # Use simple text generation for extraction
        response = await service.chat(prompt, context=None)

        # Parse JSON
        start_idx = response.find('[')
        end_idx = response.rfind(']')
        if start_idx != -1 and end_idx != -1:
            json_str = response[start_idx:end_idx + 1]
            memories = json.loads(json_str)

            if memories:
                from app.db.session import db_manager
                from app.models.ai_coach import AIUserMemory
                async with db_manager.session_factory() as session:
                    for mem in memories:
                        content = mem.get("content")
                        mtype = mem.get("memory_type", "fact")
                        if content:
                            embedding = await service.generate_embedding(content)
                            new_mem = AIUserMemory(
                                user_id=user_id,
                                memory_type=mtype,
                                content=content,
                                embedding=embedding if embedding else None,
                                importance_score=1.0,
                                confidence=1.0,
                            )
                            session.add(new_mem)
                    await session.commit()
    except Exception as e:
        logger.error(f"Failed to extract memory: {e}")

async def _build_user_context(user_id: uuid.UUID, session: AsyncSession, current_message: str) -> str:
    """Build a rich, personalised context string injected into every AI prompt.

    Covers: profile biometrics, computed age, active goal + macros,
    recent body-weight trend, today's nutrition intake, allergies,
    dietary preference, and medical conditions, plus semantic memories.
    """
    lines: list[str] = []

    # ── System Prompt & Context Layering ──────────────────────────────────
    lines.append("## Context Layers")

    # ── Nutrition profile ─────────────────────────────────────────────────
    profile: NutritionProfile | None = (
        await session.execute(
            select(NutritionProfile).where(NutritionProfile.user_id == user_id)
        )
    ).scalars().first()

    if profile:
        # Compute age from date_of_birth
        age_str = "unknown"
        if profile.date_of_birth:
            today = date.today()
            age = today.year - profile.date_of_birth.year - (
                (today.month, today.day) < (profile.date_of_birth.month, profile.date_of_birth.day)
            )
            age_str = str(age)

        gender = profile.biological_sex.value if profile.biological_sex else "unknown"
        lines.append(
            f"User profile: age {age_str}, gender {gender}, "
            f"height {profile.height_cm or 'unknown'} cm, "
            f"weight {profile.weight_kg or 'unknown'} kg."
        )
        if profile.fitness_goal:
            lines.append(f"Fitness goal: {profile.fitness_goal.value}.")
        if profile.activity_level:
            lines.append(f"Activity level: {profile.activity_level.value}.")
        if profile.dietary_preference:
            lines.append(f"Dietary preference: {profile.dietary_preference.value}.")
        if profile.allergies:
            lines.append(f"Allergies/intolerances: {', '.join(profile.allergies)}.")
        if profile.medical_conditions:
            lines.append(f"Medical conditions (for context, not for diagnosis): {', '.join(profile.medical_conditions)}.")
        if profile.daily_calorie_goal:
            lines.append(f"Daily calorie goal: {profile.daily_calorie_goal} kcal.")
        if profile.daily_protein_goal_g:
            lines.append(f"Daily protein goal: {profile.daily_protein_goal_g} g.")
        if profile.water_goal_ml:
            lines.append(f"Daily water goal: {profile.water_goal_ml} ml.")

    # ── Active goal ────────────────────────────────────────────────────────
    active_goal: Goal | None = (
        await session.execute(
            select(Goal).where(
                Goal.user_id == user_id,
                Goal.status == GoalStatus.ACTIVE,
            ).order_by(desc(Goal.created_at))
        )
    ).scalars().first()

    if active_goal:
        lines.append(
            f"Active goal: {active_goal.goal_type.value} — {active_goal.title}."
        )
        if active_goal.target_calories:
            lines.append(f"Target: {active_goal.target_calories} kcal/day.")
        macro_parts = []
        if active_goal.target_protein_g:
            macro_parts.append(f"{active_goal.target_protein_g}g protein")
        if active_goal.target_carbs_g:
            macro_parts.append(f"{active_goal.target_carbs_g}g carbs")
        if active_goal.target_fats_g:
            macro_parts.append(f"{active_goal.target_fats_g}g fat")
        if macro_parts:
            lines.append(f"Macro targets: {', '.join(macro_parts)}.")
        if active_goal.end_date:
            lines.append(f"Goal deadline: {active_goal.end_date}.")

    # ── Body weight history (last 10 entries) ─────────────────────────────
    weight_rows = (
        await session.execute(
            select(BodyWeight)
            .where(BodyWeight.user_id == user_id)
            .order_by(desc(BodyWeight.logged_date))
            .limit(10)
        )
    ).scalars().all()

    if weight_rows:
        latest = weight_rows[0]
        lines.append(f"Latest recorded weight: {latest.weight_kg} kg on {latest.logged_date}.")
        if len(weight_rows) >= 2:
            oldest = weight_rows[-1]
            delta = float(latest.weight_kg) - float(oldest.weight_kg)
            direction = "gained" if delta > 0 else "lost"
            lines.append(
                f"Weight trend ({oldest.logged_date} → {latest.logged_date}): "
                f"{direction} {abs(delta):.1f} kg."
            )

    # ── Today's nutrition intake ───────────────────────────────────────────
    today = date.today()
    today_logs = (
        await session.execute(
            select(NutritionLog).where(
                NutritionLog.user_id == user_id,
                NutritionLog.logged_date == today,
            )
        )
    ).scalars().all()

    total_kcal = 0
    total_protein = 0
    if today_logs:
        total_kcal = sum(float(l.calories_kcal) for l in today_logs)
        total_protein = sum(float(l.protein_g) for l in today_logs)
        total_carbs = sum(float(l.carbohydrate_g) for l in today_logs)
        total_fat = sum(float(l.fat_g) for l in today_logs)
        meals_logged = {l.meal_type.value for l in today_logs}
        lines.append(
            f"Today's intake so far: {total_kcal:.0f} kcal, "
            f"{total_protein:.1f}g protein, {total_carbs:.1f}g carbs, {total_fat:.1f}g fat. "
            f"Meals logged: {', '.join(sorted(meals_logged))}."
        )
    else:
        lines.append("Today's intake: no meals logged yet.")

    # ── Proactive Coaching ──────────────────────────────────────────────────
    coaching_tips = []
    current_hour = datetime.now().hour
    if active_goal:
        if active_goal.target_calories and total_kcal < active_goal.target_calories * 0.3 and current_hour >= 14:
            coaching_tips.append("User is significantly under calorie target for this time of day (missing meals?). Suggest a nutrient-dense snack.")
        if active_goal.target_protein_g and total_protein < active_goal.target_protein_g * 0.4 and current_hour >= 16:
            coaching_tips.append("User is behind on protein intake for the day. Recommend high-protein options.")

    if coaching_tips:
        lines.append("\n## Proactive Coaching Triggers (Address these naturally):")
        for tip in coaching_tips:
            lines.append(f"- {tip}")

    # ── 7-day nutrition summary ────────────────────────────────────────────
    week_ago = today - timedelta(days=7)
    week_logs = (
        await session.execute(
            select(NutritionLog).where(
                NutritionLog.user_id == user_id,
                NutritionLog.logged_date >= week_ago,
                NutritionLog.logged_date < today,
            )
        )
    ).scalars().all()

    if week_logs:
        daily_cals: dict[date, float] = {}
        for l in week_logs:
            daily_cals[l.logged_date] = daily_cals.get(l.logged_date, 0) + float(l.calories_kcal)
        avg_kcal = sum(daily_cals.values()) / len(daily_cals)
        lines.append(f"Average daily calories last 7 days: {avg_kcal:.0f} kcal ({len(daily_cals)} days logged).")

    # ── Recent cross-session memory ─────────────────────────────────────────
    recent_advice = (
        await session.execute(
            select(ChatMessage.content)
            .join(ChatSession, ChatMessage.session_id == ChatSession.id)
            .where(
                ChatSession.user_id == user_id,
                ChatMessage.role == ChatRole.ASSISTANT
            )
            .order_by(desc(ChatMessage.created_at))
            .limit(3)
        )
    ).scalars().all()

    if recent_advice:
        lines.append("\n## Recent Conversation Summary (avoid repeating exactly):")
        for idx, advice in enumerate(recent_advice):
            # truncate to 150 chars to save tokens
            lines.append(f"- {advice[:150]}...")

    # ── Top Semantic Memories ────────────────────────────────────────────────
    settings = get_settings()
    service = get_ai_coach_service()
    query_emb = await service.generate_embedding(current_message)
    if query_emb:
        retriever = get_memory_retriever(use_pgvector=False) # Fallback to Python if unsure
        top_memories = await retriever.retrieve_top_k(session, user_id, query_emb, k=5)

        if top_memories:
            lines.append("\n## Top Semantic Memories (User Facts):")
            for mem in top_memories:
                lines.append(f"- {mem.content} (Confidence: {mem.confidence:.1f})")

                # Increment usage asynchronously or quickly here
                mem.usage_count += 1
                mem.last_used_at = datetime.now(UTC)
            
            await session.commit()

    return "\n".join(lines) if lines else ""


# ── Session endpoints ─────────────────────────────────────────────────────────

@router.get("/sessions", response_model=list[ChatSessionResponse])
async def get_sessions(
    search: str | None = Query(None, description="Filter sessions by title"),
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """List all chat sessions, sorted by latest activity. Optionally filter by title."""
    stmt = (
        select(ChatSession)
        .where(ChatSession.user_id == current_user.id)
        .order_by(
            desc(ChatSession.pinned),
            desc(ChatSession.last_active_at).nullslast(),
            desc(ChatSession.updated_at),
        )
    )
    if search and search.strip():
        stmt = stmt.where(ChatSession.title.ilike(f"%{search.strip()}%"))

    result = await session.execute(stmt)
    return result.scalars().all()


@router.post("/sessions", response_model=ChatSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    body: ChatSessionCreate,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    chat_session = ChatSession(
        user_id=current_user.id,
        title=body.title.strip() or "New Conversation",
        message_count=0,
    )
    session.add(chat_session)
    await session.commit()
    await session.refresh(chat_session)
    return chat_session


@router.put("/sessions/{session_id}", response_model=ChatSessionResponse)
async def update_session(
    session_id: uuid.UUID,
    body: ChatSessionUpdate,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    stmt = select(ChatSession).where(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id,
    )
    chat_session = (await session.execute(stmt)).scalars().first()
    if not chat_session:
        raise HTTPException(status_code=404, detail="Session not found")

    if body.title is not None:
        chat_session.title = body.title.strip() or "New Conversation"
    if body.pinned is not None:
        chat_session.pinned = body.pinned
    if body.archived is not None:
        chat_session.archived = body.archived

    await session.commit()
    await session.refresh(chat_session)
    return chat_session


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    stmt = select(ChatSession).where(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id,
    )
    chat_session = (await session.execute(stmt)).scalars().first()
    if not chat_session:
        raise HTTPException(status_code=404, detail="Session not found")

    await session.delete(chat_session)
    await session.commit()
    return {"success": True, "message": "Session deleted."}


@router.get("/sessions/{session_id}/messages", response_model=list[ChatMessageResponse])
async def get_session_messages(
    session_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    ownership = (
        await session.execute(
            select(ChatSession).where(
                ChatSession.id == session_id,
                ChatSession.user_id == current_user.id,
            )
        )
    ).scalars().first()
    if not ownership:
        raise HTTPException(status_code=404, detail="Session not found")

    messages = (
        await session.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at)
        )
    ).scalars().all()
    return messages


@router.post("/sessions/{session_id}/messages/{message_id}/feedback", response_model=ChatMessageResponse)
async def submit_message_feedback(
    session_id: uuid.UUID,
    message_id: uuid.UUID,
    body: ChatMessageFeedbackRequest,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    # Verify session ownership
    ownership = (
        await session.execute(
            select(ChatSession).where(
                ChatSession.id == session_id,
                ChatSession.user_id == current_user.id,
            )
        )
    ).scalars().first()
    if not ownership:
        raise HTTPException(status_code=404, detail="Session not found")

    msg = (
        await session.execute(
            select(ChatMessage).where(
                ChatMessage.id == message_id,
                ChatMessage.session_id == session_id
            )
        )
    ).scalars().first()
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")

    if body.is_helpful is not None:
        msg.is_helpful = body.is_helpful
    if body.is_not_helpful is not None:
        msg.is_not_helpful = body.is_not_helpful
    if body.was_copied is not None:
        msg.was_copied = body.was_copied
    if body.was_regenerated is not None:
        msg.was_regenerated = body.was_regenerated

    await session.commit()
    await session.refresh(msg)
    return msg

# ── Usage endpoints ───────────────────────────────────────────────────────────

@router.get("/usage", response_model=AIUsageResponse)
async def get_usage(
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Return today's usage. A fresh row (counts = 0) is created if none exists,
    implementing the automatic daily reset."""
    tracker = await _upsert_usage_tracker(current_user.id, session, messages_delta=0)
    await session.commit()
    return AIUsageResponse(
        messages_used=tracker.messages_used,
        images_used=tracker.images_used,
        meal_plans_used=tracker.meal_plans_used,
        tokens_used=tracker.tokens_used,
        usage_date=tracker.usage_date,
        messages_limit=DAILY_MESSAGE_LIMIT,
        images_limit=DAILY_IMAGE_LIMIT,
        reset_at=_next_reset_utc(),
    )


@router.get("/usage/history", response_model=AIUsageHistoryResponse)
async def get_usage_history(
    period: str = Query("7d", description="today | yesterday | 7d | 30d | all"),
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Return AI usage history for the requested period plus aggregate stats."""
    today = date.today()

    if period == "today":
        start_date = today
    elif period == "yesterday":
        start_date = today - timedelta(days=1)
        today = start_date  # narrow range to exactly yesterday
    elif period == "7d":
        start_date = today - timedelta(days=6)
    elif period == "30d":
        start_date = today - timedelta(days=29)
    else:  # "all"
        start_date = date(2000, 1, 1)

    usage_stmt = (
        select(AIUsageTracker)
        .where(
            AIUsageTracker.user_id == current_user.id,
            AIUsageTracker.usage_date >= start_date,
            AIUsageTracker.usage_date <= today,
        )
        .order_by(desc(AIUsageTracker.usage_date))
    )
    rows = (await session.execute(usage_stmt)).scalars().all()

    # Total sessions count
    session_count_result = await session.execute(
        select(func.count(ChatSession.id)).where(ChatSession.user_id == current_user.id)
    )
    total_sessions = session_count_result.scalar() or 0

    # Average assistant response time
    avg_rt_result = await session.execute(
        select(func.avg(ChatMessage.response_time_ms)).where(
            ChatMessage.session_id.in_(
                select(ChatSession.id).where(ChatSession.user_id == current_user.id)
            ),
            ChatMessage.role == ChatRole.ASSISTANT,
            ChatMessage.response_time_ms.isnot(None),
        )
    )
    avg_rt = avg_rt_result.scalar()

    return AIUsageHistoryResponse(
        entries=[
            AIUsageHistoryEntry(
                usage_date=r.usage_date,
                messages_used=r.messages_used,
                images_used=r.images_used,
            )
            for r in rows
        ],
        total_messages=sum(r.messages_used for r in rows),
        total_sessions=total_sessions,
        avg_response_time_ms=float(avg_rt) if avg_rt is not None else None,
    )


# ── Chat endpoint ─────────────────────────────────────────────────────────────

@router.post("/chat")
async def chat(
    request: Request,
    body: ChatRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    request_id = get_request_id() or "-"

    # ── Rate limiting (atomic upsert, no SELECT + INSERT race) ────────────
    tracker = await _upsert_usage_tracker(current_user.id, session, messages_delta=0)
    if tracker.messages_used >= DAILY_MESSAGE_LIMIT:
        raise HTTPException(
            status_code=429,
            detail={
                "code": "DAILY_LIMIT_REACHED",
                "message": (
                    "You've reached today's AI limit. "
                    "Your quota resets automatically tomorrow."
                ),
                "reset_at": _next_reset_utc(),
            },
        )

    # Increment usage atomically
    tracker = await _upsert_usage_tracker(current_user.id, session, messages_delta=1)
    await session.commit()

    # ── Session management ────────────────────────────────────────────────
    now_utc = datetime.now(UTC)
    chat_session_id = body.session_id

    if not chat_session_id:
        title = (body.message[:50] + "…") if len(body.message) > 50 else body.message
        new_session = ChatSession(
            user_id=current_user.id,
            title=title,
            last_active_at=now_utc,
            message_count=0,
        )
        session.add(new_session)
        await session.commit()
        await session.refresh(new_session)
        chat_session_id = new_session.id
    else:
        cs_stmt = select(ChatSession).where(
            ChatSession.id == chat_session_id,
            ChatSession.user_id == current_user.id,
        )
        existing = (await session.execute(cs_stmt)).scalars().first()
        if not existing:
            raise HTTPException(status_code=404, detail="Session not found")

    # ── Save user message ─────────────────────────────────────────────────
    user_msg = ChatMessage(
        session_id=chat_session_id,
        role=ChatRole.USER,
        content=body.message,
    )
    session.add(user_msg)
    await session.commit()

    # ── Fetch conversation history (excluding the message just saved) ─────
    history_rows = (
        await session.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == chat_session_id)
            .order_by(ChatMessage.created_at)
        )
    ).scalars().all()
    history = [
        {"role": m.role.value, "content": m.content}
        for m in history_rows[:-1]  # all except the user msg we just saved
    ]

    # ── Build personalised context ─────────────────────────────────────────
    user_context = await _build_user_context(current_user.id, session, body.message)

    # ── AI service (singleton) ────────────────────────────────────────────────────
    service = get_ai_coach_service()

    # ── Streaming response ─────────────────────────────────────────────────
    if body.stream:
        t_start = time.perf_counter()

        async def generate():
            accumulated = ""
            try:
                yield f"data: {json.dumps({'session_id': str(chat_session_id)})}\n\n"
                async for chunk in service.chat_stream(body.message, history, user_context):
                    accumulated += chunk
                    yield f"data: {json.dumps({'content': chunk})}\n\n"
            except Exception as exc:
                logger.exception("Streaming AI error")
                yield f"data: {json.dumps({'error': str(exc)})}\n\n"
            finally:
                elapsed_ms = int((time.perf_counter() - t_start) * 1000)
                if accumulated:
                    try:
                        from app.db.session import db_manager
                        async with db_manager.session_factory() as s2:
                            ast_msg = ChatMessage(
                                session_id=chat_session_id,
                                role=ChatRole.ASSISTANT,
                                content=accumulated,
                                response_time_ms=elapsed_ms,
                            )
                            s2.add(ast_msg)
                            cs = (
                                await s2.execute(
                                    select(ChatSession).where(ChatSession.id == chat_session_id)
                                )
                            ).scalars().first()
                            if cs:
                                cs.last_active_at = datetime.now(UTC)
                                cs.updated_at = datetime.now(UTC)
                                cs.message_count = (cs.message_count or 0) + 2  # user + assistant
                            await s2.commit()
                            background_tasks.add_task(_extract_memory_background, current_user.id, body.message, accumulated)
                    except Exception as save_exc:
                        logger.error(f"Failed to save assistant message: {save_exc}")
                yield "data: [DONE]\n\n"

        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            },
        )

    # ── Non-streaming response ─────────────────────────────────────────────
    t_start = time.perf_counter()
    try:
        ai_response = await service.chat(body.message, history, user_context)
        elapsed_ms = int((time.perf_counter() - t_start) * 1000)

        ast_msg = ChatMessage(
            session_id=chat_session_id,
            role=ChatRole.ASSISTANT,
            content=ai_response,
            response_time_ms=elapsed_ms,
        )
        session.add(ast_msg)

        cs_upd = (
            await session.execute(
                select(ChatSession).where(ChatSession.id == chat_session_id)
            )
        ).scalars().first()
        if cs_upd:
            cs_upd.last_active_at = now_utc
            cs_upd.updated_at = now_utc
            cs_upd.message_count = (cs_upd.message_count or 0) + 2

        await session.commit()

        background_tasks.add_task(_extract_memory_background, current_user.id, body.message, ai_response)

        return {
            "success": True,
            "message": "Response generated.",
            "data": {
                "response": ai_response,
                "session_id": str(chat_session_id),
                "response_time_ms": elapsed_ms,
                "timestamp": now_utc.isoformat(),
            },
        }
    except Exception as exc:
        logger.exception("AI chat failed")
        return JSONResponse(
            status_code=502,
            content={
                "success": False,
                "error": {
                    "code": "AI_CHAT_FAILED",
                    "message": str(exc),
                    "request_id": request_id,
                },
            },
        )


# ── AI Analysis endpoints ─────────────────────────────────────────────────────

class MealPlanRequest(BaseModel):
    days: int = 1
    calories: int | None = None
    preferences: str | None = None

DAILY_MEAL_PLAN_LIMIT = 5

@router.post("/image-analysis")
async def analyze_food_image(
    request: Request,
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    request_id = get_request_id() or "-"
    tracker = await _upsert_usage_tracker(current_user.id, session)
    if tracker.images_used >= DAILY_IMAGE_LIMIT:
        raise HTTPException(
            status_code=429,
            detail={
                "code": "DAILY_LIMIT_REACHED",
                "message": "You've reached today's image analysis limit.",
                "reset_at": _next_reset_utc(),
            },
        )

    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large")

    settings = get_settings()
    service = FoodRecognitionService(
        gemini_api_key=settings.GEMINI_API_KEY,
        groq_api_key=settings.GROQ_API_KEY,
        gemini_model=settings.GEMINI_MODEL,
    )

    try:
        result = await service.analyze_image(contents, file.filename or "food.jpg")
        tracker = await _upsert_usage_tracker(current_user.id, session, images_delta=1)
        await session.commit()
        return {
            "success": True,
            "data": {
                "foods": [
                    {
                        "food_name": f.food_name,
                        "calories_kcal": str(f.calories_kcal),
                        "protein_g": str(f.protein_g),
                        "carbohydrate_g": str(f.carbohydrate_g),
                        "fat_g": str(f.fat_g),
                        "serving_size_g": str(f.serving_size_g),
                    }
                    for f in result.foods
                ],
                "raw_response": result.raw_response,
            }
        }
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))

@router.post("/meal-plan")
async def generate_meal_plan(
    body: MealPlanRequest,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    tracker = await _upsert_usage_tracker(current_user.id, session)
    if tracker.meal_plans_used >= DAILY_MEAL_PLAN_LIMIT:
        raise HTTPException(
            status_code=429,
            detail={
                "code": "DAILY_LIMIT_REACHED",
                "message": "You've reached today's meal plan generation limit.",
                "reset_at": _next_reset_utc(),
            }
        )

    # Increment meal plan usage
    today = date.today()
    stmt = (
        pg_insert(AIUsageTracker)
        .values(
            user_id=current_user.id,
            usage_date=today,
            messages_used=0,
            images_used=0,
            meal_plans_used=1,
            tokens_used=0,
        )
        .on_conflict_do_update(
            constraint="uq_ai_usage_user_date",
            set_={
                "meal_plans_used": AIUsageTracker.meal_plans_used + 1,
                "updated_at": func.now(),
            },
        )
        .returning(AIUsageTracker)
    )
    await session.execute(stmt)
    await session.commit()

    return {"success": True, "data": {"meal_plan": f"Meal plan for {body.days} days generated."}}
