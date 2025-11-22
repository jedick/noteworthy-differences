# Script to summarize results for README.md
# 20251117 jmd

output <- character()

intro_df <- read.csv("wikipedia_introductions.csv")
text <- "- Wikipedia pages processed:"
output <- c(output, paste(text, nrow(intro_df)))

t1 <- "- Available 10th previous revision: "
t2 <- "; 100th previous revision: "
output <- c(output, paste0(t1, sum(intro_df$intro_10 != ""), t2, sum(intro_df$intro_100 != "")))

response_df <- read.csv("examples.csv")
heuristic_noteworthy <- c(response_df$heuristic_10_noteworthy, response_df$heuristic_100_noteworthy)
heuristic_noteworthy <- heuristic_noteworthy[heuristic_noteworthy != ""]
heuristic_fraction <- round(100*sum(heuristic_noteworthy == "True") / length(heuristic_noteworthy))
few.shot_noteworthy <- c(response_df$few.shot_10_noteworthy, response_df$few.shot_100_noteworthy)
few.shot_noteworthy <- few.shot_noteworthy[few.shot_noteworthy != ""]
few.shot_fraction <- round(100*sum(few.shot_noteworthy == "True") / length(few.shot_noteworthy))

t1 <- "- Revisions classified as noteworthy with heuristic prompt: "
t2 <- "; few-shot prompt: "
output <- c(output, paste0(t1, heuristic_fraction, "%", t2, few.shot_fraction, "%"))

disagree_df <- read.csv("disagreements_for_AI.csv")
text <- "- Disagreements between heuristic and few-shot model:"
output <- c(output, paste(text, nrow(disagree_df)))

t1 <- "  - Classified as noteworthy with heuristic prompt: "
t2 <- "; few-shot prompt: "
heuristic_dis_noteworthy <- sum(disagree_df$heuristic_noteworthy == "True")
few.shot_dis_noteworthy <- sum(disagree_df$few.shot_noteworthy == "True")
output <- c(output, paste0(t1, heuristic_dis_noteworthy, t2, few.shot_dis_noteworthy))

human_df <- read.csv("human_alignments.csv")
stopifnot(all(human_df$title == disagree_df$title))
text <- "  - Classified as noteworthy by human aligner:"
output <- c(output, paste(text, sum(human_df$noteworthy == "True")))

#heuristic_correct <- sum(human_df$noteworthy == disagree_df$heuristic_noteworthy)
#heuristic_correct_fraction <- round(100*heuristic_correct / nrow(disagree_df))
#few.shot_correct <- sum(human_df$noteworthy == disagree_df$few.shot_noteworthy)
#few.shot_correct_fraction <- round(100*few.shot_correct / nrow(disagree_df))
#
#t1 <- "  - Accuracy for heuristic prompt: "
#t2 <- "; few-shot prompt: "
#output <- c(output, paste0(t1, heuristic_correct_fraction, "%", t2, few.shot_correct_fraction, "%"))

AI_judge_df <- read.csv("AI_judgments.csv")
AI_noteworthy <- sum(AI_judge_df$noteworthy == "True")
AI_correct <- sum(AI_judge_df$noteworthy == human_df$noteworthy)
AI_correct_fraction <- round(100*AI_correct / nrow(AI_judge_df))
text <- "  - Classified as noteworthy by **unaligned** AI judge: "
output <- c(output, paste0(text, AI_noteworthy, " (", AI_correct_fraction, "% accurate)"))

#text <- "  - Accuracy for AI judge: "
#output <- c(output, paste0(text, AI_correct_fraction, "%"))

# aAI: aligned AI
aAI_judge_df <- read.csv("AI_judgments_aligned.csv")
aAI_noteworthy <- sum(aAI_judge_df$noteworthy == "True")
aAI_correct <- sum(aAI_judge_df$noteworthy == human_df$noteworthy)
aAI_correct_fraction <- round(100*aAI_correct / nrow(aAI_judge_df))
text <- "  - Classified as noteworthy by **aligned** AI judge: "
output <- c(output, paste0(text, aAI_noteworthy, " (", aAI_correct_fraction, "% accurate)"))

# aAI: aligned AI
aAI_judge_df <- read.csv("AI_judgments_aligned_heuristic.csv")
aAI_noteworthy <- sum(aAI_judge_df$noteworthy == "True")
aAI_correct <- sum(aAI_judge_df$noteworthy == human_df$noteworthy)
aAI_correct_fraction <- round(100*aAI_correct / nrow(aAI_judge_df))
text <- "  - Classified as noteworthy by **aligned** AI judge (heuristic prompt): "
output <- c(output, paste0(text, aAI_noteworthy, " (", aAI_correct_fraction, "% accurate)"))


# Print output to terminal and copy to README.md
if(FALSE) {
  cat(paste(output, collapse = "\n"), sep = "\n")
}
