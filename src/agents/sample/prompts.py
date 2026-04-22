from pathlib import Path

_SYSTEM_PROMPT_PATH = Path(__file__).resolve().parent / "system_prompt.md"
SYSTEM_PROMPT = _SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")
