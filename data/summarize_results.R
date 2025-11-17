# Script to summarize results for README.md
# 20251117 jmd

output <- character()

intro_df <- read.csv("wikipedia_introductions.csv")
text <- "- Wikipedia pages processed:"
output <- c(output, paste(text, nrow(intro_df)))

t1 <- "- Pages with available 10th previous revision: "
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
text <- "- Pages with disagreements between classifications from heuristic and few-shot prompts:"
output <- c(output, paste(text, nrow(disagree_df)))

t1 <- "- Disagreements classified as noteworthy with heuristic prompt: "
t2 <- "; few-shot prompt: "
heuristic_dis_noteworthy <- sum(disagree_df$heuristic_noteworthy == "True")
few.shot_dis_noteworthy <- sum(disagree_df$few.shot_noteworthy == "True")
output <- c(output, paste0(t1, heuristic_dis_noteworthy, t2, few.shot_dis_noteworthy))

human_df <- read.csv("human_judgments.csv")
stopifnot(all(human_df$title == disagree_df$title))
text <- "- Disagreements classified as noteworthy by human judge:"
output <- c(output, paste(text, sum(human_df$noteworthy == "True")))

heuristic_correct <- sum(human_df$noteworthy == disagree_df$heuristic_noteworthy)
few.shot_correct <- sum(human_df$noteworthy == disagree_df$few.shot_noteworthy)

t1 <- "- Disagreements coinciding with human judge for heuristic prompt: "
t2 <- "; few-shot prompt: "
output <- c(output, paste0(t1, heuristic_correct, t2, few.shot_correct))

# Print output to terminal and copy to README.md
#cat(paste(output, collapse = "\n"), sep = "\n")
