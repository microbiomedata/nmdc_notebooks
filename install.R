### install regular packages

install.packages(c("rmarkdown", "caTools", "bitops")) # for knitting
install.packages(c("jsonlite", "dplyr", "tidyr", "ggplot2", "forcats", "lubridate", "maps")) # for data wrangling

### install bioconductor packages
# install.packages("BiocManager")
# BiocManager::install("package")

### install GitHub packages (tag = commit, branch or release tag)
# install.packages("devtools")
# devtools::install_github("user/repo", ref = "tag")