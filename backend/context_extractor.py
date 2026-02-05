"""
Context extraction for passing between steps.
Modes: full, code_only, json_only, summary.
"""
import re
import json
from typing import Optional
from llm_client import call_llm


def extract_code_blocks(text: str) -> str:
    """Extract content from ```...``` blocks."""
    blocks = re.findall(r"```(?:\w+)?\n?(.*?)```", text, re.DOTALL)
    return "\n\n".join(b.strip() for b in blocks) if blocks else ""


def extract_json(text: str) -> str:
    """Extract first valid JSON object/array from text."""
    for start_char, end_char in [("{", "}"), ("[", "]")]:
        start = text.find(start_char)
        if start == -1:
            continue
        depth = 0
        i = start
        while i < len(text):
            c = text[i]
            if c == start_char:
                depth += 1
            elif c == end_char:
                depth -= 1
                if depth == 0:
                    candidate = text[start : i + 1]
                    try:
                        json.loads(candidate)
                        return candidate
                    except json.JSONDecodeError:
                        pass
            i += 1
    return ""


async def extract_summary(text: str, model: str = "kimi-k2p5") -> str:
    """Use LLM to produce a concise summary for next step context."""
    if len(text) < 500:
        return text
    messages = [
        {"role": "user", "content": f"Summarize the following in 2-4 sentences, preserving key facts and outputs:\n\n{text}"}
    ]
    summary, _, _, _, _ = await call_llm(messages, model=model, max_tokens=256)
    return summary.strip()


def extract_context(text: str, mode: str) -> str:
    """
    Synchronous extraction for full, code_only, json_only.
    Returns extracted string.
    """
    if mode == "full":
        return text
    if mode == "code_only":
        return extract_code_blocks(text)
    if mode == "json_only":
        return extract_json(text)
    return text 


async def extract_context_async(text: str, mode: str, model: str = "kimi-k2p5") -> str:
    """Full extraction including summary (async)."""
    if mode == "summary":
        return await extract_summary(text, model)
    return extract_context(text, mode)
