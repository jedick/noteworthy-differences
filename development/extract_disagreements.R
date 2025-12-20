# Process classifier responses (examples.csv)
# to make files for human aligner and AI judge to review
# 20251116 jmd

# Read the classifier responses
response_df <- read.csv("examples.csv")

# Find examples where classifiers disagreed (10 and 100 revisions ago compared to current)
disagree_10 <- response_df$heuristic_10_noteworthy != response_df$few.shot_10_noteworthy
disagree_100 <- response_df$heuristic_100_noteworthy != response_df$few.shot_100_noteworthy

# Read the Wikipedia introductions
intro_df <- read.csv("wikipedia_introductions.csv")
# Check that the titles match
stopifnot(all(response_df$title == intro_df$title))

# Get the old and new revisions
old_revision <- c(intro_df$intro_10[disagree_10], intro_df$intro_100[disagree_100])
new_revision <- c(intro_df$intro_0[disagree_10], intro_df$intro_0[disagree_100])
# Also get the titles
title <- c(intro_df$title[disagree_10], intro_df$title[disagree_100])

# Create df with common columns for human aligner and AI judge
out_common <- data.frame(title, old_revision, new_revision)
# Add empty columns for human aligner to fill in
out_human <- cbind(out_common, noteworthy = "", rationale = "")
# Save file for human aligner
write.csv(out_human, "disagreements_for_human.csv", row.names = FALSE)

# Add context for AI judge
heuristic_noteworthy <- c(response_df$heuristic_10_noteworthy[disagree_10], response_df$heuristic_100_noteworthy[disagree_100])
heuristic_rationale <- c(response_df$heuristic_10_rationale[disagree_10], response_df$heuristic_100_rationale[disagree_100])
few.shot_noteworthy <- c(response_df$few.shot_10_noteworthy[disagree_10], response_df$few.shot_100_noteworthy[disagree_100])
few.shot_rationale <- c(response_df$few.shot_10_rationale[disagree_10], response_df$few.shot_100_rationale[disagree_100])

context <- data.frame(heuristic_noteworthy, heuristic_rationale, few.shot_noteworthy, few.shot_rationale)
colnames(context) <- gsub("few.shot", "few-shot", colnames(context))
out_ai <- cbind(out_common, context)
write.csv(out_ai, "disagreements_for_AI.csv", row.names = FALSE)
