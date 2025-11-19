import pandas as pd
from models import judge

if __name__ == "__main__":

    """
    Run the judge on all rows from 'data/disagreements_for_AI.csv' and save results in 'data/AI_judgments.csv'.
    """

    # Read the data
    df = pd.read_csv("data/disagreements_for_AI.csv")

    # Add empty columns for AI judgments
    df["noteworthy"] = None
    df["reasoning"] = None

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
                )
            except:
                output = {"noteworthy": None, "reasoning": None}
            print(output)
            # Update data frame
            df.at[index, "noteworthy"] = output["noteworthy"]
            df.at[index, "reasoning"] = output["reasoning"]
            # Write CSV in every loop to avoid data loss if errors occur
            df.to_csv("data/AI_judgments.csv", index=False, encoding="utf-8")
