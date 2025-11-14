# Diffipedia: Summarize differences between old and new versions of a Wikipedia article
# 20251114 jmd version 1

from google import genai
from google.genai import types
from pydantic import BaseModel
from dotenv import load_dotenv
import json
import os
import prompts

# Loads GEMINI_API_KEY
load_dotenv(dotenv_path=".env", override=True)

# Initialize the Gemini LLM
client = genai.Client()


def analyze(old_version, new_version):
    """
    Analyze differences between versions of a Wikipedia article
    """

    # Create prompt
    analyzer_prompt = prompts.heuristic.replace("{{old_version}}", old_version).replace(
        "{{new_version}}", new_version
    )

    # Response schema
    # https://ai.google.dev/gemini-api/docs/structured-output?example=recipe
    class Response(BaseModel):
        different: bool
        summary: str

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=analyzer_prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=Response.model_json_schema(),
        ),
    )

    return response


def run_analysis(example_number):
    """
    Run the two-stage pipeline for a file with a LinkedIn profile.
    Output the result to a text file in the 'emails' directory
    """

    # Pad example_number, e.g. 1 becomes "01"
    padded_number = str(example_number).zfill(2)

    file_path = os.path.join("data", f"{padded_number}_old.txt")
    with open(file_path, "r") as f:
        old_version = f.read()

    file_path = os.path.join("data", f"{padded_number}_new.txt")
    with open(file_path, "r") as f:
        new_version = f.read()

    response = analyze(old_version, new_version)
    analysis = json.loads(response.text)

    print(f"\n✓ Different: {analysis['different']}")
    print(f"Summary: {analysis['summary']}")
