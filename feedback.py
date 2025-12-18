from datasets import Dataset, load_dataset
from huggingface_hub import login
from dotenv import load_dotenv
import logfire


def save_feedback(
    title: str,
    number: int,
    units: str,
    judge_mode: str,
    old_revision: str,
    new_revision: str,
    old_timestamp: str,
    new_timestamp: str,
    heuristic_rationale: str,
    fewshot_rationale: str,
    judge_reasoning: str,
    noteworthy_text: str,
    confidence: str,
    heuristic_noteworthy: bool,
    fewshot_noteworthy: bool,
    judge_noteworthy: bool,
    feedback_value: str,  # "agree" or "disagree"
):
    """
    Save complete app state to Hugging Face dataset.

    Args:
        title: Wikipedia page title
        number: Number of revisions or days
        units: "revisions" or "days"
        judge_mode: Judge mode setting
        old_revision: Old revision text
        new_revision: New revision text
        old_timestamp: Old revision timestamp
        new_timestamp: New revision timestamp
        heuristic_rationale: Heuristic model rationale
        fewshot_rationale: Few-shot model rationale
        judge_reasoning: Judge's reasoning
        noteworthy_text: Noteworthy differences classification
        confidence: Confidence level
        heuristic_noteworthy: Heuristic model noteworthy boolean
        fewshot_noteworthy: Few-shot model noteworthy boolean
        judge_noteworthy: Judge noteworthy boolean
        feedback_value: "agree" or "disagree"

    Returns:
        Success message
    """
    try:
        # Prepare data dictionary with all app state
        new_row = {
            "page_title": title or "",
            "number": number if number is not None else 0,
            "units": units or "",
            "judge_mode": judge_mode or "",
            "old_revision": old_revision or "",
            "new_revision": new_revision or "",
            "old_timestamp": old_timestamp or "",
            "new_timestamp": new_timestamp or "",
            "heuristic_rationale": heuristic_rationale or "",
            "fewshot_rationale": fewshot_rationale or "",
            "judge_reasoning": judge_reasoning or "",
            "noteworthy_differences": noteworthy_text or "",
            "confidence": confidence or "",
            "heuristic_noteworthy": (
                bool(heuristic_noteworthy) if heuristic_noteworthy is not None else None
            ),
            "fewshot_noteworthy": (
                bool(fewshot_noteworthy) if fewshot_noteworthy is not None else None
            ),
            "judge_noteworthy": (
                bool(judge_noteworthy) if judge_noteworthy is not None else None
            ),
            "feedback": feedback_value,
        }

        dataset_name = "noteworthy-differences-feedback"

        # Try to load existing dataset, create new one if it doesn't exist
        try:
            existing_dataset = load_dataset(dataset_name, split="train")
            # Convert to list of dicts, append new row, create new dataset
            existing_data = existing_dataset.to_list()
            existing_data.append(new_row)
            dataset = Dataset.from_list(existing_data)
        except Exception:
            # Dataset doesn't exist, create new one
            dataset = Dataset.from_dict({k: [v] for k, v in new_row.items()})

        # Push to Hugging Face Hub
        dataset.push_to_hub(dataset_name, private=True)

        return f"Feedback ({feedback_value}) saved successfully!"

    except Exception as e:
        error_msg = f"Error saving feedback: {str(e)}"
        raise gr.Error(error_msg, print_exception=False)
        return "Error saving feedback"


@logfire.instrument("Save feedback: agree")
def save_feedback_agree(
    title: str,
    number: int,
    units: str,
    judge_mode: str,
    old_revision: str,
    new_revision: str,
    old_timestamp: str,
    new_timestamp: str,
    heuristic_rationale: str,
    fewshot_rationale: str,
    judge_reasoning: str,
    noteworthy_text: str,
    confidence: str,
    heuristic_noteworthy: bool,
    fewshot_noteworthy: bool,
    judge_noteworthy: bool,
):
    """Wrapper to save feedback with 'agree' value."""
    return save_feedback(
        title,
        number,
        units,
        judge_mode,
        old_revision,
        new_revision,
        old_timestamp,
        new_timestamp,
        heuristic_rationale,
        fewshot_rationale,
        judge_reasoning,
        noteworthy_text,
        confidence,
        heuristic_noteworthy,
        fewshot_noteworthy,
        judge_noteworthy,
        "agree",
    )


@logfire.instrument("Save feedback: disagree")
def save_feedback_disagree(
    title: str,
    number: int,
    units: str,
    judge_mode: str,
    old_revision: str,
    new_revision: str,
    old_timestamp: str,
    new_timestamp: str,
    heuristic_rationale: str,
    fewshot_rationale: str,
    judge_reasoning: str,
    noteworthy_text: str,
    confidence: str,
    heuristic_noteworthy: bool,
    fewshot_noteworthy: bool,
    judge_noteworthy: bool,
):
    """Wrapper to save feedback with 'disagree' value."""
    return save_feedback(
        title,
        number,
        units,
        judge_mode,
        old_revision,
        new_revision,
        old_timestamp,
        new_timestamp,
        heuristic_rationale,
        fewshot_rationale,
        judge_reasoning,
        noteworthy_text,
        confidence,
        heuristic_noteworthy,
        fewshot_noteworthy,
        judge_noteworthy,
        "disagree",
    )
