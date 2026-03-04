import json
import re
from typing import Any, Callable, Dict, List, Optional, Union

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


def extract_and_merge_fields(
    validated_data: Dict[str, Any],
    field_selector: Union[List[str], Callable[[str], bool]],
    existing_data: Optional[Dict[str, Any]] = None,
    merge: bool = True
) -> Dict[str, Any]:
    extracted_data = existing_data.copy() if existing_data and merge else {}

    if isinstance(field_selector, list):
        main_fields = set(field_selector)
        fields_to_extract = [field for field in validated_data.keys() if field not in main_fields]
    elif callable(field_selector):
        fields_to_extract = [field for field in validated_data.keys() if field_selector(field)]
    else:
        raise ValueError("field_selector must be a list of field names or a callable")

    for field in fields_to_extract:
        value = validated_data.pop(field)
        extracted_data[field] = str(value).strip() if value is not None else ''

    return extracted_data
