from wiki_data_fetcher import (
    get_previous_revisions,
    get_revision_from_age,
    get_wikipedia_introduction,
    extract_revision_info,
    get_revisions_behind,
)
from models import classifier, judge
import gradio as gr
import logfire


@logfire.instrument("Fetch current revision")
def _fetch_current_revision(title: str):
    """
    Fetch current revision of a Wikipedia article and return its introduction.

    Args:
        title: Wikipedia article title

    Returns:
        Tuple of (introduction, timestamp)
    """
    if not title or not title.strip():
        error_msg = "Please enter a Wikipedia page title."
        raise gr.Error(error_msg, print_exception=False)
        return None, None

    try:
        # Get current revision (revision 0)
        json_data = get_previous_revisions(title, revisions=0)
        revision_info = extract_revision_info(json_data, revnum=0)

        if not revision_info.get("revid"):
            error_msg = f"Error: Could not find Wikipedia page '{title}'. Please check the title."
            raise gr.Error(error_msg, print_exception=False)
            return None, None

        revid = revision_info["revid"]
        timestamp = revision_info["timestamp"]

        # Get introduction
        introduction = get_wikipedia_introduction(revid)

        if introduction is None:
            introduction = f"Error: Could not retrieve introduction for current revision (revid: {revid})"

        # Format timestamp for display
        timestamp = f"**Timestamp:** {timestamp}" if timestamp else ""

        # Return introduction text and timestamp
        return introduction, timestamp

    except Exception as e:
        error_msg = f"Error occurred: {str(e)}"
        raise gr.Error(error_msg, print_exception=False)
        return None, None


@logfire.instrument("Fetch previous revision")
def _fetch_previous_revision(title: str, number: int, units: str, new_revision: str):
    """
    Fetch previous revision of a Wikipedia article and return its introduction.

    Args:
        title: Wikipedia article title
        number: Number of revisions or days behind
        units: "revisions" or "days"

    Returns:
        Tuple of (introduction, timestamp)
    """

    # If we get here with an empty new revision, then an error should have been raised
    # in fetch_current_revision, so just return empty values without raising another error
    if not new_revision:
        return None, None

    try:
        # Get previous revision based on units
        if units == "revisions":
            json_data = get_previous_revisions(title, revisions=number)
            revision_info = extract_revision_info(json_data, revnum=number)
        else:  # units == "days"
            revision_info = get_revision_from_age(title, age_days=number)

        if not revision_info.get("revid"):
            error_msg = f"Error: Could not find revision {number} {'revisions' if units == 'revisions' else 'days'} behind for '{title}'."
            raise gr.Error(error_msg, print_exception=False)
            return None, None

        revid = revision_info["revid"]
        timestamp = revision_info["timestamp"]

        # Get introduction
        introduction = get_wikipedia_introduction(revid)

        if introduction is None:
            introduction = f"Error: Could not retrieve introduction for previous revision (revid: {revid})"

        # Get revisions_behind
        if units == "revisions":
            revisions_behind = revision_info["revnum"]
        else:
            revisions_behind = get_revisions_behind(title, revid)
            # For a negative number, replace the negative sign with ">"
            if revisions_behind < 0:
                revisions_behind = str(revisions_behind).replace("-", ">")

        # Format timestamp for display
        timestamp = (
            f"**Timestamp:** {timestamp}, {revisions_behind} revisions behind"
            if timestamp
            else ""
        )

        # Return introduction text and timestamp
        return introduction, timestamp

    except Exception as e:
        error_msg = f"Error occurred: {str(e)}"
        raise gr.Error(error_msg, print_exception=False)
        return None, None


def run_classifier(old_revision: str, new_revision: str, prompt_style: str):
    """
    Run a classification model on the revisions.

    Args:
        old_revision: Old revision text
        new_revision: New revision text
        prompt_style: heuristic or few-shot

    Returns:
        Tuple of (noteworthy, rationale) (bool, str)
    """

    # Values to return if there is an error
    noteworthy, rationale = None, None
    if not old_revision or not new_revision:
        return noteworthy, rationale

    try:
        # Run classifier model
        result = classifier(old_revision, new_revision, prompt_style=prompt_style)
        if result:
            noteworthy = result.get("noteworthy", None)
            rationale = result.get("rationale", "")
        else:
            error_msg = f"Error: Could not get {prompt_style} model result"
            raise gr.Error(error_msg, print_exception=False)

    except Exception as e:
        error_msg = f"Error running model: {str(e)}"
        raise gr.Error(error_msg, print_exception=False)

    return noteworthy, rationale


@logfire.instrument("Run heuristic classifier")
def _run_heuristic_classifier(old_revision: str, new_revision: str):
    return run_classifier(old_revision, new_revision, prompt_style="heuristic")


@logfire.instrument("Run few-shot classifier")
def _run_fewshot_classifier(old_revision: str, new_revision: str):
    return run_classifier(old_revision, new_revision, prompt_style="few-shot")


def compute_confidence(
    heuristic_noteworthy,
    fewshot_noteworthy,
    judge_noteworthy,
    heuristic_rationale,
    fewshot_rationale,
    judge_reasoning,
):
    """
    Compute a confidence label using the noteworthy booleans.
    """
    # Return None if any of the rationales or reasoning is missing.
    if not heuristic_rationale or not fewshot_rationale or not judge_reasoning:
        return None
    if heuristic_noteworthy == fewshot_noteworthy == judge_noteworthy:
        # Classifiers and judge all agree
        return "High"
    elif heuristic_noteworthy != fewshot_noteworthy:
        # Classifiers disagree, judge decides
        return "Moderate"
    else:
        # Classifiers agree, judge vetoes
        return "Questionable"


@logfire.instrument("Run judge")
def _run_judge(
    old_revision: str,
    new_revision: str,
    heuristic_noteworthy: bool,
    fewshot_noteworthy: bool,
    heuristic_rationale: str,
    fewshot_rationale: str,
    judge_mode: str,
):
    """
    Run judge on the revisions and classifiers' rationales.

    Args:
        old_revision: Old revision text
        new_revision: New revision text
        heuristic_noteworthy: Heuristic model's noteworthiness prediction
        fewshot_noteworthy: Few-shot model's noteworthiness prediction
        heuristic_rationale: Heuristic model's rationale
        fewshot_rationale: Few-shot model's rationale
        judge_mode: Mode for judge function ("unaligned", "aligned-fewshot", "aligned-heuristic")

    Returns:
        Tuple of (noteworthy, noteworthy_text, reasoning, confidence) (bool, str, str, str)
    """

    # Values to return if there is an error
    noteworthy, noteworthy_text, reasoning, confidence = None, None, None, None
    if (
        not old_revision
        or not new_revision
        or not heuristic_rationale
        or not fewshot_rationale
    ):
        return noteworthy, noteworthy_text, reasoning, confidence

    try:
        # Run judge
        result = judge(
            old_revision,
            new_revision,
            heuristic_rationale,
            fewshot_rationale,
            mode=judge_mode,
        )
        if result:
            noteworthy = result.get("noteworthy", "")
            reasoning = result.get("reasoning", "")
        else:
            error_msg = f"Error: Could not get judge's result"
            raise gr.Error(error_msg, print_exception=False)

    except Exception as e:
        error_msg = f"Error running judge: {str(e)}"
        raise gr.Error(error_msg, print_exception=False)

    # Format noteworthy label (boolean) as text
    if not reasoning:
        noteworthy_text = None
    else:
        noteworthy_text = str(noteworthy)

    # Get confidence score
    confidence = compute_confidence(
        heuristic_noteworthy,
        fewshot_noteworthy,
        noteworthy,
        heuristic_rationale,
        fewshot_rationale,
        reasoning,
    )

    return noteworthy, noteworthy_text, reasoning, confidence
