import gradio as gr
from wiki_data_fetcher import (
    get_previous_revisions,
    get_revision_from_age,
    get_wikipedia_introduction,
    extract_revision_info,
)


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
        return "", ""

    try:
        # Get current revision (revision 0)
        json_data = get_previous_revisions(title, revisions=0)
        revision_info = extract_revision_info(json_data, revision=0)

        if not revision_info.get("revid"):
            error_msg = f"Error: Could not find Wikipedia page '{title}'. Please check the title."
            raise gr.Error(error_msg, print_exception=False)
            return "", ""

        revid = revision_info["revid"]
        timestamp = revision_info["timestamp"]

        # Get introduction
        introduction = get_wikipedia_introduction(title, revid)

        if introduction is None:
            introduction = f"Error: Could not retrieve introduction for current revision (revid: {revid})"

        # Format timestamp for display
        timestamp = f"**Timestamp:** {timestamp}" if timestamp else ""

        # Return introduction text and timestamp
        return introduction, timestamp

    except Exception as e:
        error_msg = f"Error occurred: {str(e)}"
        raise gr.Error(error_msg, print_exception=False)
        return "", ""


def fetch_previous_revision(title: str, mode: str, number: int, new_revision: str):
    """
    Fetch previous revision of a Wikipedia article and return its introduction.

    Args:
        title: Wikipedia article title
        mode: "days" or "revisions"
        number: Number of days or revisions to go back

    Returns:
        Tuple of (introudction, timestamp)
    """

    # If we get here with an empty new revision, then an error should have been raised
    # in fetch_current_revision, so just return empty values without raising another error
    if not new_revision:
        return "", ""

    try:
        # Get previous revision based on mode
        if mode == "revisions":
            json_data = get_previous_revisions(title, revisions=number)
            revision_info = extract_revision_info(json_data, revision=number)
        else:  # mode == "days"
            revision_info = get_revision_from_age(title, age_days=number)

        if not revision_info.get("revid"):
            error_msg = f"Error: Could not find revision {number} {'revisions' if mode == 'revisions' else 'days'} back for '{title}'."
            raise gr.Error(error_msg, print_exception=False)
            return "", ""

        revid = revision_info["revid"]
        timestamp = revision_info["timestamp"]

        # Get introduction
        introduction = get_wikipedia_introduction(title, revid)

        if introduction is None:
            introduction = f"Error: Could not retrieve introduction for previous revision (revid: {revid})"

        # Format timestamp for display
        timestamp = f"**Timestamp:** {timestamp}" if timestamp else ""

        # Return introduction text and timestamp
        return introduction, timestamp

    except Exception as e:
        error_msg = f"Error occurred: {str(e)}"
        raise gr.Error(error_msg, print_exception=False)
        return "", ""


# Create Gradio interface
with gr.Blocks(title="Noteworthy Differences") as demo:
    gr.Markdown("# Noteworthy Differences")

    with gr.Row():
        title_input = gr.Textbox(
            label="Wikipedia Page Title", placeholder="e.g., David_Szalay", value=""
        )
        mode_dropdown = gr.Dropdown(
            choices=["days", "revisions"], value="days", label="Mode"
        )
        number_input = gr.Number(label="Number", value=100, minimum=0, precision=0)
        submit_btn = gr.Button("Fetch Revisions", variant="primary")

    with gr.Row():
        with gr.Column():
            gr.Markdown("### Old Revision")
            old_timestamp = gr.Markdown("")
            old_revision = gr.Textbox(
                label="", lines=20, max_lines=30, interactive=False
            )

        with gr.Column():
            gr.Markdown("### New Revision")
            new_timestamp = gr.Markdown("")
            new_revision = gr.Textbox(
                label="", lines=20, max_lines=30, interactive=False
            )

        with gr.Column():
            gr.Markdown("### Model Output")
            model_output = gr.Textbox(
                label="",
                lines=20,
                max_lines=30,
                interactive=False,
                placeholder="Model output will appear here...",
            )

    # Press Enter in textbox or use button to submit
    gr.on(
        triggers=[title_input.submit, submit_btn.click],
        fn=fetch_current_revision,
        inputs=[title_input],
        outputs=[new_revision, new_timestamp],
    ).then(
        fn=fetch_previous_revision,
        inputs=[title_input, mode_dropdown, number_input, new_revision],
        outputs=[old_revision, old_timestamp],
    )


if __name__ == "__main__":
    demo.launch()
