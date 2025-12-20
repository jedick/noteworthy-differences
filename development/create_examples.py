import pandas as pd
from models import classifier


def run_classifier(row):
    """
    Run the model on one row of data from 'development/wikipedia_introductions.csv'.
    The model is run up to four times: two prompt styles (heuristic and few-shot)
    and two revision intervals (from 10th and 100th previous revisions to current).

    Usage:

    df = pd.read_csv("development/wikipedia_introductions.csv")
    row = df.iloc[38]
    run_classifier(row)
    """

    # Initialize output dict
    output = {}

    output["heuristic_10"] = classifier(row["intro_10"], row["intro_0"], "heuristic")
    output["few-shot_10"] = classifier(row["intro_10"], row["intro_0"], "few-shot")
    output["heuristic_100"] = classifier(row["intro_100"], row["intro_0"], "heuristic")
    output["few-shot_100"] = classifier(row["intro_100"], row["intro_0"], "few-shot")

    return output


if __name__ == "__main__":

    """
    Run the classifier on all rows from 'development/wikipedia_introductions.csv' and save results in 'development/examples.csv'.
    """

    # Read the data
    df = pd.read_csv("development/wikipedia_introductions.csv")

    # For reference: Find row indices with at least one missing value
    # missing_rows = df.index[df.isnull().any(axis=1)].tolist()
    # print("\nRow indices with missing values:", missing_rows)

    # Initialize output data frame
    df_out = None

    for index, row in df.iterrows():
        # Print the title to see progress
        print(row["title"])
        # Run classifier
        output = run_classifier(row)
        print(output)
        # Create column names and row for data frame
        column_names = [
            outer_k + "_" + inner_k
            for outer_k in output.keys()
            for inner_k in output[outer_k].keys()
        ]
        row_values = [
            inner_v for outer_k in output.keys() for inner_v in output[outer_k].values()
        ]
        # Add title to output
        column_names = ["title"] + column_names
        row_values = [row["title"]] + row_values
        df_row = pd.DataFrame([row_values], columns=column_names)
        if df_out is None:
            df_out = df_row
        else:
            df_out = pd.concat([df_out, df_row])
        # Write CSV in every loop to avoid data loss if errors occur
        df_out.to_csv("development/examples.csv", index=False, encoding="utf-8")
