import time
import csv
from wiki_data_fetcher import (
    get_previous_revisions,
    extract_revision_info,
    get_wikipedia_introduction,
)

title = []
revid_0, revid_10, revid_100 = [], [], []
ts_0, ts_10, ts_100 = [], [], []
intro_0, intro_10, intro_100 = [], [], []


if __name__ == "__main__":

    # Open the file in read mode
    with open("development/wikipedia_titles.txt", "r") as file:
        # Iterate through each line in the file
        for line in file:
            # Get title from each line without trailing newline characters
            this_title = line.strip()
            print(this_title)
            # Append title
            title.append(this_title)
            # Get info for most recent 100 revisions
            json_data = get_previous_revisions(this_title, revisions=100)
            # Append data for current revision
            info_0 = extract_revision_info(json_data, 0)
            revid_0.append(info_0["revid"])
            ts_0.append(info_0["timestamp"])
            intro_0.append(get_wikipedia_introduction(info_0["revid"]))
            # Append data for 10th revision before current
            info_10 = extract_revision_info(json_data, 10, limit_revnum=False)
            revid_10.append(info_10["revid"])
            ts_10.append(info_10["timestamp"])
            intro_10.append(get_wikipedia_introduction(info_10["revid"]))
            # Append data for 100th revision before current
            info_100 = extract_revision_info(json_data, 100, limit_revnum=False)
            revid_100.append(info_100["revid"])
            ts_100.append(info_100["timestamp"])
            intro_100.append(get_wikipedia_introduction(info_100["revid"]))

            # Write the CSV in each loop in case we need to restart after an error
            # Combine the lists
            # fmt: off
            export_data = zip(
                title, revid_0, revid_10, revid_100,
                ts_0, ts_10, ts_100, intro_0, intro_10, intro_100,
            )
            column_names = [
                "title", "revid_0", "revid_10", "revid_100",
                "ts_0", "ts_10", "ts_100",
                "intro_0", "intro_10", "intro_100",
            ]
            # fmt: on

            with open(
                "development/wikipedia_introductions.csv",
                "w",
                newline="",
                encoding="utf-8",
            ) as myfile:
                wr = csv.writer(myfile)
                # Write a header row
                wr.writerow(column_names)
                # Write the combined data rows
                wr.writerows(export_data)

            # Rate limit our API calls
            time.sleep(5)
