# Function definitions for /R/proteomic_aggregation.ipynb

# Function that takes a peptide sequence (s: string) and 
# returns the same sequence but without any prefix or suffix.
trim_peptide_sequence <- function(s) {
  str_match(s, "\\.([A-Z\\\\*@#]+)\\.")[, 2]
}


# Function that extracts the feature annotations column from
# GFF3 format files located at the provided address (url: string)
gff_extract_features <- function(url) {
  
  withCallingHandlers(
    expr = {
      
      tsv_df <- suppressWarnings(read_tsv(url, col_names = FALSE, progress = FALSE, show_col_types = FALSE))
      
      colnames(tsv_df) <- c("seqname", "source", "feature", "start", "end", "score", "strand", "frame", "attribute") 
      # See https://www.ensembl.org/info/website/upload/gff.html for GFF format specification
      
      # Break "attribute" column by separator
      tsv_df <- strsplit(tsv_df$attribute, split = ";") %>%
        lapply(strsplit, split = "=") %>%
        lapply(function (x) { 
          a <- do.call(rbind, x) %>%
            t() %>%
            data.frame()
          colnames(a) <- a[1, ]
          a[-1, ] }) %>%
        bind_rows() %>%
        distinct()
    },
    error = function(e) print(paste("Error while reading GFF from", url, ":", e))
  )
  return(tsv_df)
}


# Function that takes a dataframe (input_df: data.frame) with a column of urls
# (url_col: a column name in input_df, string) and a column of dataset identifiers
# (identifier_col: a column name in input_df, string) and returns a data.frame
# of the desired columns (extract_cols: character vector) from each file in url_col.
# Use file_type (str) to specify "tsv" or "gff" files.
# Use filter_col (column name, str) and filter_values (vector) to filter the 
# output data.frame.
iterate_file_extract <- function(input_df, identifier_col, url_col, 
                                 extract_cols, file_type, 
                                 filter_col = NA, filter_values = NA) {
  
  output <- vector(mode = "list", length = nrow(input_df))

  for (row in 1:nrow(input_df)) {
    
    # Extract url and id for readability
    file_url <- input_df[[url_col]][row]
    identifier <- input_df[[identifier_col]][row]
    
    tryCatch(
      expr = {
        if(file_type == "tsv") {
          df <- read_tsv(file_url, show_col_types = FALSE, progress = FALSE)
          }
        if (file_type == "gff") {
          df <- gff_extract_features(file_url)
        }
      },
      error = function(e) print(paste("An error occurred fetching data from", identifier, ":", e))
    )
    
    # Check that the subsetted df will have unique rows, otherwise break
    if(nrow(df) != nrow(distinct(df[extract_cols]))) {
      print(paste("Selected columns result in non-unique rows for ", identifier, ". Data will not be included in output."))
      break
    }
    
    # Subset data frame to desired columns
    df <- df[extract_cols]
    
    # Filter if specified
    if (!is.na(filter_col) & all(is.na(filter_values))) {
      df <- filter(df, {{filter_col}} %in% filter_values)
    }
    
    # Add identifier column
    df <- mutate(df, id = identifier)
    
    # Append to list
    output[[row]] <- df
  }
  return(bind_rows(output))
}


# Function that implements a spectral probability filter (specprob: numeric) and 
# returns a value representing the impact on FDR of using specprob as the filter.
# Takes two data.frames (forward_peptides, reversed_peptides) to calculate FDR.
spec_filt_value <- function(specprob, forward_peptides, reversed_peptides) {

  df_r <- filter(reversed_peptides, MSGFDB_SpecEValue < 10 ^ specprob)
  df_f <- filter(forward_peptides, MSGFDB_SpecEValue < 10 ^ specprob)

  f_spec <- length(unique(df_f$SpecID))
  r_spec <- length(unique(df_r$SpecID))
  
  fdr_spec <- ifelse(f_spec == 0 & r_spec == 0,
                     1,
                     (2 * r_spec) / (f_spec + r_spec))
    
  filter_value <- 1 / (0.050001 - fdr_spec) * (-f_spec)
  
  return(filter_value)
}


# Function that returns a spectral probability filter that optimizes the number
# of forward peptides retained, given an FDR of 0.05. Takes an initial filter 
# value (initial_specprob_filter: numeric) and two data.frames (forward_peptides, reversed_peptides)
optimize_spec_filt <- function(initial_specprob_filter, forward_peptides, reversed_peptides) {

 result <- optim(fn = spec_filt_value, par = initial_specprob_filter, 
          forward_peptides = forward_peptides, reversed_peptides = reversed_peptides,
           method = "Brent", lower = -100, upper = 100)
 
 # Brent method for optim() function always returns 0 (success) for convergence
}


# Function taking a dataframe of all peptide to protein mappings and 
# returning a dataframe of peptide to razor protein mappings.
# Rules for 'razor protein' are as follows:
# - If a peptide is unique to a protein, then that is the razor
# - If a peptide belongs to more than one protein, but one of those proteins 
#   has a unique peptide, then that protein is the razor
# - If a peptide belongs to more than one protein and one of those proteins has
#   has the maximal number of peptides, then that protein is the razor
# - If a peptide belongs to more than one protein and more than one of those 
#   proteins has the maximal number of peptides, then collapse the proteins and
#   gene annotations into single strings
# - If a peptide belongs to more than one protein and more than one of those 
#   proteins has a unique peptide, then the peptide is removed from analysis 
#   because its mapping is inconclusive
# Takes a mapping dataframe (mapping_df) with a row for each unique peptide to 
# protein mapping and columns 'Peptide Sequence with Mods' and 'Protein'
# Returns a mapping dataframe with a row for each unique peptide to razor 
# protein mapping
get_razor_protein <- function(mapping_df) {
    
  # Make the mapping df into named vectors for easier indexing
  
  # Names = peptides, values = number of proteins the peptide maps to
  a <- distinct(mapping_df, Peptide_Sequence_with_Mods, prot_count)
  prot_count_vec <- setNames(a$prot_count, a$Peptide_Sequence_with_Mods)
  
  # Names = peptides, values = proteins
  pep_prot_vec <- setNames(mapping_df$Protein, nm = mapping_df$Peptide_Sequence_with_Mods)
  
  # Create vector of all peptides for readability
  pep_vec <- a$Peptide_Sequence_with_Mods
  rm(a)
  

  # Pre allocate results list
  razor_result <- vector(mode = "list", length = length(pep_vec))
  
  # Iterate through peptides to choose a razor protein for each one
  for (pep in 1:length(pep_vec)) {
    
    query_peptide <- pep_vec[pep]
    
    # If the peptide only maps to one protein, that is the razor protein
    if (prot_count_vec[query_peptide] == 1) { razor_result[[pep]] <- pep_prot_vec[query_peptide] }
    
    # If the peptide maps to more than one protein and ...
    else {
      mapping_subset <- filter(mapping_df, Peptide_Sequence_with_Mods == query_peptide)
      prots_with_unique_peptides <- sum(mapping_subset$unique_pep_count > 0)
      
      razor_result[[pep]] <- case_when(
        
        # ...there is only one potential protein with unique peptides, that is the razor protein
        prots_with_unique_peptides == 1 ~ mapping_subset$Protein[which.max(mapping_subset$unique_pep_count)],
        
        # ...there is more than one potential protein with unique peptides, razor protein cannot be determined
        prots_with_unique_peptides > 1  ~ "indeterminate - discard",
        
        # ...there are no potential proteins with unique peptides, 
        # and ONE potential protein has the most redundant peptides, that is the razor protein
        # note: which.max returns the FIRST maximum index which in this case should be the only one
        prots_with_unique_peptides == 0 & 
          sum(mapping_subset$redundant_pep_count == max(mapping_subset$redundant_pep_count)) == 1 ~ 
          mapping_subset$Protein[which.max(mapping_subset$redundant_pep_count)],
        
        # ...there are no potential proteins with unique peptides, 
        # and more than one potential protein has the most redundant peptides, those are the razor proteins
        # note: which ( blah == max(blah) ) will return ALL of the maximum indices
        prots_with_unique_peptides == 0 &
          sum(mapping_subset$redundant_pep_count == max(mapping_subset$redundant_pep_count)) > 1 ~ 
          mapping_subset$Protein[which(mapping_subset$redundant_pep_count == max(mapping_subset$redundant_pep_count))],
        
        # there should be no cases not captured
        TRUE ~ "fix razor logic until you don't see this"
      )
    }
    razor_result[[pep]] <- data.frame(Peptide = query_peptide,
                                      Razor_Protein = razor_result[[pep]], 
                                      row.names = NULL)
  }
  # Bind into one long dataframe
  bind_rows(razor_result, .id = NULL) %>%
    
    # Discard indeterminate cases
    filter(Razor_Protein != "indeterminate - discard") %>%
    
    # Add the protein annotations back in
    left_join(select(mapping_df, Protein, product, product_source, Peptide_Sequence_with_Mods),
              by = join_by(Razor_Protein == Protein, Peptide == Peptide_Sequence_with_Mods)) %>%
    distinct()
}