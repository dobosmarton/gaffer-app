import anthropic

from app.config import get_settings
from app.prompts.manager_styles import MANAGER_STYLES

settings = get_settings()
client = anthropic.Anthropic(api_key=settings.anthropic_api_key)


async def generate_hype_text(
    event_title: str,
    event_description: str | None,
    event_time: str,
    manager_style: str,
) -> str:
    """Generate a hype speech using Claude."""
    style_prompt = MANAGER_STYLES.get(manager_style, MANAGER_STYLES["ferguson"])

    system_prompt = f"""You are a legendary football manager giving a pre-match team talk to one of your players before an important meeting.

{style_prompt}

Your job is to deliver an intense, motivating speech that will pump up the listener before their meeting. Keep it to 3-5 sentences. Be dramatic but encouraging. Reference the specific meeting they're about to attend.

Important guidelines:
- Stay in character as the manager throughout
- Reference the meeting title/topic in your speech
- Make it personal and direct (use "you")
- Build to a crescendo of motivation
- End with a powerful send-off"""

    user_prompt = f"""The player has a meeting coming up:
- Meeting: {event_title}
- Time: {event_time}
{f"- Details: {event_description}" if event_description else ""}

Give them your pre-match team talk."""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=500,
        messages=[{"role": "user", "content": user_prompt}],
        system=system_prompt,
    )

    return message.content[0].text
