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
    
    # If id_list is longer than max_id, split it into chunks of max_id
    if (length(id_list) > max_id) {
        id_list <- split(id_list, ceiling(seq_along(id_list)/max_id))
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
  return(unnest(response))
}
