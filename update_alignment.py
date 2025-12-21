from datasets import load_dataset
from google import genai
from dotenv import load_dotenv
from retry_with_backoff import retry_with_backoff
from prompts import update_prompt
import logfire

# Load API keys
load_dotenv()

# This wraps Google Gen AI client calls
# to capture prompts, responses, and metadata
logfire.configure()
logfire.instrument_google_genai()

# Initialize the Gemini LLM
client = genai.Client()


@logfire.instrument("Update alignment")
def update_alignment():
    # Load feedback dataset
    dataset = load_dataset("jedick/noteworthy-differences-feedback")
    # Convert to DataFrame
    df = dataset["train"].to_pandas()
    # Remove samples with High confidence where feedback is "agree"
    high_and_agree = (df["confidence_score"] == "High") & (df["feedback"] == "agree")
    df = df.loc[~high_and_agree]
    # Get 30 examples for training the LLM
    examples = df[df.confidence_score != "High"].iloc[:30, :]
    examples_text = []
    # Loop over rows
    for index, row in df.iterrows():
        # Construct training text for this row
        noteworthy = "not noteworthy differences"
        if row["judge_noteworthy"] and row["feedback"] == "agree":
            noteworthy = "noteworthy differences"
        if not row["judge_noteworthy"] and row["feedback"] == "disagree":
            noteworthy = "noteworthy differences"
        heuristic = f"Model 1: {row['heuristic_rationale']}"
        fewshot = f"Model 2: {row['fewshot_rationale']}"
        judge = f"AI Judge: {row['judge_reasoning']}"
        human = f"Human feedback: {row['feedback']}"
        row_text = f"{heuristic}\n{fewshot}\n{judge}\n{human} ({noteworthy})."
        examples_text.append(row_text)

    examples_text = "\n\n".join(examples_text)

    # Read the existing alignment
    with open("production/alignment_1.txt", "r") as file:
        lines = file.readlines()
        alignment_text = "".join(lines)

    # Write prompt to update alignment
    prompt = update_prompt.replace("{{alignment_text}}", alignment_text).replace(
        "{{examples_text}}", examples_text
    )

    # Function to generate response
    @retry_with_backoff()
    def get_response():
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        return response

    # Get the response
    response = get_response()
    # Save to new alignment text file
    with open("production/alignment_2.txt", "w") as file:
        file.write(response.text)


if __name__ == "__main__":

    update_alignment()
