import gradio as gr
from wiki_data_fetcher import get_random_wikipedia_title
from feedback import save_feedback_agree, save_feedback_disagree
from contextlib import nullcontext
from dotenv import load_dotenv
import logfire
import os

# Load API keys
load_dotenv()
# Setup logging with Logfire
logfire.configure()

# This goes after logfire.configure() to avoid
# LogfireNotConfiguredWarning: Instrumentation will have no effect
from app_functions import (
    _fetch_current_revision,
    _fetch_previous_revision,
    _run_heuristic_classifier,
    _run_fewshot_classifier,
    _run_judge,
)


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
    We use a wrapper to minimize indentation in the called function.
    """
    with logfire.attach_context(context) if context else nullcontext():
        return _fetch_current_revision(title)


def fetch_previous_revision(
    title: str, number: int, units: str, new_revision: str, context=None
):
    with logfire.attach_context(context) if context else nullcontext():
        return _fetch_previous_revision(title, number, units, new_revision)


def run_heuristic_classifier(old_revision: str, new_revision: str, context=None):
    with logfire.attach_context(context) if context else nullcontext():
        return _run_heuristic_classifier(old_revision, new_revision)


def run_fewshot_classifier(old_revision: str, new_revision: str, context=None):
    with logfire.attach_context(context) if context else nullcontext():
        return _run_fewshot_classifier(old_revision, new_revision)


def run_judge(
    old_revision: str,
    new_revision: str,
    heuristic_noteworthy: bool,
    fewshot_noteworthy: bool,
    heuristic_rationale: str,
    fewshot_rationale: str,
    context=None,
):
    with logfire.attach_context(context) if context else nullcontext():
        return _run_judge(
            old_revision,
            new_revision,
            heuristic_noteworthy,
            fewshot_noteworthy,
            heuristic_rationale,
            fewshot_rationale,
        )


# Create Gradio interface
with gr.Blocks(title="Noteworthy Differences") as demo:
    with gr.Row():
        gr.Markdown(
            """
        <table>
          <colgroup>
            <col span="1" style="width: 30%;">
            <col span="1" style="width: 25%;">
            <col span="1" style="width: 45%;">
          </colgroup>
          <tr>
            <td>
              <i class="fa-brands fa-wikipedia-w"></i> Compare current and old revisions of a Wikipedia article.<br>
              📅 You choose the number of revisions or days behind.
            </td>
            <td>
              ◇ ∴ ⚖ Two classifier models and a judge predict the noteworthiness of the differences.
            </td>
            <td>
              <i class="fa-brands fa-github"></i> The <a href="https://github.com/jedick/noteworthy-differences">GitHub repository</a> describes how the judge was aligned with human preferences.<br>
              👥 The <a href="https://huggingface.co/datasets/jedick/noteworthy-differences-feedback">feedback dataset</a> holds all user feedback collected to date.
              </td>
          </tr>
        </table>

        """,
            elem_id="intro-table",
        )

    with gr.Row():
        with gr.Column(scale=1):
            with gr.Accordion("Query Instructions", open=False) as accordion:
                gr.Markdown(
                    """
                - Page title is case sensitive; use underscores or spaces
                - Specify any number of days or up to 499 revisions behind
                  - The closest available revision is retrieved
                - Only article introductions are downloaded
                """
                )
            with gr.Accordion("Confidence Scores", open=False) as accordion:
                gr.Markdown(
                    """
                    - **High:** heuristic = few-shot, judge agrees
                    - **Moderate:** heuristic ≠ few-shot, judge decides
                    - **Questionable:** heuristic = few-shot, judge vetoes
                    """
                )
        with gr.Column(scale=3):
            with gr.Row():
                page_title = gr.Textbox(
                    label="Wikipedia Page Title",
                    placeholder="e.g., Albert Einstein",
                    value="",
                )
                number_behind = gr.Number(
                    label="Number", value=50, minimum=0, precision=0
                )
                units_behind = gr.Dropdown(
                    choices=["revisions", "days"], value="revisions", label="Units"
                )
        with gr.Column(scale=1):
            random_btn = gr.Button("Get Random Page Title", size="md")
            submit_btn = gr.Button(
                "Fetch Revisions and Run Model", size="md", variant="primary"
            )
            rerun_btn = gr.Button("Rerun Model", size="md")

    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### Old Revision")
            old_timestamp = gr.Markdown("")
            old_revision = gr.Textbox(label="", lines=15, max_lines=30, container=False)

        with gr.Column(scale=1):
            gr.Markdown("### Current Revision")
            new_timestamp = gr.Markdown("")
            new_revision = gr.Textbox(label="", lines=15, max_lines=30, container=False)

        with gr.Column(scale=2):
            gr.Markdown("### Model Output")
            with gr.Row():
                with gr.Column():
                    heuristic_rationale = gr.Textbox(
                        label="◇ Heuristic Model's Rationale",
                        lines=2,
                        max_lines=7,
                    )
                    fewshot_rationale = gr.Textbox(
                        label="∴ Few-shot Model's Rationale",
                        lines=2,
                        max_lines=7,
                    )
                    judge_reasoning = gr.Textbox(
                        label="⚖ Judge's Reasoning",
                        lines=2,
                        max_lines=7,
                    )

                with gr.Column():
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

                    gr.Markdown("### 👥 Your feedback")
                    with gr.Row():
                        thumbs_up_btn = gr.Button(
                            "👍 Agree", size="md", variant="primary"
                        )
                        thumbs_down_btn = gr.Button(
                            "👎 Disagree", size="md", variant="primary"
                        )

    # States to store boolean values
    heuristic_noteworthy = gr.State()
    fewshot_noteworthy = gr.State()
    judge_noteworthy = gr.State()
    # State to store Logfire context
    context = gr.State()

    random_btn.click(
        fn=get_random_wikipedia_title,
        inputs=None,
        outputs=[page_title],
    )

    gr.on(
        # Press Enter in textbox or use button to submit
        triggers=[page_title.submit, submit_btn.click],
        # Clear the new_revision and new_timestamp values before proceeding.
        # The empty values will propagate to the other components (through function return values) if there is an error.
        fn=lambda: (gr.update(value=""), gr.update(value="")),
        inputs=None,
        outputs=[new_revision, new_timestamp],
        api_name=False,
    ).then(
        # Initialize Logfire context
        fn=start_parent_span,
        inputs=[page_title, number_behind, units_behind],
        outputs=context,
    ).then(
        fn=fetch_current_revision,
        inputs=[page_title, context],
        outputs=[new_revision, new_timestamp],
        api_name=False,
    ).then(
        fn=fetch_previous_revision,
        inputs=[page_title, number_behind, units_behind, new_revision, context],
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
            context,
        ],
        outputs=[judge_noteworthy, noteworthy_text, judge_reasoning, confidence],
        api_name=False,
    )

    # Feedback button handlers
    thumbs_up_btn.click(
        fn=save_feedback_agree,
        inputs=[
            page_title,
            number_behind,
            units_behind,
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
        api_name=False,
    )

    thumbs_down_btn.click(
        fn=save_feedback_disagree,
        inputs=[
            page_title,
            number_behind,
            units_behind,
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
        api_name=False,
    )

if __name__ == "__main__":

    # Setup theme without background image
    theme = gr.Theme.from_hub("NoCrypt/miku")
    theme.set(body_background_fill="#FFFFFF", body_background_fill_dark="#000000")
    # Define the HTML for Font Awesome
    head = '<link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css" rel="stylesheet">'
    # Use CSS to style table
    css = """
    #intro-table {background-color: #eff6ff}
    table, tr, td {
        border: none; /* Removes all borders */
        border-collapse: collapse; /* Ensures no gaps between cells */
    }
    """

    demo.launch(theme=theme, head=head, css=css)
