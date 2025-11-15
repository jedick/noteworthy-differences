# Diffipedia: Summarize differences between old and new versions of a Wikipedia article
# 20251114 jmd version 1

from google import genai
from google.genai import types
from pydantic import BaseModel
from dotenv import load_dotenv
import json
import os
from prompts import analyzer_prompts

# Loads GEMINI_API_KEY
load_dotenv(dotenv_path=".env", override=True)

# Initialize the Gemini LLM
client = genai.Client()


def analyze(old_version, new_version, prompt_style):
    """
    Analyze differences between versions of a Wikipedia article
    """

    # Get prompt template for given style
    prompt_template = analyzer_prompts[prompt_style]

    # Add article versions to prompt
    prompt = prompt_template.replace("{{old_version}}", old_version).replace(
        "{{new_version}}", new_version
    )

    # Define response schema
    class Response(BaseModel):
        different: bool
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

    return response


def run_analysis(example_number):
    """
    Run the model using two prompt styles for a given example in the 'data' directory.
    Print the results to the console.
    """

    # Pad example_number, e.g. 1 becomes "01"
    padded_number = str(example_number).zfill(2)

    file_path = os.path.join("data", f"{padded_number}_old.txt")
    with open(file_path, "r") as f:
        old_version = f.read()

    file_path = os.path.join("data", f"{padded_number}_new.txt")
    with open(file_path, "r") as f:
        new_version = f.read()

    # Loop over prompt styles
    prompt_styles = ["heuristic", "few-shot"]
    for prompt_style in prompt_styles:

        print(f"Prompt style: {prompt_style}")
        response = analyze(old_version, new_version, prompt_style)
        analysis = json.loads(response.text)

        if analysis["different"]:
            print(f"✓ Noteworthy Differences: True")
        else:
            print(f"✗ Noteworthy Differences: False")
        print(f"{analysis['rationale']}\n")
