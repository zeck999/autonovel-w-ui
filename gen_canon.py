#!/usr/bin/env python3
"""
Generate canon.md by extracting all hard facts from world.md + characters.md.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

from src.project_context import DATA_DIR, CODE_DIR
BASE_DIR = DATA_DIR
load_dotenv(CODE_DIR / ".env")

WRITER_MODEL = os.environ.get("AUTONOVEL_WRITER_MODEL", "claude-sonnet-4-6")
API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
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
        "temperature": 0.2,  # Low temp for factual extraction
        "system": (
            "You are a continuity editor extracting hard facts from novel "
            "planning documents. You are precise, exhaustive, and never invent facts "
            "that aren't in the source material. Every entry must be traceable to a "
            "specific statement in the source documents."
        ),
        "messages": [{"role": "user", "content": prompt}],
    }
    resp = httpx.post(f"{API_BASE}/v1/messages", headers=headers, json=payload, timeout=300)
    resp.raise_for_status()
    return resp.json()["content"][0]["text"]

world = (BASE_DIR / "world.md").read_text()
characters = (BASE_DIR / "characters.md").read_text()
seed = (BASE_DIR / "seed.txt").read_text()
outline = (BASE_DIR / "outline.md").read_text()

prompt = f"""Extract a canon ledger from the documents below. Record established facts,
chronology, character constraints, world rules and planted clues. Do not invent
facts or reuse characters from another novel. Return Markdown only.
WORLD:
{world}
CHARACTERS:
{characters}
OUTLINE:
{outline}"""

print("Calling writer model...", file=sys.stderr)
result = call_writer(prompt)
(BASE_DIR / "canon.md").write_text(result, encoding="utf-8")
print(result)
