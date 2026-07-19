import json
import os
from openai import OpenAI
from schema import ResumeParserResponse

#This is for local machine to talk to Ollama online
from dotenv import load_dotenv
load_dotenv()

PYDANTIC_SCHEMA = ResumeParserResponse.model_json_schema()
current_dir = os.path.dirname(os.path.abspath(__file__))
schema_path = os.path.join(current_dir, "JSON_Scheme.json")

try:
    with open(schema_path, "r") as f:
        example_template = f.read()
except Exception:
    example_template = json.dumps({"candidate_profile": {}}, indent=2)

SYSTEM_PROMPT = f"""You are a precise, deterministic AI data extraction engine.
Your ONLY task is to extract candidate information from an unstructured resume into
a strictly structured JSON object.

## REQUIRED OUTPUT STRUCTURE:
{example_template}

## STRICT RULES:
1. Output ONLY a valid raw JSON object. No markdown fences, no explanations, no extra text.
2. ALL JSON keys MUST use snake_case exactly as shown above (e.g., "first_name" NOT "firstName").
3. The top-level key MUST be "candidate_profile".
4. If a field cannot be found in the resume, use null for string fields and [] for list fields.
5. Date formats: use the format found in the resume (e.g., "2024-06" or "June 2024").
6. Do NOT invent, infer, or guess any data not explicitly present in the resume.
7. Do NOT add any fields not present in the schema above.
"""

def parse_resume_text(model_name: str, raw_text: str) -> ResumeParserResponse:
    # Using the modern Hugging Face Inference Router
    client = OpenAI(
        base_url="https://router.huggingface.co/v1",
        api_key=os.environ.get("HF_TOKEN", "mock_key")
    )

    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Extract the following resume:\n\n{raw_text}"}
        ],
        temperature=0.1,
        response_format={
            "type": "json_object",
            "schema": PYDANTIC_SCHEMA
        }
    )

    raw_json_str = response.choices[0].message.content

    try:
        validated_data = ResumeParserResponse.model_validate_json(raw_json_str)
        return validated_data
    except Exception as e:
        raise ValueError(f"Failed to validate JSON: {e}")