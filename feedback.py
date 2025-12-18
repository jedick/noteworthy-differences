from huggingface_hub import HfApi, CommitScheduler
from dotenv import load_dotenv
from datetime import datetime
from pathlib import Path
import gradio as gr
import logfire
import json
import os

# Load API keys
load_dotenv()

# Set repo ID for Hugging Face dataset
REPO_ID = "jedick/noteworthy-differences-feedback"
# Setup user feedback file for uploading to HF dataset
# https://huggingface.co/spaces/Wauplin/space_to_dataset_saver
# https://huggingface.co/docs/huggingface_hub/v0.16.3/en/guides/upload#scheduled-uploads
USER_FEEDBACK_DIR = Path("user_feedback")
USER_FEEDBACK_DIR.mkdir(parents=True, exist_ok=True)


if gr.NO_RELOAD:
    # Create dataset if one doesn't exist
    api = HfApi()
    if not api.repo_exists(REPO_ID, repo_type="dataset"):
        api.create_repo(REPO_ID, repo_type="dataset")

    # Initialize commit scheduler if we're running on Hugging Face spaces
    if "SPACE_ID" in os.environ:
        scheduler = CommitScheduler(
            repo_id=REPO_ID,
            repo_type="dataset",
            folder_path=USER_FEEDBACK_DIR,
            path_in_repo="data",
        )


def save_feedback(*args, feedback_value: str) -> None:
    """
    Save complete app state and user feedback to a
    JSON Lines file for upload to a Hugging Face dataset.
    """
    # Assign dict keys to positional arguments
    keys = [
        "title_input",
        "number_input",
        "units_dropdown",
        "judge_mode_dropdown",
        "old_revision",
        "new_revision",
        "old_timestamp",
        "new_timestamp",
        "heuristic_rationale",
        "fewshot_rationale",
        "judge_reasoning",
        "noteworthy_text",
        "confidence",
        "heuristic_noteworthy",
        "fewshot_noteworthy",
        "judge_noteworthy",
    ]
    feedback_dict = dict(zip(keys, args))
    # Add feedback value
    feedback_dict["feedback"] = feedback_value
    # Save feedback to file
    feedback_file = f"train-{datetime.now().isoformat()}.json"
    feedback_path = USER_FEEDBACK_DIR / feedback_file
    with feedback_path.open("a") as f:
        f.write(json.dumps(feedback_dict))
        f.write("\n")
    gr.Success(f"Saved your feedback: {feedback_value}", duration=2, title="Thank you!")


@logfire.instrument("Save feedback: agree")
def save_feedback_agree(*args) -> None:
    """Wrapper to save feedback with 'agree' value."""
    # Schedule feedback for commit if we're running on Hugging Face spaces
    if "SPACE_ID" in os.environ:
        # Use a thread lock to avoid concurrent writes from different users
        with scheduler.lock:
            save_feedback(*args, feedback_value="agree")
    else:
        save_feedback(*args, feedback_value="agree")


@logfire.instrument("Save feedback: disagree")
def save_feedback_disagree(*args) -> None:
    """Wrapper to save feedback with 'disagree' value."""
    if "SPACE_ID" in os.environ:
        with scheduler.lock:
            save_feedback(*args, feedback_value="disagree")
    else:
        save_feedback(*args, feedback_value="disagree")
