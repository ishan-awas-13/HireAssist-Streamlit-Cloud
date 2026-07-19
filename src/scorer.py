import json
import os
from openai import OpenAI

from dotenv import load_dotenv
load_dotenv()

def _build_scorer_prompt(eval_factors: list[dict]) -> str:
    """Build a dynamic system prompt from the recruiter's evaluation factors."""
    factor_names   = "\n".join(f"- {f['name']}" for f in eval_factors)
    factor_schema  = "\n".join(
        f'    "{f["name"].lower().replace(" ", "_")}": <integer 1-100>,'
        for f in eval_factors
    )
    return f"""You are an expert technical recruiter and resume evaluator.
You will be given:
1. A job description
2. A list of key skills important for the role
3. A candidate's parsed resume as structured JSON

Evaluate the candidate ONLY on these factors:
{factor_names}

Return ONLY a valid JSON object in this exact schema — no extra text, no markdown:
{{
{factor_schema}
    "summary": "<concise explanation of the scores>"
}}

Rules:
- All keys must use snake_case exactly as shown above.
- Do NOT add any extra keys.
"""

def score_candidate_suitability(
    model_name: str,
    job_description: str,
    key_skills: list[str],
    resume_json: dict,
    eval_factors: list[dict]
) -> dict:
    """
    Evaluate candidate suitability using Hugging Face's Serverless Inference API.
    Scoring factors are driven dynamically by the recruiter's sidebar configuration.
    """
    system_prompt = _build_scorer_prompt(eval_factors)

    prompt = f"""Job Description:
{job_description}

Key Skills:
{', '.join(key_skills)}

Resume JSON:
{json.dumps(resume_json, indent=2)}

Now evaluate how suitable the candidate is for the job role."""

    client = OpenAI(
        base_url="https://router.huggingface.co/v1/",
        api_key=os.environ.get("HF_TOKEN")
    )

    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": prompt}
        ],
        temperature=0.2,
        response_format={"type": "json_object"}
    )
    #Inserting method to catch the scores and make an overalls score via python formula
    llm_scores = json.loads(response.choices[0].message.content)

    #now extract the numbers, LLM will be giving keys and values pairs
    #Inore the "summary" that LLM sends back.
    factor_values=[
        value for key, value in llm_scores.items()
        if isinstance(value, int) # this is to take only stuff that is a number, avoids summary text
    ]
    
    #now we Calculate using the simple average formula
    if factor_values:
        calculated_overall = sum(factor_values) / len(factor_values)
    else:
        calculated_overall = 0
        
    #inject the calculated score into the dictionary
    llm_scores["overall_score"] = int(calculated_overall)
    
    # return the combined result with the calculated overall score
    return llm_scores

def extract_mandatory_skills(model_name: str, job_description: str) -> list[str]:
    """
    Analyze a job description and extract only the mandatory/required skills.
    Returns a clean list of skill strings for recruiter review.
    """
    system_prompt = """You are an expert technical recruiter.
You will be given a job description. Your sole task is to extract ONLY the mandatory and required skills.
- Do NOT include "nice-to-have", "preferred", or "bonus" skills.
- Focus on concrete technical skills, tools, languages, and frameworks, abilities that are listed as requirements.
- Keep each skill concise (1-4 words maximum).

Return ONLY a valid JSON object with no extra text, no markdown, no explanation:
{
    "mandatory_skills": ["skill1", "skill2", "skill3"]
}"""

    client = OpenAI(
        base_url="https://router.huggingface.co/v1/",
        api_key=os.environ.get("HF_TOKEN")
    )

    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": f"Extract absolutely mandatory skills from this job description:\n\n{job_description}"}
        ],
        temperature=0.1,
        response_format={"type": "json_object"}
    )

    result = json.loads(response.choices[0].message.content)
    return result.get("mandatory_skills", [])
