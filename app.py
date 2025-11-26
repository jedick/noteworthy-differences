import gradio as gr
from wiki_data_fetcher import (
    get_previous_revisions,
    get_revision_from_age,
    get_wikipedia_introduction,
    extract_revision_info,
    get_revisions_behind,
    get_random_wikipedia_title,
)
from models import classifier, judge
import logfire
from dotenv import load_dotenv

# Load API keys
load_dotenv()
# Setup logging with Logfire
logfire.configure()

# If running a standalone Gradio app via `demo.launch()` within a script,
# Logfire's auto-instrumentation for FastAPI is often automatically handled
# if installed. If mounting within a separate FastAPI app, use:
# logfire.instrument_fastapi(app)


@logfire.instrument("Step 1: Fetch current revision")
def fetch_current_revision(title: str):
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
        revision_info = extract_revision_info(json_data, revision=0)

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


@logfire.instrument("Step 2: Fetch previous revision")
def fetch_previous_revision(title: str, unit: str, number: int, new_revision: str):
    """
    Fetch previous revision of a Wikipedia article and return its introduction.

    Args:
        title: Wikipedia article title
        unit: "days" or "revisions"
        number: Number of days or revisions behind

    Returns:
        Tuple of (introduction, timestamp)
    """

    # If we get here with an empty new revision, then an error should have been raised
    # in fetch_current_revision, so just return empty values without raising another error
    if not new_revision:
        return None, None

    try:
        # Get previous revision based on unit
        if unit == "revisions":
            json_data = get_previous_revisions(title, revisions=number)
            revision_info = extract_revision_info(json_data, revision=number)
        else:  # unit == "days"
            revision_info = get_revision_from_age(title, age_days=number)

        if not revision_info.get("revid"):
            error_msg = f"Error: Could not find revision {number} {'revisions' if unit == 'revisions' else 'days'} behind for '{title}'."
            raise gr.Error(error_msg, print_exception=False)
            return None, None

        revid = revision_info["revid"]
        timestamp = revision_info["timestamp"]

        # Get introduction
        introduction = get_wikipedia_introduction(revid)

        if introduction is None:
            introduction = f"Error: Could not retrieve introduction for previous revision (revid: {revid})"

        # Get revisions_behind
        if unit == "revisions":
            revisions_behind = number
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


@logfire.instrument("Step 3a: Run heuristic classifier")
def run_heuristic_classifier(old_revision: str, new_revision: str):
    return run_classifier(old_revision, new_revision, prompt_style="heuristic")


@logfire.instrument("Step 3b: Run few-shot classifier")
def run_fewshot_classifier(old_revision: str, new_revision: str):
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


@logfire.instrument("Step 4: Run judge")
def run_judge(
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


# Create Gradio interface
with gr.Blocks(title="Noteworthy Differences") as demo:
    with gr.Row():
        gr.Markdown(
            """
        Compare current and old revisions of a Wikipedia article - you choose the number of days or revisions behind.<br>
        Two classifier models (with heuristic and few-shot prompts) and a judge predict the noteworthiness of the differences.<br>
        The judge was aligned with human preferences as described in the
        [GitHub repository](https://github.com/jedick/noteworthy-differences).
        """
        )

    with gr.Row():
        title_input = gr.Textbox(
            label="Wikipedia Page Title", placeholder="e.g., Albert Einstein", value=""
        )
        number_input = gr.Number(label="Number", value=100, minimum=0, precision=0)
        unit_dropdown = gr.Dropdown(
            choices=["days", "revisions"], value="days", label="Unit"
        )
        judge_mode_dropdown = gr.Dropdown(
            choices=["unaligned", "aligned-fewshot", "aligned-heuristic"],
            value="aligned-heuristic",
            label="Judge Mode",
        )
        with gr.Column():
            random_btn = gr.Button("Get Random Page Title")
            submit_btn = gr.Button("Fetch Revisions and Run Model", variant="primary")

    with gr.Row():
        with gr.Column():
            gr.Markdown("### Old Revision")
            old_timestamp = gr.Markdown("")
            old_revision = gr.Textbox(label="", lines=15, max_lines=30, container=False)
            gr.Markdown(
                """#### Query Instructions
            - Page title is case sensitive; use underscores or spaces
            - Specify any number of days or up to 499 revisions behind
            - Only article introductions are downloaded
            """
            )

        with gr.Column():
            gr.Markdown("### Current Revision")
            new_timestamp = gr.Markdown("")
            new_revision = gr.Textbox(label="", lines=15, max_lines=30, container=False)
            gr.Markdown(
                """#### Confidence Key
                - **High:** heuristic = few-shot, judge agrees
                - **Moderate:** heuristic ≠ few-shot, judge decides
                - **Questionable:** heuristic = few-shot, judge vetoes
                """
            )

        with gr.Column():
            gr.Markdown("### Model Output")
            heuristic_rationale = gr.Textbox(
                label="Heuristic Model's Rationale",
                lines=2,
                max_lines=7,
            )
            fewshot_rationale = gr.Textbox(
                label="Few-shot Model's Rationale",
                lines=2,
                max_lines=7,
            )
            judge_reasoning = gr.Textbox(
                label="Judge's Reasoning",
                lines=2,
                max_lines=7,
            )
            with gr.Row(variant="default"):
                noteworthy_text = gr.Textbox(
                    label="Noteworthy Differences",
                    lines=1,
                    interactive=False,
                )
                confidence = gr.Textbox(
                    label="Confidence",
                    lines=1,
                    interactive=False,
                )
            rerun_btn = gr.Button("Rerun Model")

    # States to store boolean values
    heuristic_noteworthy = gr.State()
    fewshot_noteworthy = gr.State()
    judge_noteworthy = gr.State()

    random_btn.click(
        fn=get_random_wikipedia_title,
        inputs=None,
        outputs=[title_input],
    )

    gr.on(
        # Press Enter in textbox or use button to submit
        triggers=[title_input.submit, submit_btn.click],
        # Clear the new_revision and new_timestamp values before proceeding.
        # The empty values will propagate to the other components (through function return values) if there is an error.
        fn=lambda: (gr.update(value=""), gr.update(value="")),
        inputs=None,
        outputs=[new_revision, new_timestamp],
        api_name=False,
    ).then(
        fn=fetch_current_revision,
        inputs=[title_input],
        outputs=[new_revision, new_timestamp],
        api_name=False,
    ).then(
        fn=fetch_previous_revision,
        inputs=[title_input, unit_dropdown, number_input, new_revision],
        outputs=[old_revision, old_timestamp],
        api_name=False,
    ).then(
        fn=run_heuristic_classifier,
        inputs=[old_revision, new_revision],
        outputs=[heuristic_noteworthy, heuristic_rationale],
        api_name=False,
    ).then(
        fn=run_fewshot_classifier,
        inputs=[old_revision, new_revision],
        outputs=[fewshot_noteworthy, fewshot_rationale],
        api_name=False,
    ).then(
        fn=run_judge,
        inputs=[
            old_revision,
            new_revision,
            heuristic_noteworthy,
            fewshot_noteworthy,
            heuristic_rationale,
            fewshot_rationale,
            judge_mode_dropdown,
        ],
        outputs=[judge_noteworthy, noteworthy_text, judge_reasoning, confidence],
        api_name=False,
    )

    # Rerun model when rerun button is clicked
    gr.on(
        triggers=[rerun_btn.click],
        fn=run_heuristic_classifier,
        inputs=[old_revision, new_revision],
        outputs=[heuristic_noteworthy, heuristic_rationale],
        api_name=False,
    ).then(
        fn=run_fewshot_classifier,
        inputs=[old_revision, new_revision],
        outputs=[fewshot_noteworthy, fewshot_rationale],
        api_name=False,
    ).then(
        fn=run_judge,
        inputs=[
            old_revision,
            new_revision,
            heuristic_noteworthy,
            fewshot_noteworthy,
            heuristic_rationale,
            fewshot_rationale,
            judge_mode_dropdown,
        ],
        outputs=[judge_noteworthy, noteworthy_text, judge_reasoning, confidence],
        api_name=False,
    )

if __name__ == "__main__":

    # Setup theme without background image
    theme = gr.Theme.from_hub("NoCrypt/miku")
    theme.set(body_background_fill="#FFFFFF", body_background_fill_dark="#000000")

    demo.launch(theme=theme)
