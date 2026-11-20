#!/usr/bin/env python3
"""Generate outline.md from seed + world + characters + mystery + craft."""
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
        "anthropic-beta": "context-1m-2025-08-07",
        "content-type": "application/json",
    }
    payload = {
        "model": WRITER_MODEL,
        "max_tokens": max_tokens,
        "temperature": 0.5,
        "system": (
            "You are a novel architect with deep knowledge of Save the Cat beats, "
            "Sanderson's plotting principles, Dan Harmon's Story Circle, and MICE Quotient. "
            "You build outlines that an author can draft from without inventing structure "
            "on the fly. Every chapter has beats, emotional arc, and try-fail cycle type. "
            "You never use AI slop words. You write in clean, direct prose."
        ),
        "messages": [{"role": "user", "content": prompt}],
    }
    resp = post_messages(f"{API_BASE}/v1/messages", headers=headers, json=payload, timeout=600)
    resp.raise_for_status()
    return resp.json()["content"][0]["text"]

seed = (BASE_DIR / "seed.txt").read_text()
world = (BASE_DIR / "world.md").read_text()
characters = (BASE_DIR / "characters.md").read_text()
mystery = (BASE_DIR / "MYSTERY.md").read_text() if (BASE_DIR / "MYSTERY.md").exists() else "Infer a coherent central conflict from the seed and outline."
craft = (CODE_DIR / "CRAFT.md").read_text()

# Voice Part 2 only
voice = (BASE_DIR / "voice.md").read_text()
voice_lines = voice.split('\n')
part2_start = next((i for i, l in enumerate(voice_lines) if 'Part 2' in l), 0)
voice_part2 = '\n'.join(voice_lines[part2_start:])

prompt = f"""Build a complete chapter outline for the novel below. Respect the chapter
count requested in the seed; otherwise choose a justified count appropriate to
its scope. Number headings exactly ## Chapter N: Title, starting at 1. For each
chapter specify POV, location, goal, obstacle, turning point, emotional change,
new information and causal link to the next chapter. Follow the established
characters and world, never import another novel's names or plot. Add a concise
foreshadowing ledger with planting and payoff chapters. Return Markdown only.
SEED:
{seed}
WORLD:
{world}
CHARACTERS:
{characters}
CRAFT:
{craft}
VOICE:
{voice_part2}"""

print("Calling writer model...", file=sys.stderr)
result = call_writer(prompt)
(BASE_DIR / "outline.md").write_text(result, encoding="utf-8")
print(result)
