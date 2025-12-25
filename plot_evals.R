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

eval_accuracy <- function() {
  # Plot accuracy for different alignments and eval sets

  # Get concept drift (True labels in feedback)
  u_evals <- evals[!duplicated(evalsets)]
  time_step <- 1:length(u_evals)
  true_percent <- sapply(u_evals, function(eval) {
    sum(eval$human_noteworthy == "True") / nrow(eval) * 100
  })

  # Setup plots
  png("image/eval-accuracy.png", width = 1000, height = 600, pointsize=24)
  layout(matrix(1:2, nrow = 1), widths = c(1, 2))
  par(mar = c(4, 3.7, 3, 1), mgp = c(2.5, 1, 0), las = 1)

  # Start plot 1
  plot(range(time_step), range(true_percent), xlab = "Time Step", ylab = "% Samples labeled 'True'", type = "n", xaxt = "n")
  axis(1, at = time_step)
  title("Concept Drift")
  # Add lines
  lines(time_step, true_percent, type = "b", pch = 19, lwd = 2)

  # Get data for no realignment
  df1 <- df[df$alignment == 1, ]
  # Get data for continuous realignment
  dfx <- df[df$evalset == df$alignment, ]
  # Put data together to get total accuracy range for plot
  df_all <- rbind(df1, dfx)

  # Start plot 2
  par(mar = c(4, 3.7, 3, 6))
  ylim <- range(df_all$accuracy)
  ylim[1] <- ylim[1] - 5
  plot(range(time_step), ylim, xlab = "Time Step", ylab = "% Accuracy", type = "n", xaxt = "n")
  axis(1, at = time_step)
  title("Model Accuracy")

  # Plot lines
  lines(df1$evalset, df1$accuracy, lty = 3, col = 2, type = "b", pch = 19, lwd = 2)
  lines(dfx$evalset, dfx$accuracy, lty = 1, col = 4, type = "b", pch = 19, lwd = 2)

  # Add labels
  text(1, par("usr")[3], "   Development", adj = c(0, 0), srt = 35)
  text(2.5, par("usr")[3], "Production -->", adj = c(0.5, -1))
  text(max(time_step) + 0.2, tail(df1$accuracy, 1), "No realignment", adj = 0, xpd = NA)
  text(max(time_step) + 0.2, tail(dfx$accuracy, 1), "Continuous\nrealignment", adj = 0, xpd = NA)
  dev.off()

}
