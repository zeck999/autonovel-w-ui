#!/usr/bin/env python3
"""
One-shot characters.md generator for foundation phase.
Reads seed.txt + voice.md + world.md + CRAFT.md, calls writer model.
"""
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
        "temperature": 0.7,
        "system": (
            "You are a character designer for literary fiction with deep knowledge of "
            "wound/want/need/lie frameworks, Sanderson's three sliders, and dialogue "
            "distinctiveness. You create characters who feel like real people with "
            "contradictions, secrets, and speech patterns you can hear. "
            "You never use AI slop words. You write in clean, direct prose."
        ),
        "messages": [{"role": "user", "content": prompt}],
    }
    resp = post_messages(f"{API_BASE}/v1/messages", headers=headers, json=payload, timeout=300)
    resp.raise_for_status()
    return resp.json()["content"][0]["text"]

seed = (BASE_DIR / "seed.txt").read_text()
world = (BASE_DIR / "world.md").read_text()

# Voice Part 2 only
voice = (BASE_DIR / "voice.md").read_text()
voice_lines = voice.split('\n')
part2_start = next((i for i, l in enumerate(voice_lines) if 'Part 2' in l), 0)
voice_part2 = '\n'.join(voice_lines[part2_start:])

prompt = f"""Create a character registry for the novel described below. Derive every name,
relationship and conflict from the seed and world, not a different novel. Include
protagonist, antagonist and supporting cast: goals, fears, contradictions, voice,
relationships, agency and character arcs. Keep the cast size appropriate to this
story. Return Markdown only, headed # Character Registry.
SEED:
{seed}
WORLD:
{world}
VOICE:
{voice_part2}"""

print("Calling writer model...", file=sys.stderr)
result = call_writer(prompt)
(BASE_DIR / "characters.md").write_text(result, encoding="utf-8")
print(result)
