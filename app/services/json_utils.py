import json
import re


def extract_json_array(raw: str) -> list:
    """Strip markdown fences and pull the first [...] block out of a raw LLM response."""
    cleaned = raw.strip()
    cleaned = re.sub(r"^```(json)?", "", cleaned).strip()
    cleaned = re.sub(r"```$", "", cleaned).strip()

    match = re.search(r"\[.*\]", cleaned, re.DOTALL)
    if not match:
        raise ValueError("No JSON array found in model response")
    return json.loads(match.group(0))
