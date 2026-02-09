"""AI-powered meeting importance scoring using Claude Haiku."""

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

import anthropic
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.calendar_event import CalendarEvent

logger = logging.getLogger(__name__)
settings = get_settings()

# Use Haiku for cost-efficient classification
SCORER_MODEL = "claude-haiku-4-5-20251001"


@dataclass(frozen=True, slots=True)
class ScoredEvent:
    """Result of scoring a calendar event."""

    event_id: UUID
    google_event_id: str
    score: int
    reason: str
    category: str  # routine, moderate, high_stakes


@dataclass(frozen=True, slots=True)
class EventForScoring:
    """Event data needed for scoring."""

    id: UUID
    google_event_id: str
    title: str
    description: Optional[str]
    start_time: datetime
    end_time: datetime
    attendees_count: Optional[int]


class MeetingScorerService:
    """Service for scoring meeting importance using Claude Haiku."""

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    def _build_batch_prompt(self, events: list[EventForScoring]) -> str:
        """Build a prompt to score multiple events at once."""
        events_json = []
        for i, event in enumerate(events):
            duration_minutes = int(
                (event.end_time - event.start_time).total_seconds() / 60
            )
            events_json.append(
                {
                    "index": i,
                    "title": event.title,
                    "description": event.description or "",
                    "duration_minutes": duration_minutes,
                    "attendees": event.attendees_count or 0,
                    "time": event.start_time.strftime("%A %I:%M %p"),
                }
            )

        return f"""You are analyzing calendar events to determine their importance for pre-meeting preparation.

Rate each meeting's importance from 1-10 where:
- 1-3: Routine (standups, casual syncs, recurring team meetings, lunch breaks)
- 4-6: Moderate (project updates, 1:1s, internal reviews, regular team meetings)
- 7-10: High stakes (interviews, client meetings, presentations, executive meetings, negotiations, performance reviews, board meetings)

Events to analyze:
{json.dumps(events_json, indent=2)}

Respond with a JSON array only, no other text. Each item must have:
- "index": the event index from above
- "score": integer 1-10
- "reason": brief reason (max 10 words)
- "category": one of "routine", "moderate", "high_stakes"

Example response:
[{{"index": 0, "score": 3, "reason": "Regular team standup", "category": "routine"}}, {{"index": 1, "score": 8, "reason": "Client presentation", "category": "high_stakes"}}]"""

    def _parse_scores(
        self, response_text: str, events: list[EventForScoring]
    ) -> list[ScoredEvent]:
        """Parse Claude's response into scored events."""
        try:
            # Try to extract JSON from the response
            text = response_text.strip()
            # Handle potential markdown code blocks
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
                text = text.strip()

            scores_data = json.loads(text)

            # Create a mapping from index to score data
            index_to_score = {item["index"]: item for item in scores_data}

            results = []
            for i, event in enumerate(events):
                if i in index_to_score:
                    score_data = index_to_score[i]
                    results.append(
                        ScoredEvent(
                            event_id=event.id,
                            google_event_id=event.google_event_id,
                            score=max(1, min(10, int(score_data.get("score", 5)))),
                            reason=str(score_data.get("reason", ""))[:100],
                            category=score_data.get("category", "moderate"),
                        )
                    )
                else:
                    # Fallback for missing events
                    results.append(
                        ScoredEvent(
                            event_id=event.id,
                            google_event_id=event.google_event_id,
                            score=5,
                            reason="Unable to score",
                            category="moderate",
                        )
                    )

            return results

        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.error(f"Failed to parse scoring response: {e}, response: {response_text[:200]}")
            # Return default scores for all events
            return [
                ScoredEvent(
                    event_id=event.id,
                    google_event_id=event.google_event_id,
                    score=5,
                    reason="Scoring unavailable",
                    category="moderate",
                )
                for event in events
            ]

    async def score_events_batch(
        self, events: list[EventForScoring]
    ) -> list[ScoredEvent]:
        """
        Score multiple events in a single Claude API call.

        Uses Haiku for cost efficiency (~$0.001 per 10 events).
        """
        if not events:
            return []

        prompt = self._build_batch_prompt(events)

        try:
            message = self.client.messages.create(
                model=SCORER_MODEL,
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
            )

            response_text = message.content[0].text
            return self._parse_scores(response_text, events)

        except anthropic.APIError as e:
            logger.error(f"Claude API error during scoring: {e}")
            # Return default scores on API failure
            return [
                ScoredEvent(
                    event_id=event.id,
                    google_event_id=event.google_event_id,
                    score=5,
                    reason="Scoring unavailable",
                    category="moderate",
                )
                for event in events
            ]


async def get_events_needing_scoring(
    db: AsyncSession,
    user_id: UUID,
    limit: int = 20,
) -> list[EventForScoring]:
    """Get events that need scoring (no score or etag changed)."""
    result = await db.execute(
        select(CalendarEvent)
        .where(
            CalendarEvent.user_id == user_id,
            CalendarEvent.is_deleted == False,  # noqa: E712
            CalendarEvent.importance_score.is_(None),
            CalendarEvent.start_time > datetime.now(timezone.utc),
        )
        .order_by(CalendarEvent.start_time)
        .limit(limit)
    )
    events = result.scalars().all()

    return [
        EventForScoring(
            id=event.id,
            google_event_id=event.google_event_id,
            title=event.title,
            description=event.description,
            start_time=event.start_time,
            end_time=event.end_time,
            attendees_count=event.attendees_count,
        )
        for event in events
    ]


async def save_scores(db: AsyncSession, scores: list[ScoredEvent]) -> None:
    """Save scored events to the database."""
    now = datetime.now(timezone.utc)

    for score in scores:
        await db.execute(
            update(CalendarEvent)
            .where(CalendarEvent.id == score.event_id)
            .values(
                importance_score=score.score,
                importance_reason=score.reason,
                importance_category=score.category,
                scored_at=now,
            )
        )

    await db.commit()


async def score_user_events(
    db: AsyncSession,
    user_id: UUID,
    scorer: MeetingScorerService | None = None,
) -> int:
    """
    Score all unscored events for a user.

    Returns the number of events scored.
    """
    if scorer is None:
        scorer = MeetingScorerService()

    events = await get_events_needing_scoring(db, user_id)

    if not events:
        return 0

    scores = await scorer.score_events_batch(events)
    await save_scores(db, scores)

    logger.info(f"Scored {len(scores)} events for user {user_id}")
    return len(scores)
