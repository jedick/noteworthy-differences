# plot_evals.R
# Plot evaluation results
# 20251222 jmd version 1

evalsets <- 1:3
alignments <- 0:2
reps <- 1:3

# Loop over evalsets
eval_list <- lapply(evalsets, function(evalset) {
  eval_file <- paste0("evaluations/", paste("evalset", evalset, sep = "_"))

  # Loop over alignments
  align_list <- lapply(alignments, function(alignment) {
    align_file <- paste(eval_file, "alignment", alignment, sep = "_")

    # Loop over repetitions
    rep_list <- lapply(reps, function(rep){
      rep_file <- paste0(paste(align_file, "rep", rep, sep = "_"), ".csv")
      read.csv(rep_file)
    })

    # Combine reps and calculate accuracy
    rep_df <- do.call(rbind, rep_list)
    accuracy <- sum(rep_df$judge_noteworthy == rep_df$human_noteworthy) / nrow(rep_df)
    # Turn into data frame
    data.frame(alignment, accuracy)
  })

  # Combine alignment accuracies into data frame
  align_df <- do.call(rbind, align_list)
  # Add evalset column
  cbind(evalset, align_df)

})

# Make the final data frame
df <- do.call(rbind, eval_list)

# Start plot
plot(range(evalsets), range(df$accuracy), xlab = "Evalulation Set", ylab = "Accuracy", type = "n")
# Plot lines for each alignment
lty <- c(3, 2, 1)
for(alignment in alignments) {
  align_df <- df[df$alignment == alignment, ]
  lines(align_df$evalset, align_df$accuracy, lty = lty[alignment + 1])
}
# Add a legend
legend("topleft", legend = rev(alignments), lty = rev(lty), title = "Alignments")
