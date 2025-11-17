# Noteworthy Differences:
# Classification of noteworthy differences between revisions of Wikipedia articles: an AI alignment project
# 20251114 jmd version 1

from google import genai
from google.genai import types
from pydantic import BaseModel
from dotenv import load_dotenv
import json
import os
import pandas as pd
from prompts import analyzer_prompts, judge_prompt

# Loads GEMINI_API_KEY
load_dotenv(dotenv_path=".env", override=True)

# Initialize the Gemini LLM
client = genai.Client()


def classify(old_revision, new_revision, prompt_style):
    """
    Classify noteworthy differences between revisions of a Wikipedia article

    Args:
        old_revision: Old revision of article
        new_revision: New revision of article

    Returns:
        noteworthy: True if the differences are noteworthy; False if not
        rationale: One-sentence rational for the classification
    """

    # Return None for missing revisions
    if not pd.notna(old_revision) or not pd.notna(new_revision):
        return {"noteworthy": None, "rationale": None}

    # Get prompt template for given style
    prompt_template = analyzer_prompts[prompt_style]

    # Add article revisions to prompt
    prompt = prompt_template.replace("{{old_revision}}", old_revision).replace(
        "{{new_revision}}", new_revision
    )

    # Define response schema
    class Response(BaseModel):
        noteworthy: bool
        rationale: str

    # Generate response
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=Response.model_json_schema(),
        ),
    )

    analysis = json.loads(response.text)

    return analysis


def judge(old_revision, new_revision, rationale_1, rationale_2):
    """
    AI judge to settle disagreements between classifications with different prompts

    Args:
        old_revision: Old revision of article
        new_revision: New revision of article
        rationale_1: Rationale provided by model with prompt 1
        rationale_2: Rationale provided by model with prompt 2

    Returns:
        noteworthy: True if the differences are noteworthy; False if not
        reasoning: One-sentence reason for the decision
    """

    prompt = judge_prompt
    # Add article revisions to prompt
    prompt = prompt.replace("{{old_revision}}", old_revision).replace(
        "{{new_revision}}", new_revision
    )
    # Add rationales to prompt
    prompt = prompt.replace("{{rationale_1}}", rationale_1).replace(
        "{{rationale_2}}", rationale_2
    )

    # Define response schema
    class Response(BaseModel):
        noteworthy: bool
        reasoning: str

    # Generate response
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=Response.model_json_schema(),
        ),
    )

    analysis = json.loads(response.text)

    return analysis
