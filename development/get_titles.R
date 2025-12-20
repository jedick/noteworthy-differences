# This script was run on 2025-11-15 and 2025-11-18 to create train/wikipedia_titles.txt
# This script was run on 2025-11-21 to create test/wikipedia_titles.txt

url <- "https://en.wikipedia.org/wiki/Main_Page"
lines <- readLines(url)

# This is the page revision at this time, but doesn't capture current page content (Main Page is a special page)
#url <- "https://en.wikipedia.org/w/index.php?title=Main_Page&oldid=1319805659"

process_line <- function(line) {
  splits <- strsplit(line, "<a href=\"/wiki/", fixed=TRUE)
  # Keep all but the first split (before the first <a href ... tag)
  splits <- tail(splits[[1]], -1)
  # Get the page titles
  titles <- gsub('\" title=\".*', "", splits)
  # Decode URL escapes
  URLdecode(titles)
}

# Get the titles for all lines
sapply(lines, process_line)
all_titles <- sapply(lines, process_line)
# Convert to character vector
all_titles <- as.character(unlist(all_titles))
# Remove special pages
used_titles <- all_titles
for(special in c("^Main_Page", "^File:", "^Help:", "^Portal:", "^Special:", "^Talk:", "^Template_talk:", "^Template:", "^User:", "^Wikipedia:")) {
  used_titles <- grep(special, used_titles, invert = TRUE, value = TRUE)
}
# Save the unique titles
unique_titles <- unique(used_titles)
writeLines(unique_titles, "wikipedia_titles.txt")
