# plot_evals.R
# Plot evaluation results
# 20251222 jmd version 1
# 20251223 use available files instead of hard-coded rounds/reps

evalsets <- numeric()
alignments <- numeric()
evals <- list()

files <- dir("evaluations", full.names=TRUE)

# Loop over files
for(file in files) {
  eval <- read.csv(file)
  evalset <- as.numeric(strsplit(file[1], "_")[[1]][2])
  alignment <- as.numeric(strsplit(file[1], "_")[[1]][4])
  # Check if we're doing a rep > 1
  if(evalset %in% evalsets & alignment %in% alignments) {
    ieval <- which(evalsets == evalset & alignments == alignment)
    if(length(ieval) > 0) {
      evals[[ieval]] <- rbind(evals[[ieval]], eval)
      next
    }
  }
  # Assign the initial rep
  evalsets <- c(evalsets, evalset)
  alignments <- c(alignments, alignment)
  evals <- c(evals, list(eval))
}

# Calculate accuracy for each eval
accuracy <- sapply(evals, function(eval) {
    sum(eval$judge_noteworthy == eval$human_noteworthy) / nrow(eval)
})
# Make the data frame
df <- data.frame(evalset = evalsets, alignment = alignments, accuracy)
# Use percent for accuracy
df$accuracy <- df$accuracy * 100

concept_drift <- function() {
  # Plot baseline accuracy and concept drift
  df0 <- df[df$alignment == 0, ]
  # Get concept drift (True labels in feedback)
  u_evals <- evals[!duplicated(evalsets)]
  true_percent <- sapply(u_evals, function(eval) {
    sum(eval$human_noteworthy == "True") / nrow(eval) * 100
  })
  # Get baseline accuracy (unaligned judge)
  accuracy <- df0$accuracy
  # Start plot
  png("image/concept-drift.png", width = 800, height = 600, pointsize=24)
  par(mar = c(4, 3.7, 3, 10), mgp = c(2.5, 1, 0), las = 1)
  plot(range(df0$evalset), range(accuracy, true_percent), xlab = "Time Step", ylab = "Percentage", type = "n", xaxt = "n")
  axis(1, at = df0$evalset)
  title("Concept Drift Visualization")
  # Add lines
  lines(df0$evalset, percentage_true, type = "b", pch = 19, lwd = 2)
  lines(df0$evalset, accuracy, type = "b", pch = 19, lwd = 2, lty = 2)
  # Add labels
  text(1, par("usr")[3], "   Development", adj = c(0, 0), srt = 30)
  text(2, par("usr")[3], "Production -->", adj = c(0.3, -1))
  text(nrow(df0) + 0.2, tail(true_percent, 1), "'True' Label Frequency\n(User Feedback)", adj = 0, xpd = NA)
  text(nrow(df0) + 0.2, tail(accuracy, 1), "Baseline Accuracy\n(Unaligned Judge)", adj = 0, xpd = NA)
  #text(1.5, 35, "Over time,\nmore revisions\nare labeled\nnot noteworthy", adj = 0.5)
  dev.off()
}

eval_accuracy <- function() {
  # Plot accuracy for different alignments and eval sets

  # Subtract baseline (no alignment)
  u_evalsets <- unique(evalsets)
  for(evalset in u_evalsets) {
    ieval <- df$evalset == evalset
    noalign <- df$alignment == 0
    df$accuracy[ieval] <- df$accuracy[ieval] - df$accuracy[ieval & noalign]
  }

  # Get data for no realignment
  df1 <- df[df$alignment == 1, ]
  # Get data for single realignment
  df2 <- df[df$evalset == 1 & df$alignment == 1 | df$evalset > 1 & df$alignment == 2, ]
  # Get data for continuous realignment
  dfx <- df[df$evalset == df$alignment, ]
  # Put data together to get total accuracy range for plot
  df_all <- rbind(df1, df2, dfx)

  # Start plot
  png("image/eval-accuracy.png", width = 800, height = 600, pointsize=24)
  par(mar = c(4, 3.7, 3, 10), mgp = c(2.5, 1, 0), las = 1)
  plot(range(u_evalsets), range(df_all$accuracy), xlab = "Time Step", ylab = "% Accuracy vs Baseline", type = "n", xaxt = "n")
  axis(1, at = u_evalsets)
  rect(par("usr")[1], par("usr")[3], par("usr")[2], 0, col = "#cccccc", border = NA)
  title("Accuracy vs Baseline")

  # Plot lines
  lines(df1$evalset, df1$accuracy, lty = 3, col = 2, type = "b", pch = 19, lwd = 2)
  lines(df2$evalset, df2$accuracy, lty = 2, col = "orange", type = "b", pch = 19, lwd = 2)
  lines(dfx$evalset, dfx$accuracy, lty = 1, col = 4, type = "b", pch = 19, lwd = 2)

  # Add labels
  text(1, par("usr")[3], "   Development", adj = c(0, 0), srt = 30)
  text(2, par("usr")[3], "Production -->", adj = c(0.3, -1))
  text(nrow(df1) + 0.2, tail(df1$accuracy, 1), "No realignment\nin production", adj = 0, xpd = NA)
  text(nrow(df2) + 0.2, tail(df2$accuracy, 1), "Single realignment\nat Time 2", adj = 0, xpd = NA)
  text(nrow(dfx) + 0.2, tail(dfx$accuracy, 1), "Continuous realignment", adj = 0, xpd = NA)
  dev.off()

}
