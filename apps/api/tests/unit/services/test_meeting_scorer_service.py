"""
Unit tests for meeting_scorer_service functions.
"""

import json
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock, AsyncMock
from uuid import uuid4

from app.services.meeting_scorer_service import (
    MeetingScorerService,
    EventForScoring,
    ScoredEvent,
)


class TestBuildBatchPrompt:
    """Tests for building the batch scoring prompt."""

    def test_builds_prompt_with_single_event(self):
        """Builds prompt correctly for a single event."""
        service = MeetingScorerService()
        events = [
            EventForScoring(
                id=uuid4(),
                google_event_id="event-123",
                title="Team Meeting",
                description="Weekly sync",
                start_time=datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc),
                end_time=datetime(2024, 1, 15, 11, 0, tzinfo=timezone.utc),
                attendees_count=5,
            )
        ]

        prompt = service._build_batch_prompt(events)

        assert "Team Meeting" in prompt
        assert "Weekly sync" in prompt
        assert "60" in prompt  # duration in minutes
        assert "5" in prompt  # attendees
        assert "index" in prompt
        assert "1-10" in prompt

    def test_builds_prompt_with_multiple_events(self):
        """Builds prompt correctly for multiple events."""
        service = MeetingScorerService()
        events = [
            EventForScoring(
                id=uuid4(),
                google_event_id="event-1",
                title="Standup",
                description=None,
                start_time=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
                end_time=datetime(2024, 1, 15, 9, 15, tzinfo=timezone.utc),
                attendees_count=3,
            ),
            EventForScoring(
                id=uuid4(),
                google_event_id="event-2",
                title="Client Presentation",
                description="Q1 Results",
                start_time=datetime(2024, 1, 15, 14, 0, tzinfo=timezone.utc),
                end_time=datetime(2024, 1, 15, 15, 30, tzinfo=timezone.utc),
                attendees_count=12,
            ),
        ]

        prompt = service._build_batch_prompt(events)

        assert "Standup" in prompt
        assert "Client Presentation" in prompt
        assert "Q1 Results" in prompt
        assert '"index": 0' in prompt
        assert '"index": 1' in prompt

    def test_handles_none_description(self):
        """Handles None description gracefully."""
        service = MeetingScorerService()
        events = [
            EventForScoring(
                id=uuid4(),
                google_event_id="event-123",
                title="Quick Sync",
                description=None,
                start_time=datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc),
                end_time=datetime(2024, 1, 15, 10, 30, tzinfo=timezone.utc),
                attendees_count=None,
            )
        ]

        prompt = service._build_batch_prompt(events)

        assert "Quick Sync" in prompt
        assert '"description": ""' in prompt


class TestParseScores:
    """Tests for parsing Claude's scoring response."""

    def test_parses_valid_json_response(self):
        """Parses a valid JSON response correctly."""
        service = MeetingScorerService()
        events = [
            EventForScoring(
                id=uuid4(),
                google_event_id="event-1",
                title="Standup",
                description=None,
                start_time=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
                end_time=datetime(2024, 1, 15, 9, 15, tzinfo=timezone.utc),
                attendees_count=3,
            ),
            EventForScoring(
                id=uuid4(),
                google_event_id="event-2",
                title="Interview",
                description="Senior dev candidate",
                start_time=datetime(2024, 1, 15, 14, 0, tzinfo=timezone.utc),
                end_time=datetime(2024, 1, 15, 15, 0, tzinfo=timezone.utc),
                attendees_count=4,
            ),
        ]

        response = json.dumps([
            {"index": 0, "score": 3, "reason": "Daily standup", "category": "routine"},
            {"index": 1, "score": 8, "reason": "Interview", "category": "high_stakes"},
        ])

        results = service._parse_scores(response, events)

        assert len(results) == 2
        assert results[0].score == 3
        assert results[0].category == "routine"
        assert results[1].score == 8
        assert results[1].category == "high_stakes"

    def test_handles_markdown_code_block(self):
        """Handles response wrapped in markdown code block."""
        service = MeetingScorerService()
        events = [
            EventForScoring(
                id=uuid4(),
                google_event_id="event-1",
                title="Meeting",
                description=None,
                start_time=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
                end_time=datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc),
                attendees_count=2,
            )
        ]

        response = """```json
[{"index": 0, "score": 5, "reason": "Regular meeting", "category": "moderate"}]
```"""

        results = service._parse_scores(response, events)

        assert len(results) == 1
        assert results[0].score == 5

    def test_clamps_scores_to_valid_range(self):
        """Clamps scores to 1-10 range."""
        service = MeetingScorerService()
        events = [
            EventForScoring(
                id=uuid4(),
                google_event_id="event-1",
                title="Meeting",
                description=None,
                start_time=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
                end_time=datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc),
                attendees_count=2,
            )
        ]

        # Score of 15 should be clamped to 10
        response = json.dumps([
            {"index": 0, "score": 15, "reason": "Test", "category": "high_stakes"}
        ])

        results = service._parse_scores(response, events)

        assert results[0].score == 10

    def test_handles_invalid_json(self):
        """Returns default scores for invalid JSON."""
        service = MeetingScorerService()
        events = [
            EventForScoring(
                id=uuid4(),
                google_event_id="event-1",
                title="Meeting",
                description=None,
                start_time=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
                end_time=datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc),
                attendees_count=2,
            )
        ]

        response = "This is not valid JSON at all"

        results = service._parse_scores(response, events)

        assert len(results) == 1
        assert results[0].score == 5  # default
        assert results[0].category == "moderate"

    def test_handles_missing_event_in_response(self):
        """Returns default for events not in response."""
        service = MeetingScorerService()
        events = [
            EventForScoring(
                id=uuid4(),
                google_event_id="event-1",
                title="Meeting 1",
                description=None,
                start_time=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
                end_time=datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc),
                attendees_count=2,
            ),
            EventForScoring(
                id=uuid4(),
                google_event_id="event-2",
                title="Meeting 2",
                description=None,
                start_time=datetime(2024, 1, 15, 11, 0, tzinfo=timezone.utc),
                end_time=datetime(2024, 1, 15, 12, 0, tzinfo=timezone.utc),
                attendees_count=2,
            ),
        ]

        # Response only has first event
        response = json.dumps([
            {"index": 0, "score": 7, "reason": "Important", "category": "high_stakes"}
        ])

        results = service._parse_scores(response, events)

        assert len(results) == 2
        assert results[0].score == 7
        assert results[1].score == 5  # default for missing


class TestScoreEventsBatch:
    """Tests for the batch scoring function."""

    @pytest.mark.asyncio
    async def test_scores_events_successfully(self):
        """Successfully scores events using Claude."""
        service = MeetingScorerService()
        events = [
            EventForScoring(
                id=uuid4(),
                google_event_id="event-1",
                title="Client Call",
                description="Quarterly review",
                start_time=datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc),
                end_time=datetime(2024, 1, 15, 11, 0, tzinfo=timezone.utc),
                attendees_count=8,
            )
        ]

        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(
                text=json.dumps([
                    {"index": 0, "score": 8, "reason": "Client review", "category": "high_stakes"}
                ])
            )
        ]

        with patch.object(service.client.messages, "create", return_value=mock_response):
            results = await service.score_events_batch(events)

        assert len(results) == 1
        assert results[0].score == 8
        assert results[0].category == "high_stakes"

    @pytest.mark.asyncio
    async def test_returns_empty_for_no_events(self):
        """Returns empty list when no events provided."""
        service = MeetingScorerService()

        results = await service.score_events_batch([])

        assert results == []

    @pytest.mark.asyncio
    async def test_handles_api_error_gracefully(self):
        """Returns default scores on API error."""
        import anthropic

        service = MeetingScorerService()
        events = [
            EventForScoring(
                id=uuid4(),
                google_event_id="event-1",
                title="Meeting",
                description=None,
                start_time=datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc),
                end_time=datetime(2024, 1, 15, 11, 0, tzinfo=timezone.utc),
                attendees_count=2,
            )
        ]

        with patch.object(
            service.client.messages,
            "create",
            side_effect=anthropic.APIError(
                message="API Error",
                request=MagicMock(),
                body=None,
            ),
        ):
            results = await service.score_events_batch(events)

        assert len(results) == 1
        assert results[0].score == 5  # default
        assert "unavailable" in results[0].reason.lower()

    @pytest.mark.asyncio
    async def test_uses_correct_model(self):
        """Verifies Haiku model is used for cost efficiency."""
        service = MeetingScorerService()
        events = [
            EventForScoring(
                id=uuid4(),
                google_event_id="event-1",
                title="Meeting",
                description=None,
                start_time=datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc),
                end_time=datetime(2024, 1, 15, 11, 0, tzinfo=timezone.utc),
                attendees_count=2,
            )
        ]

        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(
                text=json.dumps([
                    {"index": 0, "score": 5, "reason": "Test", "category": "moderate"}
                ])
            )
        ]

        with patch.object(service.client.messages, "create", return_value=mock_response) as mock_create:
            await service.score_events_batch(events)

            # Verify Haiku model is used
            call_kwargs = mock_create.call_args.kwargs
            assert "haiku" in call_kwargs["model"].lower()


class TestScoredEvent:
    """Tests for the ScoredEvent dataclass."""

    def test_creates_scored_event(self):
        """Creates a scored event with all fields."""
        event_id = uuid4()
        scored = ScoredEvent(
            event_id=event_id,
            google_event_id="event-123",
            score=8,
            reason="Important client meeting",
            category="high_stakes",
        )

        assert scored.event_id == event_id
        assert scored.score == 8
        assert scored.reason == "Important client meeting"
        assert scored.category == "high_stakes"


class TestEventForScoring:
    """Tests for the EventForScoring dataclass."""

    def test_creates_event_for_scoring(self):
        """Creates an event for scoring with all fields."""
        event_id = uuid4()
        start = datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc)
        end = datetime(2024, 1, 15, 11, 0, tzinfo=timezone.utc)

        event = EventForScoring(
            id=event_id,
            google_event_id="event-123",
            title="Team Meeting",
            description="Weekly sync",
            start_time=start,
            end_time=end,
            attendees_count=5,
        )

        assert event.id == event_id
        assert event.title == "Team Meeting"
        assert event.description == "Weekly sync"
        assert event.attendees_count == 5
