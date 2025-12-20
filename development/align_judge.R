# Create examples to align judge
# 20251119 jmd

disagree_df <- read.csv("disagreements_for_AI.csv")
classifier_1 <- paste0("Model 1: ", disagree_df$heuristic_rationale)
classifier_2 <- paste0("Model 2: ", disagree_df$few.shot_rationale)

human_df <- read.csv("human_alignments.csv")
stopifnot(all(human_df$title == disagree_df$title))
human <- paste0("Human: ", human_df$rationale, " Noteworthy: ", human_df$noteworthy, ".")

alignment_text <- paste(paste(classifier_1, classifier_2, human), collapse = "\n")
writeLines(alignment_text, "alignment_fewshot.txt")
