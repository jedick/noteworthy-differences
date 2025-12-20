# Script to summarize results for README.md
# 20251117 jmd

# Function to calculate accuracy
calc_accuracy <- function(predicted, actual) {
  if (length(predicted) == 0 || length(actual) == 0) return(NA)
  if (length(predicted) != length(actual)) return(NA)
  correct <- sum(predicted == actual)
  round(100 * correct / length(predicted))
}

# Read train data
train_intro_df <- read.csv("train/wikipedia_introductions.csv")
train_response_df <- read.csv("train/examples.csv")
train_disagree_df <- read.csv("train/disagreements_for_AI.csv")
train_human_df <- read.csv("train/human_alignments.csv")
train_AI_judge_df <- read.csv("train/AI_judgments_unaligned.csv")
train_aAI_fewshot_df <- read.csv("train/AI_judgments_fewshot.csv")
train_aAI_heuristic_df <- read.csv("train/AI_judgments_heuristic.csv")

# Read test data
test_intro_df <- read.csv("test/wikipedia_introductions.csv")
test_response_df <- read.csv("test/examples.csv")
test_disagree_df <- read.csv("test/disagreements_for_AI.csv")
test_human_df <- read.csv("test/human_alignments.csv")
test_AI_judge_df <- read.csv("test/AI_judgments_unaligned.csv")
test_aAI_fewshot_df <- read.csv("test/AI_judgments_fewshot.csv")
test_aAI_heuristic_df <- read.csv("test/AI_judgments_heuristic.csv")

# Calculate metrics for train set
train_wikipedia_pages <- nrow(train_intro_df)
train_revisions <- sum(train_intro_df$intro_10 != "") + sum(train_intro_df$intro_100 != "")

train_heuristic_noteworthy <- c(train_response_df$heuristic_10_noteworthy, train_response_df$heuristic_100_noteworthy)
train_heuristic_noteworthy <- train_heuristic_noteworthy[train_heuristic_noteworthy != ""]
train_heuristic_count <- sum(train_heuristic_noteworthy == "True")

train_fewshot_noteworthy <- c(train_response_df$few.shot_10_noteworthy, train_response_df$few.shot_100_noteworthy)
train_fewshot_noteworthy <- train_fewshot_noteworthy[train_fewshot_noteworthy != ""]
train_fewshot_count <- sum(train_fewshot_noteworthy == "True")

train_disagreements <- nrow(train_disagree_df)
train_human_noteworthy <- sum(train_human_df$noteworthy == "True")
train_AI_noteworthy <- sum(train_AI_judge_df$noteworthy == "True")
train_aAI_fewshot_noteworthy <- sum(train_aAI_fewshot_df$noteworthy == "True")
train_aAI_heuristic_noteworthy <- sum(train_aAI_heuristic_df$noteworthy == "True")

# Calculate train accuracies
stopifnot(all(train_human_df$title == train_disagree_df$title))
train_AI_accuracy <- calc_accuracy(train_AI_judge_df$noteworthy, train_human_df$noteworthy)
train_aAI_fewshot_accuracy <- calc_accuracy(train_aAI_fewshot_df$noteworthy, train_human_df$noteworthy)
train_aAI_heuristic_accuracy <- calc_accuracy(train_aAI_heuristic_df$noteworthy, train_human_df$noteworthy)

# Calculate metrics for test set
test_wikipedia_pages <- nrow(test_intro_df)
test_revisions <- sum(test_intro_df$intro_10 != "") + sum(test_intro_df$intro_100 != "")

test_heuristic_noteworthy <- c(test_response_df$heuristic_10_noteworthy, test_response_df$heuristic_100_noteworthy)
test_heuristic_noteworthy <- test_heuristic_noteworthy[test_heuristic_noteworthy != ""]
test_heuristic_count <- sum(test_heuristic_noteworthy == "True")

test_fewshot_noteworthy <- c(test_response_df$few.shot_10_noteworthy, test_response_df$few.shot_100_noteworthy)
test_fewshot_noteworthy <- test_fewshot_noteworthy[test_fewshot_noteworthy != ""]
test_fewshot_count <- sum(test_fewshot_noteworthy == "True")

test_disagreements <- nrow(test_disagree_df)
test_human_noteworthy <- sum(test_human_df$noteworthy == "True")
test_AI_noteworthy <- sum(test_AI_judge_df$noteworthy == "True")
test_aAI_fewshot_noteworthy <- sum(test_aAI_fewshot_df$noteworthy == "True")
test_aAI_heuristic_noteworthy <- sum(test_aAI_heuristic_df$noteworthy == "True")

# Calculate test accuracies
stopifnot(all(test_human_df$title == test_disagree_df$title))
test_AI_accuracy <- calc_accuracy(test_AI_judge_df$noteworthy, test_human_df$noteworthy)
test_aAI_fewshot_accuracy <- calc_accuracy(test_aAI_fewshot_df$noteworthy, test_human_df$noteworthy)
test_aAI_heuristic_accuracy <- calc_accuracy(test_aAI_heuristic_df$noteworthy, test_human_df$noteworthy)

# Build markdown table
table_rows <- character()

# Helper function to format table row
format_row <- function(label, train_samples, test_samples, train_acc = "", test_acc = "") {
  if(train_samples == "" | test_samples == "") {
    return(sprintf("| %s | %s | %s | %s | %s |", label, train_samples, test_samples, train_acc, test_acc))
  }
  train_acc_str <- ifelse(train_acc == "", "", paste0(train_acc, "%"))
  test_acc_str <- ifelse(test_acc == "", "", paste0(test_acc, "%"))
  sprintf("| %s | %d | %d | %s | %s |", label, train_samples, test_samples, train_acc_str, test_acc_str)
}

# Main rows
table_rows <- c(table_rows, format_row("Wikipedia pages", train_wikipedia_pages, test_wikipedia_pages))
table_rows <- c(table_rows, format_row("Total revisions (10 and 100 behind)", train_revisions, test_revisions))
table_rows <- c(table_rows, format_row("Noteworthy classifications by:", "", ""))
table_rows <- c(table_rows, format_row("&emsp;Heuristic classifier", train_heuristic_count, test_heuristic_count))
table_rows <- c(table_rows, format_row("&emsp;Few-shot classifier", train_fewshot_count, test_fewshot_count))
table_rows <- c(table_rows, format_row("Disagreements between classifiers", train_disagreements, test_disagreements))

# Indented sub-rows
table_rows <- c(table_rows, format_row("&emsp;Noteworthy classifications by:", "", ""))
table_rows <- c(table_rows, format_row("&emsp;&emsp;Human annotator", train_human_noteworthy, test_human_noteworthy))
table_rows <- c(table_rows, format_row("&emsp;&emsp;Unaligned AI judge", train_AI_noteworthy, test_AI_noteworthy, train_AI_accuracy, test_AI_accuracy))
table_rows <- c(table_rows, format_row("&emsp;&emsp;Few-shot AI judge", train_aAI_fewshot_noteworthy, test_aAI_fewshot_noteworthy, train_aAI_fewshot_accuracy, test_aAI_fewshot_accuracy))
table_rows <- c(table_rows, format_row("&emsp;&emsp;Heuristic AI judge", train_aAI_heuristic_noteworthy, test_aAI_heuristic_noteworthy, train_aAI_heuristic_accuracy, test_aAI_heuristic_accuracy))

# Create full markdown table
header <- "| | Train samples | Test samples | Train accuracy | Test accuracy |"
separator <- "| --- | --- | --- | --- | --- |"
output <- c(header, separator, table_rows)

# Print output
cat(paste(output, collapse = "\n"), sep = "\n")
