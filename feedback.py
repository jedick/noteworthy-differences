from huggingface_hub import HfApi, CommitScheduler
from dotenv import load_dotenv
from datetime import datetime
from pathlib import Path
import gradio as gr
import logfire
import json
import os
import re
import random

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
        "page_title",
        "number_behind",
        "units_behind",
        "old_timestamp",
        "new_timestamp",
        "old_revision",
        "new_revision",
        "heuristic_rationale",
        "fewshot_rationale",
        "judge_reasoning",
        "heuristic_noteworthy",
        "fewshot_noteworthy",
        "judge_noteworthy",
        "confidence_score",
    ]
    feedback_dict = dict(zip(keys, args))

    # Data cleanup
    # Split dictionary in two
    keys_start = {"page_title", "number_behind", "units_behind"}
    dict_start = {k: v for k, v in feedback_dict.items() if k in keys_start}
    dict_end = {k: v for k, v in feedback_dict.items() if k not in keys_start}
    # Normalize timestamp and extract revisions behind from display string
    raw_new_timestamp = dict_end.get("new_timestamp", "")
    # Extract ISO timestamp (e.g. 2013-12-09T04:48:24Z)
    ts_match = re.search(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", raw_new_timestamp)
    if ts_match:
        dict_end["new_timestamp"] = ts_match.group(0)
    # Do the same for old timestamp
    raw_old_timestamp = dict_end.get("old_timestamp", "")
    ts_match = re.search(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", raw_old_timestamp)
    if ts_match:
        dict_end["old_timestamp"] = ts_match.group(0)
    # Extract revisions behind (e.g. "35 revisions behind")
    rev_match = re.search(r"(\d+)\s+revisions?\s+behind", raw_old_timestamp)
    if rev_match:
        dict_start["revisions_behind"] = int(rev_match.group(1))
    else:
        dict_start["revisions_behind"] = None
    # Merge the start and end dictionaries
    feedback_dict = dict_start | dict_end

    # Add feedback value
    feedback_dict["feedback"] = feedback_value
    do_save = True
    feedback_action = "Saved"

    # Check for duplicate feedback against the most recent feedback file
    feedback_files = sorted(
        USER_FEEDBACK_DIR.glob("*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if feedback_files:
        latest_feedback_path = feedback_files[0]
        with latest_feedback_path.open("r") as latest_f:
            # Files are written as JSON Lines, but currently contain a single line
            latest_line = latest_f.readline().strip()
            if latest_line:
                latest_feedback = json.loads(latest_line)
                # Pop the last feedback value
                old_feedback = latest_feedback.pop("feedback", None)
                # Use the same feedback value (for detecting resubmission)
                latest_feedback["feedback"] = feedback_value
                if latest_feedback == feedback_dict:
                    # The user resubmitted feedback: remove the previous feedback
                    latest_feedback_path.unlink()
                    if feedback_dict["feedback"] == old_feedback:
                        # The user submitted the same feedback: Issue a warning
                        gr.Warning(
                            f"Removed feedback: <strong>{old_feedback}</strong>",
                            duration=5,
                        )
                        do_save = False
                    else:
                        # The user changed the feedback: Proceed to update the feedback
                        feedback_action = "Updated"

    if do_save:
        # Randomly assign to train or test split (40% probability for test)
        split = "test" if random.random() < 0.4 else "train"
        # Save feedback to file
        feedback_file = f"{split}-{datetime.now().isoformat()}.json"
        feedback_path = USER_FEEDBACK_DIR / feedback_file
        with feedback_path.open("a") as f:
            f.write(json.dumps(feedback_dict))
            f.write("\n")
        if feedback_action == "Updated":
            gr.Info(f"Updated feedback: <strong>{feedback_value}</strong>", duration=5)
        else:
            gr.Success(f"Saved feedback: <strong>{feedback_value}</strong>", duration=5)


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
