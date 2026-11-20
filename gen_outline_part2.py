#!/usr/bin/env python3
"""Generate remaining chapters + foreshadowing ledger."""
import os
from src.text_provider import post_messages as _provider_post_messages
from src.narrative_contract import apply_contract as _provider_post_messages
from src.narrative_contract import apply_contract
import sys
from pathlib import Path
from dotenv import load_dotenv

from src.project_context import DATA_DIR, CODE_DIR
BASE_DIR = DATA_DIR


def post_messages(url, **kwargs):
    kwargs['json'] = apply_contract(kwargs.get('json', {}), BASE_DIR)
    return _provider_post_messages(url, **kwargs)



def post_messages(url, **kwargs):
    kwargs['json'] = apply_contract(kwargs.get('json', {}), BASE_DIR)
    return _provider_post_messages(url, **kwargs)

from src.project_context import guard_mutating_cli
guard_mutating_cli(BASE_DIR)
load_dotenv(CODE_DIR / ".env")

WRITER_MODEL = os.environ.get("AUTONOVEL_WRITER_MODEL", "claude-sonnet-4-6")
API_KEY = (os.environ.get("AUTONOVEL_TEXT_API_KEY", "") if os.environ.get("AUTONOVEL_TEXT_PROVIDER") == "openai-compatible" else os.environ.get("ANTHROPIC_API_KEY", ""))
API_BASE = os.environ.get("AUTONOVEL_API_BASE_URL", "https://api.anthropic.com")

def call_writer(prompt, max_tokens=16000):
    import httpx
    headers = {
        "x-api-key": API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    payload = {
        "model": WRITER_MODEL,
        "max_tokens": max_tokens,
        "temperature": 0.5,
        "system": (
            "You are a novel architect continuing an outline. Write in the same format "
            "as the preceding chapters. Every chapter needs: POV, Location, Save the Cat beat, "
            "% mark, Emotional arc, Try-fail cycle, Beats, Plants, Payoffs, Character movement, "
            "The lie, Word count target."
        ),
        "messages": [{"role": "user", "content": prompt}],
    }
    resp = post_messages(f"{API_BASE}/v1/messages", headers=headers, json=payload, timeout=600)
    resp.raise_for_status()
    return resp.json()["content"][0]["text"]

part1 = (BASE_DIR / "outline.md").read_text(encoding="utf-8")
characters = (BASE_DIR / "characters.md").read_text(encoding="utf-8")
prompt = f"""Review and complete this novel outline. Preserve all existing chapter
numbers and the intended total. Return the COMPLETE final outline, including
any missing chapter details and a foreshadowing ledger. Use only this project's
world and characters; do not introduce another novel's plot. Markdown only.
SEED:
{(BASE_DIR / 'seed.txt').read_text()}
WORLD:
{world}
CHARACTERS:
{characters}
CURRENT OUTLINE:
{existing}
VOICE:
{voice_part2}
CRAFT:
{craft}"""

print("Calling writer model...", file=sys.stderr)
result = call_writer(prompt)
(BASE_DIR / "outline.md").write_text(part1.rstrip() + "\n\n" + result + "\n", encoding="utf-8")
print(result)
