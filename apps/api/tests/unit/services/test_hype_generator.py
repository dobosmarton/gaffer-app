"""
Unit tests for hype_generator functions.
"""

import pytest
from unittest.mock import patch, MagicMock

from app.services.hype_generator import (
    strip_audio_tags,
    sanitize_audio_tags,
    generate_hype_text,
    SUPPORTED_AUDIO_TAGS,
)


class TestStripAudioTags:
    """Tests for stripping audio tags from text."""

    def test_strips_single_tag(self):
        """Removes a single tag from text."""
        text = "[excited] This is your moment!"
        result = strip_audio_tags(text)
        assert result == "This is your moment!"

    def test_strips_multiple_tags(self):
        """Removes multiple tags from text."""
        text = "[excited] Listen up! [pause] This is it! [shouts] GO!"
        result = strip_audio_tags(text)
        assert result == "Listen up! This is it! GO!"

    def test_handles_no_tags(self):
        """Returns text unchanged when no tags present."""
        text = "Just regular text"
        result = strip_audio_tags(text)
        assert result == "Just regular text"

    def test_handles_consecutive_tags(self):
        """Handles tags directly next to each other."""
        text = "[excited] [intense] Double energy!"
        result = strip_audio_tags(text)
        assert result == "Double energy!"

    def test_handles_tags_with_spaces_inside(self):
        """Handles tags with spaces inside brackets."""
        text = "[long pause] Wait for it..."
        result = strip_audio_tags(text)
        assert result == "Wait for it..."

    def test_strips_and_trims(self):
        """Result is trimmed of whitespace."""
        text = "  [excited] Hello world!  "
        result = strip_audio_tags(text)
        assert result == "Hello world!"


class TestSanitizeAudioTags:
    """Tests for sanitizing audio tags to whitelist."""

    def test_keeps_supported_tags(self):
        """Preserves tags that are in the whitelist."""
        text = "[excited] Hello [pause] world"
        result = sanitize_audio_tags(text)
        assert "[excited]" in result
        assert "[pause]" in result

    def test_removes_unsupported_tags(self):
        """Removes tags not in the whitelist."""
        text = "[unsupported_tag] This is text [excited] more text"
        result = sanitize_audio_tags(text)
        assert "[unsupported_tag]" not in result
        assert "unsupported_tag" not in result
        assert "[excited]" in result
        assert "This is text" in result

    def test_normalizes_tag_case(self):
        """Tags are normalized to lowercase."""
        text = "[EXCITED] Uppercase tag"
        result = sanitize_audio_tags(text)
        assert "[excited]" in result
        assert "[EXCITED]" not in result

    def test_handles_mixed_case_tag(self):
        """Handles mixed case tags."""
        text = "[ExCiTeD] Mixed case"
        result = sanitize_audio_tags(text)
        assert "[excited]" in result

    @pytest.mark.parametrize(
        "tag",
        [
            "excited",
            "nervous",
            "frustrated",
            "calm",
            "intense",
            "angry",
            "sad",
            "happy",
            "whispers",
            "shouts",
            "pause",
            "laughs",
            "sighs",
            "dramatic",
            "sarcastic",
        ],
    )
    def test_common_supported_tags_preserved(self, tag):
        """Common whitelisted tags are preserved."""
        text = f"[{tag}] Test text"
        result = sanitize_audio_tags(text)
        assert f"[{tag}]" in result

    def test_removes_all_unsupported_keeps_text(self):
        """Removes unsupported tags but keeps surrounding text."""
        text = "[fake1] Hello [fake2] world [fake3]"
        result = sanitize_audio_tags(text)
        assert "[fake" not in result
        assert "Hello" in result
        assert "world" in result


class TestGenerateHypeText:
    """Tests for the Claude API hype generation."""

    @pytest.mark.asyncio
    async def test_generates_hype_text(self, mock_claude_response):
        """Successfully generates hype text from Claude."""
        with patch("app.services.hype_generator._get_client") as mock_get_client:
            mock_client = mock_get_client.return_value
            mock_client.messages.create.return_value = mock_claude_response

            result = await generate_hype_text(
                event_title="Team Meeting",
                event_description="Weekly sync",
                event_time="2024-01-15T10:00:00Z",
                manager_style="ferguson",
            )

            assert result == mock_claude_response.content[0].text
            mock_client.messages.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_calls_claude_with_correct_model(self, mock_claude_response):
        """Calls Claude with the expected model."""
        with patch("app.services.hype_generator._get_client") as mock_get_client:
            mock_client = mock_get_client.return_value
            mock_client.messages.create.return_value = mock_claude_response

            await generate_hype_text(
                event_title="Meeting",
                event_description=None,
                event_time="2024-01-15T10:00:00Z",
                manager_style="ferguson",
            )

            call_kwargs = mock_client.messages.create.call_args.kwargs
            assert "claude" in call_kwargs["model"].lower()

    @pytest.mark.asyncio
    async def test_handles_none_description(self, mock_claude_response):
        """Handles None event description."""
        with patch("app.services.hype_generator._get_client") as mock_get_client:
            mock_client = mock_get_client.return_value
            mock_client.messages.create.return_value = mock_claude_response

            result = await generate_hype_text(
                event_title="Meeting",
                event_description=None,
                event_time="2024-01-15T10:00:00Z",
                manager_style="ferguson",
            )

            assert result is not None

    @pytest.mark.asyncio
    async def test_falls_back_to_ferguson_for_unknown_style(self, mock_claude_response):
        """Falls back to Ferguson style for unknown manager."""
        with patch("app.services.hype_generator._get_client") as mock_get_client:
            mock_client = mock_get_client.return_value
            mock_client.messages.create.return_value = mock_claude_response

            result = await generate_hype_text(
                event_title="Meeting",
                event_description=None,
                event_time="2024-01-15T10:00:00Z",
                manager_style="unknown_manager_style",
            )

            # Should still work with fallback
            assert result is not None
            mock_client.messages.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_includes_event_details_in_prompt(self, mock_claude_response):
        """Event details are included in the prompt."""
        with patch("app.services.hype_generator._get_client") as mock_get_client:
            mock_client = mock_get_client.return_value
            mock_client.messages.create.return_value = mock_claude_response

            await generate_hype_text(
                event_title="Important Product Launch",
                event_description="Launching our new feature",
                event_time="2024-01-15T10:00:00Z",
                manager_style="klopp",
            )

            call_args = mock_client.messages.create.call_args
            # The event details should be in the messages
            messages = call_args.kwargs.get("messages", [])
            user_message = next(
                (m for m in messages if m.get("role") == "user"), {}
            )
            content = user_message.get("content", "")
            assert "Important Product Launch" in content
