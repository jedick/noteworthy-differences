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
from retry_with_backoff import retry_with_backoff
import logfire

# Load API keys
load_dotenv()

# This wraps Google Gen AI client calls
# to capture prompts, responses, and metadata
logfire.instrument_google_genai()

# Initialize the Gemini LLM
client = genai.Client()


@retry_with_backoff()
def classifier(old_revision, new_revision, prompt_style):
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

    return json.loads(response.text)


@retry_with_backoff()
def judge(old_revision, new_revision, rationale_1, rationale_2, mode="unaligned"):
    """
    AI judge to settle disagreements between classification models

    Args:
        old_revision: Old revision of article
        new_revision: New revision of article
        rationale_1: Rationale provided by model 1 (i.e., heuristic prompt)
        rationale_2: Rationale provided by model 2 (i.e., few-shot prompt)
        mode: Prompt mode: unaligned, aligned-fewshot, or aligned-heuristic

    Returns:
        noteworthy: True if the differences are noteworthy; False if not
        reasoning: One-sentence reason for the judgment
    """

    prompt = judge_prompt
    # Add article revisions to prompt
    prompt = prompt.replace("{{old_revision}}", old_revision).replace(
        "{{new_revision}}", new_revision
    )
    # Add rationales to prompt
    prompt = prompt.replace("{{model_1_rationale}}", rationale_1).replace(
        "{{model_2_rationale}}", rationale_2
    )

    # Optionally add alignment text to prompt
    if mode == "unaligned":
        alignment_text = ""
    elif mode == "aligned-fewshot":
        with open("development/alignment_fewshot.txt", "r") as file:
            lines = file.readlines()
            alignment_text = "".join(lines)
    elif mode == "aligned-heuristic":
        with open("development/alignment_heuristic.txt", "r") as file:
            lines = file.readlines()
            alignment_text = "".join(lines)
    else:
        raise ValueError(f"Unknown mode: {mode}")

    prompt = prompt.replace("{{alignment_text}}", alignment_text)

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

    return json.loads(response.text)
