import sys
import pandas as pd
from models import judge

if __name__ == "__main__":

    """
    Run the judge on all rows from 'development/disagreements_for_AI.csv' and save results in 'development/AI_judgments_unaligned.csv'.
    """

    # Read the data
    df = pd.read_csv("development/disagreements_for_AI.csv")

    # Add empty columns for AI judgments
    df["noteworthy"] = None
    df["reasoning"] = None

    # We run the unaligned judge unless the script is called with --aligned-fewshot or --aligned--heuristic
    mode = "unaligned"
    outfile = "development/AI_judgments_unaligned.csv"
    # Check if an argument was passed
    if len(sys.argv) > 1:
        # sys.argv[0] is the script name, sys.argv[1] is the first argument
        argument = sys.argv[1]
        if argument == "--aligned-fewshot":
            mode = "aligned-fewshot"
            outfile = "development/AI_judgments_fewshot.csv"
        elif argument == "--aligned-heuristic":
            mode = "aligned-heuristic"
            outfile = "development/AI_judgments_heuristic.csv"
        else:
            raise ValueError(f"Unknown argument: {argument}")

    print(f"Saving judgments to {outfile}")

    for index, row in df.iterrows():
        # Change this if needed (to restart after errors)
        if index < 0:
            next
        else:
            # Print the title to see progress
            print(row["title"])
            # Run judge
            try:
                output = judge(
                    df.iloc[index]["old_revision"],
                    df.iloc[index]["new_revision"],
                    df.iloc[index]["heuristic_rationale"],
                    df.iloc[index]["few-shot_rationale"],
                    mode=mode,
                )
            except:
                output = {"noteworthy": None, "reasoning": None}
            print(output)
            # Update data frame
            df.at[index, "noteworthy"] = output["noteworthy"]
            df.at[index, "reasoning"] = output["reasoning"]
            # Write CSV in every loop to avoid data loss if errors occur
            df.to_csv(outfile, index=False, encoding="utf-8")
