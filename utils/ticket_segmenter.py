# utils/ticket_segmenter.py

import re
from typing import List, Dict

def segment_ticket_with_ai(full_thread_summary: str) -> List[Dict]:
    """
    Uses an AI model to split a customer support ticket into structured parts.
    Each part includes the issue text and a 'resolved' flag.

    Returns:
        A list of dicts like: [{"issue": "...", "resolved": False}, {...}]
    """
    from config.llm_config_local import SECONDARY_MODEL_KEY
    from openai import OpenAI  # Assuming you already have openai_client setup like in reformulate_reply

    openai_client = OpenAI()

    system_prompt = """You are a support assistant specializing in ticket triage.
Split the following customer ticket into distinct issues.
For each issue, detect if it is already resolved.
Respond ONLY with a clean JSON array in the format:
[
  {"issue": "<issue text>", "resolved": false},
  {"issue": "<issue text>", "resolved": true}
]
Do NOT include any explanation or extra commentary.
"""

    user_prompt = f"""Ticket Text:
{full_thread_summary.strip()}
"""

    response = openai_client.chat.completions.create(
        model="gpt-4.1",  # or your chosen model
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.2  # Keep it low for high precision
    )

    content = response.choices[0].message.content.strip()

    import json
    try:
        parsed_output = json.loads(content)
        return parsed_output
    except json.JSONDecodeError:
        raise ValueError(f"Failed to parse AI segmenter output: {content}")

