from pathlib import Path

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"
BODY_MAX_CHARS = 6000


def load_system_prompt() -> str:
    return (PROMPTS_DIR / "signal_analysis_system.md").read_text(encoding="utf-8")


def build_user_prompt(signal: dict) -> str:
    template = (PROMPTS_DIR / "signal_analysis_user_template.md").read_text(encoding="utf-8")

    body = signal.get("body") or signal.get("summary") or signal.get("title") or ""
    if len(body) > BODY_MAX_CHARS:
        body = body[:BODY_MAX_CHARS] + "\n[truncated]"

    replacements = {
        "{{source_type}}": str(signal.get("source_type") or ""),
        "{{source_name}}": str(signal.get("source_name") or ""),
        "{{title}}": str(signal.get("title") or ""),
        "{{published_at}}": str(signal.get("published_at") or ""),
        "{{summary}}": str(signal.get("summary") or ""),
        "{{body}}": body,
        "{{url}}": str(signal.get("url") or ""),
        "{{category_hint}}": str(signal.get("category_hint") or ""),
        "{{matched_keywords}}": str(signal.get("matched_keywords") or ""),
        "{{latitude}}": str(signal.get("latitude") or ""),
        "{{longitude}}": str(signal.get("longitude") or ""),
        "{{event_category}}": str(signal.get("event_category") or ""),
        "{{event_status}}": str(signal.get("event_status") or ""),
    }

    for placeholder, value in replacements.items():
        template = template.replace(placeholder, value)

    return template
