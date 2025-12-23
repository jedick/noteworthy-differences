from datasets import load_dataset
from dotenv import load_dotenv
from datetime import datetime
from models import judge
import pandas as pd
import logfire

# Load API keys
load_dotenv()
# Setup logging with Logfire
logfire.configure()


def select_round(dataset, split, round=None):
    """
    Select the production round for a given dataset and split.

    Args:
        dataset: Hugging Face dataset
        split: train or test
        round: round number (None for most recent)

    Returns a tuple of (index, round) with the the indices of files in the round and the round used.
    """
    # Define production time spans for rounds
    time_spans = [
        # First round (development) has no time span
        [None, None],
        ["2025-12-19T13:29:42", "2025-12-20T07:25:12"],
        ["2025-12-23T01:20:55", "2025-12-23T06:39:43"],
    ]
    # If no round is specified, use the most recent one
    if round is None:
        round = len(time_spans)
        print(f"Selected round {round}")
    # Return None for non-production round
    if round < 2:
        return None
    # Get file names
    file_urls = list(dataset.info.download_checksums.keys())
    file_names = [x.split("/data/")[1] for x in file_urls]
    # Filter list using list comprehension
    split_file_names = [x for x in file_names if f"{split}-" in x]
    # Remove test- prefix and .json suffix
    timestamps = [
        x.replace(f"{split}-", "").replace(".json", "") for x in split_file_names
    ]
    # Convert to datetime object
    dt_timestamps = [datetime.fromisoformat(x) for x in timestamps]
    # Get time span for this round
    time_span = time_spans[round - 1]
    dt_cutoffs = [datetime.fromisoformat(x) for x in time_span]
    # Get index of files that are between the cutoff times
    index = [
        i
        for i, x in enumerate(dt_timestamps)
        if x > dt_cutoffs[0] and x < dt_cutoffs[1]
    ]
    return index, round


def get_evalset(round=None):
    """
    Get the evalset for a given round.

    Returns:
        Tuple of (df, y) where df is a DataFrame with model input
        and y is a list of boolean with ground truth.
    """

    dataset = None
    index = None

    # Get latest round if argument is None
    if round is None:
        dataset = load_dataset("jedick/noteworthy-differences-feedback", split="test")
        index, round = select_round(dataset, "test", round)

    if round == 1:
        # For the 1st round we use development set (model disagreements on pages linked from the Wikipedia main page)
        df = pd.read_csv("development/test/disagreements_for_AI.csv")
        # Get y list (ground truth)
        y_df = pd.read_csv("development/test/human_alignments.csv")
        y = list(y_df["noteworthy"])
        # Sanity check: page titles are the same
        if not y_df["title"].equals(df["title"]):
            raise ValueError("Titles aren't equal")
        # Rename columns for consistency with later rounds
        df.rename(
            columns={
                "title": "page_title",
                "few-shot_noteworthy": "fewshot_noteworthy",
                "few-shot_rationale": "fewshot_rationale",
            },
            inplace=True,
        )
        # Return results
        return df, y
    else:
        if dataset is None:
            # For the 2nd and higher rounds we use production data (examples with user feedback)
            # Load feedback dataset
            dataset = load_dataset(
                "jedick/noteworthy-differences-feedback", split="test"
            )
            # Get indices of files in this round
            index, _ = select_round(dataset, "test", round)
        # Convert to DataFrame
        df = dataset.to_pandas()
        # Use only these examples
        df = df.iloc[index]
        # Reset the index after subsetting
        df.reset_index(drop=True, inplace=True)
        # Construct y list (ground truth)
        judge = list(df["judge_noteworthy"])
        feedback = list(df["feedback"])
        y = [j if f == "agree" else not j for j, f in zip(judge, feedback)]
        # Return results
        return df, y


def evaluate(e_round=1, a_round=1, rep=1):
    """
    Run evaluation for a given evalset and alignment prompt.

    Args:
        e_round: The round of the evalset to use (> 0).
        a_round: The round of the alignment to use (>= 0).

    Details:
        Round 0 corresponds to the unaligned judge.
        Round 1 corresponds to the development evalset and first heuristic alignment.
        Rounds 2 and higher correspond to production evalsets and alignments.

    Results:
        Saves results in 'evals/evalset_{e_round}_alignment_{a_round}.csv'.
    """

    span_name = f"Evalset {e_round}, alignment {a_round}"
    with logfire.span(span_name):
        # Select judge mode
        judge_mode = "unaligned" if a_round == 0 else "aligned-heuristic"
        # Define output file
        outfile = f"evaluations/evalset_{e_round}_alignment_{a_round}_rep_{rep}.csv"
        print(f"Saving evaluation results to {outfile}")
        # Get evalset and ground truth
        df, y = get_evalset(e_round)

        # Initialize output lists
        page_title = []
        judge_reasoning = []
        judge_noteworthy = []
        human_noteworthy = []

        for index, row in df.iterrows():
            # Change this if needed (to restart after errors)
            if index < 0:
                next
            else:
                # Run judge
                try:
                    with logfire.span(row["page_title"]):
                        output = judge(
                            df.iloc[index]["old_revision"],
                            df.iloc[index]["new_revision"],
                            df.iloc[index]["heuristic_rationale"],
                            df.iloc[index]["fewshot_rationale"],
                            mode=judge_mode,
                            round=a_round,
                        )
                except:
                    output = {"noteworthy": None, "reasoning": None}
                print(output)
                # Update output lists
                page_title.append(row["page_title"])
                judge_reasoning.append(output["reasoning"])
                judge_noteworthy.append(output["noteworthy"])
                human_noteworthy.append(y[index])
                # Write CSV in every loop to avoid data loss if errors occur
                data_list = list(
                    zip(page_title, judge_reasoning, judge_noteworthy, human_noteworthy)
                )
                columns = [
                    "page_title",
                    "judge_reasoning",
                    "judge_noteworthy",
                    "human_noteworthy",
                ]
                out_df = pd.DataFrame(data_list, columns=columns)
                out_df.to_csv(outfile, index=False, encoding="utf-8")
