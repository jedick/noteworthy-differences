from datasets import load_dataset
from google import genai
from dotenv import load_dotenv
from retry_with_backoff import retry_with_backoff
from prompts import update_prompt
from evaluate import select_round
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
def update_alignment(round=None):
    """
    Update the alignment prompt using feedback collect from production app.

    Args:
        round: alignment round, starting with 2 (None uses most recent available round)
    """
    # Load feedback dataset
    dataset = load_dataset("jedick/noteworthy-differences-feedback", split="train")
    # Convert to DataFrame
    df = dataset.to_pandas()
    # Get examples for this round
    # This also gets the number of the most recent round if the argument is None
    index, round = select_round(dataset, "train", round)
    examples = df.iloc[index]
    examples_text = []
    # Loop over rows
    for index, row in examples.iterrows():
        # Construct training text for this row
        ground_truth = "noteworthy=False"
        if row["judge_noteworthy"] and row["feedback"] == "agree":
            ground_truth = "noteworthy=True"
        if not row["judge_noteworthy"] and row["feedback"] == "disagree":
            ground_truth = "noteworthy=True"
        judge = f"AI Judge: {row['judge_reasoning']}"
        human = f"Human feedback: {row['feedback']} ({ground_truth})."
        row_text = f"{judge} {human}"
        examples_text.append(row_text)

    examples_text = "\n\n".join(examples_text)

    # Read the existing alignment
    with open(f"production/alignment_{str(round - 1)}.txt", "r") as file:
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
    with open(f"production/alignment_{str(round)}.txt", "w") as file:
        file.write(response.text)


if __name__ == "__main__":

    update_alignment()
