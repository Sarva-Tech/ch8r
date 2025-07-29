import json
import re

def parse_llm_response(content: str) -> dict:
    try:
        content = content.strip()
        if content.startswith("```"):
            content = re.sub(r"^```(?:json)?\s*", "", content, flags=re.IGNORECASE)
            content = re.sub(r"\s*```$", "", content, flags=re.IGNORECASE)

        return json.loads(content)
    except json.JSONDecodeError as e:
        print("Failed to parse LLM response as JSON:", e)
        raise
