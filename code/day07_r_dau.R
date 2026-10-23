script_path <- function() {
  args <- commandArgs(trailingOnly = FALSE)
  file_arg <- grep("^--file=", args, value = TRUE)
  if (length(file_arg) == 0) {
    return(getwd())
  }
  dirname(normalizePath(sub("^--file=", "", file_arg[1])))
}

project_dir <- normalizePath(file.path(script_path(), ".."))
output_dir <- file.path(project_dir, "days")
input_file <- file.path(output_dir, "ml_day07_daily_metrics.csv")
output_file <- file.path(output_dir, "ml_day07_r_dau.png")

suppressPackageStartupMessages({
  library(dplyr)
  library(ggplot2)
})

if (!file.exists(input_file)) {
  stop("Missing daily metrics. Run code/day07_review.py first.")
}

daily <- read.csv(input_file, stringsAsFactors = FALSE) %>%
  mutate(
    date_day = as.Date(date_day),
    dau_7d_avg = if_else(
      is.na(dau_7d_avg),
      as.numeric(stats::filter(dau, rep(1 / 7, 7), sides = 1)),
      dau_7d_avg
    )
  )

plot_data <- daily %>%
  select(date_day, dau, dau_7d_avg, is_dau_anomaly)

chart <- ggplot(plot_data, aes(x = date_day)) +
  geom_line(aes(y = dau, colour = "DAU"), linewidth = 0.6, na.rm = TRUE) +
  geom_line(
    aes(y = dau_7d_avg, colour = "7-day average"),
    linewidth = 0.8,
    na.rm = TRUE
  ) +
  scale_colour_manual(
    values = c("DAU" = "#2F6B9A", "7-day average" = "#F28E2B")
  ) +
  labs(
    title = "Daily Active Users - R Reproduction",
    x = "Date",
    y = "DAU",
    colour = "Series"
  ) +
  theme_minimal()

if ("is_dau_anomaly" %in% names(plot_data)) {
  chart <- chart +
    geom_point(
      data = filter(plot_data, is_dau_anomaly == 1),
      aes(y = dau),
      colour = "#C00000",
      size = 1.5
    )
}

ggsave(output_file, chart, width = 12, height = 6, dpi = 150)

cat("Saved:", output_file, "\n")
