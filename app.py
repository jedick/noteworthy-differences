import gradio as gr
from wiki_data_fetcher import (
    get_previous_revisions,
    get_revision_from_age,
    get_wikipedia_introduction,
    extract_revision_info,
    get_revisions_behind,
    get_random_wikipedia_title,
)
from feedback import save_feedback_agree, save_feedback_disagree
from models import classifier, judge
from contextlib import nullcontext
from dotenv import load_dotenv
import logfire
import os

# Load API keys
load_dotenv()
# Setup logging with Logfire
logfire.configure(service_name="app")


def start_parent_span(title: str, number: int, units: str):
    """
    Start a parent span and return the context for propagation to children.
    See https://logfire.pydantic.dev/docs/how-to-guides/distributed-tracing/#manual-context-propagation
    """
    span_name = f"{title} - {number} {units}"
    with logfire.span(span_name) as span:
        span.__enter__()
        context = logfire.get_context()
    return context


def fetch_current_revision(title: str, context=None):
    """
    Wrapper to run _fetch_current_revision in provided Logfire context.
    We use this to minimize indentation in the wrapped function.
    """
    with logfire.attach_context(context) if context else nullcontext():
        return _fetch_current_revision(title)


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


def fetch_previous_revision(
    title: str, number: int, units: str, new_revision: str, context=None
):
    with logfire.attach_context(context) if context else nullcontext():
        return _fetch_previous_revision(title, number, units, new_revision)


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


def run_heuristic_classifier(old_revision: str, new_revision: str, context=None):
    with logfire.attach_context(context) if context else nullcontext():
        return _run_heuristic_classifier(old_revision, new_revision)


@logfire.instrument("Run heuristic classifier")
def _run_heuristic_classifier(old_revision: str, new_revision: str):
    return run_classifier(old_revision, new_revision, prompt_style="heuristic")


def run_fewshot_classifier(old_revision: str, new_revision: str, context=None):
    with logfire.attach_context(context) if context else nullcontext():
        return _run_fewshot_classifier(old_revision, new_revision)


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


def run_judge(
    old_revision: str,
    new_revision: str,
    heuristic_noteworthy: bool,
    fewshot_noteworthy: bool,
    heuristic_rationale: str,
    fewshot_rationale: str,
    judge_mode: str,
    context=None,
):
    with logfire.attach_context(context) if context else nullcontext():
        return _run_judge(
            old_revision,
            new_revision,
            heuristic_noteworthy,
            heuristic_noteworthy,
            heuristic_rationale,
            fewshot_rationale,
            judge_mode,
        )


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
        Compare current and old revisions of a Wikipedia article - you choose the number of revisions or days behind.<br>
        Two classifier models (with heuristic and few-shot prompts) and a judge predict the noteworthiness of the differences.<br>
        The judge was aligned with human preferences as described in the
        [GitHub repository](https://github.com/jedick/noteworthy-differences).
        """
        )

    with gr.Row():
        title_input = gr.Textbox(
            label="Wikipedia Page Title", placeholder="e.g., Albert Einstein", value=""
        )
        number_input = gr.Number(label="Number", value=50, minimum=0, precision=0)
        units_dropdown = gr.Dropdown(
            choices=["revisions", "days"], value="revisions", label="Unit"
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
              - The closest available revision is retrieved
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

            gr.Markdown("### Your feedback")
            feedback_status = gr.Textbox(
                label="",
                lines=1,
                interactive=False,
                visible=True,
            )
            with gr.Row():
                thumbs_up_btn = gr.Button("👍 Agree", variant="primary")
                thumbs_down_btn = gr.Button("👎 Disagree", variant="secondary")

    # States to store boolean values
    heuristic_noteworthy = gr.State()
    fewshot_noteworthy = gr.State()
    judge_noteworthy = gr.State()
    # State to store Logfire context
    context = gr.State()

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
        # Initialize Logfire context
        fn=start_parent_span,
        inputs=[title_input, number_input, units_dropdown],
        outputs=context,
    ).then(
        fn=fetch_current_revision,
        inputs=[title_input, context],
        outputs=[new_revision, new_timestamp],
        api_name=False,
    ).then(
        fn=fetch_previous_revision,
        inputs=[title_input, number_input, units_dropdown, new_revision, context],
        outputs=[old_revision, old_timestamp],
        api_name=False,
    ).then(
        fn=run_heuristic_classifier,
        inputs=[old_revision, new_revision, context],
        outputs=[heuristic_noteworthy, heuristic_rationale],
        api_name=False,
    ).then(
        fn=run_fewshot_classifier,
        inputs=[old_revision, new_revision, context],
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
            context,
        ],
        outputs=[judge_noteworthy, noteworthy_text, judge_reasoning, confidence],
        api_name=False,
    )

    # Rerun model when rerun button is clicked
    gr.on(
        triggers=[rerun_btn.click],
        fn=run_heuristic_classifier,
        inputs=[old_revision, new_revision, context],
        outputs=[heuristic_noteworthy, heuristic_rationale],
        api_name=False,
    ).then(
        fn=run_fewshot_classifier,
        inputs=[old_revision, new_revision, context],
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
            context,
        ],
        outputs=[judge_noteworthy, noteworthy_text, judge_reasoning, confidence],
        api_name=False,
    )

    # Feedback button handlers
    thumbs_up_btn.click(
        fn=save_feedback_agree,
        inputs=[
            title_input,
            number_input,
            units_dropdown,
            judge_mode_dropdown,
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
        ],
        outputs=[feedback_status],
        api_name=False,
    )

    thumbs_down_btn.click(
        fn=save_feedback_disagree,
        inputs=[
            title_input,
            number_input,
            units_dropdown,
            judge_mode_dropdown,
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
        ],
        outputs=[feedback_status],
        api_name=False,
    )

if __name__ == "__main__":

    # Setup theme without background image
    theme = gr.Theme.from_hub("NoCrypt/miku")
    theme.set(body_background_fill="#FFFFFF", body_background_fill_dark="#000000")

    demo.launch(theme=theme)
