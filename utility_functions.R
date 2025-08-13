# This function provides a general-purpose way to make an API request to 
# NMDC's runtime API. Note that this function will only return the first page 
# of results. The function's input includes the name of the collection 
# to access (e.g. biosample_set), the filter to be performed, the maximum page 
# size, and a list of the fields to be retrieved. 
# It returns the metadata as a dataframe.

get_first_page_results <- function(collection, filter, max_page_size, fields) {
  og_url <- paste0(
      'https://api.microbiomedata.org/nmdcschema/', 
      collection, '?&filter=', filter, '&max_page_size=', max_page_size, '&projection=', fields
      )
  
  response <- jsonlite::fromJSON(URLencode(og_url, repeated = TRUE))
  
  return(response)
}


# The get_all_results function uses the get_first_page_results function, 
# defined above, to retrieve the rest of the results from a call with multiple 
# pages. It takes the same inputs as the get_first_page_results function above:
# the name of the collection to be retrieved, the filter string, the maximum 
# page size, and a list of the fields to be returned. This function returns the
# results as a single dataframe (can be nested). It uses the next_page_token 
# key in each page of results to retrieve the following page.

get_all_results <- function(collection, filter_text, max_page_size, fields) {
  initial_data <- get_first_page_results(collection, filter_text, max_page_size, fields)
  results_df <- initial_data$resources
  
  if (!is.null(initial_data$next_page_token)) {
    next_page_token <- initial_data$next_page_token
    
    while (TRUE) {
      url <- paste0('https://api.microbiomedata.org/nmdcschema/', collection, '?&filter=', filter_text, '&max_page_size=', max_page_size, '&page_token=', next_page_token, '&projection=', fields)
      response <- jsonlite::fromJSON(URLencode(url, repeated = TRUE))

      results_df <- results_df %>% bind_rows(response$resources)
      next_page_token <- response$next_page_token
      
      if (is.null(next_page_token)) {
        break
      }
    }
  }
  
  return(results_df)
}


# This function constructs a different type of API request that takes a list of
# IDs and uses them to retrieve related data. In short, it searches in 
# `collection` for records that have elements of `id_list` in their 
# `match_id_field`, then returns all `fields` for the matching records.
# Fields such as `has_input` or `has_output` are likely to be useful values 
# for `match_id_field`, though other fields are also usable.

get_results_by_id <- function(collection, match_id_field, id_list, fields, max_page_size = 50) {
    # collection: the name of the collection to query
    # match_id_field: the field in the new collection to match to the id_list
    # id_list: a vector of ids to filter on
    # fields: field names to return - a single string of field names separated by commas, no spaces
    # max_page_size: the maximum number of records to return in a single query
    
    # If id_list is longer than max page size, split it into chunks of max_page_size
    if (length(id_list) > max_page_size) {
        id_list <- split(id_list, ceiling(seq_along(id_list)/max_page_size))
    } else {
        id_list <- list(id_list)
    }
    
    output <- list()
    for (i in 1:length(id_list)) {
        # Cast as a character vector and add double quotes around each ID
        mongo_id_string <- as.character(id_list[[i]]) %>%
            paste0('"', ., '"') %>%
            paste(collapse = ', ')
        
        # Create the filter string
        filter = paste0('{"', match_id_field, '": {"$in": [', mongo_id_string, ']}}')
        
        # Get the data
        output[[i]] = get_all_results(
            collection = collection,
            filter = filter,
            max_page_size = max_page_size, 
            fields = fields
        )
    }
    output_df <- bind_rows(output)
}


# The functions above rely on knowing the MongoDB "collection" to search for 
# relevant objects. But what if you don't know what the collection is called? 
# This function takes an NMDC ID and returns the collection that the object is 
# part of.

get_collection_by_id <- function(id) {
  
  # Create API endpoint URL
  url <- paste0("https://api.microbiomedata.org/nmdcschema/ids/", id, "/collection-name")

  # Retrieve the JSON result from the API endpoint URL
  response <- jsonlite::fromJSON(URLencode(url, repeated = TRUE))
  
  # Extract the collection name from the response
  return(response$collection_name)
}


# This function returns all data objects associated with all biosamples associated 
# with the provided study ID. Study IDs can be found in the URL of a study page in 
# the NMDC data portal. For example, for the study shown at 
# https://data.microbiomedata.org/details/study/nmdc:sty-11-8xdqsn54
# study_id = "nmdc:sty-11-8xdqsn54"
# study_id must include the "nmdc:" prefix.

get_data_objects_for_study <- function(study_id) {
  # Create API endpoint URL
  url <- paste0("https://api.microbiomedata.org/data_objects/study/", study_id)
  
  # Retrieve the JSON result from the API endpoint URL
  response <- jsonlite::fromJSON(URLencode(url, repeated = TRUE))
  
  # Response is a nested dataframe, return flattened
  return(unnest(response, cols = c(data_objects)))
}

# This function takes a vector of processed sample and/or biosample IDs and 
# returns the first biosample in the chain. It iterates through MaterialProcessing
# records to get the has_input and has_output sample IDs and adds them to a dataframe.
# It returns the final (rightmost) value in each row and checks that they are all 
# biosample IDs.
# May need work to handle pooled biosamples.

get_bsm_source_for_procsm <- function(data_df, procsm_column) {
  
  # Pull out all of the processed sample IDs to start from
  id_vec <- data_df[[procsm_column]][str_which(data_df[[procsm_column]], "nmdc:procsm-")]
  
  # Starting variables
  joined_df <- data.frame(starting_sample = data_df[[procsm_column]])
  join_colname <- "starting_sample"
  counter <- 1
  
  # As long as there are still processed samples left in the id list...
  while(length(id_vec) > 0) {

    # Assemble column names
    id_colname <- paste0("mp.id.", counter)
    in_colname <- paste0("mp.has_input.", counter)
    out_colname <- paste0("mp.has_output.", counter)
    
    # Query material processing steps
    material_processing_steps <- get_results_by_id(
      collection = "material_processing_set",
      match_id_field = "has_output",
      id_list = id_vec,
      fields = "id,has_input,has_output",
      max_page_size = 20
      ) %>%
      
      # Flatten results for viewing
      mutate(has_input = unlist(has_input)) %>%
      unnest(cols = has_output) %>%
      distinct() %>%
      
      # Rename columns for consistency
      dplyr::rename_with(
        .fn = function(x) return(c(id_colname, in_colname, out_colname)),
        .cols = c(id, has_input, has_output))
    
    # Add to last round of data
    joined_df <- left_join(
      joined_df, material_processing_steps,
      by = join_by({{join_colname}} == {{out_colname}}))
    
    # Assign next join colname
    join_colname <- in_colname

    # Create next ID list
    id_vec <- material_processing_steps[[in_colname]][str_which(material_processing_steps[[in_colname]], "nmdc:procsm-")]

    # Increment loop counter
    counter <- counter + 1
  }
  
  # Find last value in each row (terminal/source biosample) and return that vector
  last_value <- function(x) tail(x[!is.na(x)], 1)
  source_biosample_vec <- apply(joined_df, 1, last_value)

  # Check that the last value in each row was actually a biosample. If not,
  # something has gone awry and someone familiar with the NMDC database
  # needs to troubleshoot
  stopifnot(str_detect(source_biosample_vec, "nmdc:bsm-"))

  return(source_biosample_vec)
}