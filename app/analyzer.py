from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ollama import chat

from config import MAX_MODEL_TEXT_CHARS, MODEL_NAME
from app.prompts import SYSTEM_PROMPT, USER_TEMPLATE
from app.schemas import BugAnalysis


def _compact_json(data: dict[str, Any]) -> str:
    text = json.dumps(data, ensure_ascii=False, indent=2)
    return text[:MAX_MODEL_TEXT_CHARS]


def analyze_viewport(result: dict[str, Any]) -> BugAnalysis:
    diagnostics = {
        "viewport": result["viewport"],
        "navigation_error": result["navigation_error"],
        "console_errors": result["console_errors"],
        "page_errors": result["page_errors"],
        "failed_requests": result["failed_requests"],
        "bad_responses": result["bad_responses"],
        "browser_facts": result["browser_facts"],
    }

    prompt = USER_TEMPLATE.format(
        viewport=result["viewport"],
        diagnostics=_compact_json(diagnostics),
    )

    response = chat(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": prompt,
                "images": [result["screenshot"]],
            },
        ],
        format=BugAnalysis.model_json_schema(),
        options={"temperature": 0},
    )

    return BugAnalysis.model_validate_json(response.message.content)
