get_first_page_results <- function(collection, filter, max_page_size, fields) {
  og_url <- paste0(
      'https://api.microbiomedata.org/nmdcschema/', 
      collection, '?&filter=', filter, '&max_page_size=', max_page_size, '&projection=', fields
      )
  
  response <- jsonlite::fromJSON(URLencode(og_url, repeated = TRUE))
  
  return(response)
}

get_next_results <- function(collection, filter_text, max_page_size, fields) {
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

get_results_by_id <- function(collection, match_id_field, id_list, fields, max_id = 50) {
    # collection: the name of the collection to query
    # match_id_field: the field in the new collection to match to the id_list
    # id_list: a list of ids to filter on
    # fields: a list of fields to return
    # max_id: the maximum number of ids to include in a single query
    
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
        output[[i]] = get_next_results(
            collection = collection,
            filter = filter,
            max_page_size = max_id*3, #assumes that there are no more than 3 records per query
            fields = fields
        )
    }
    output_df <- bind_rows(output)
}

get_collection_by_id <- function(id) {
  
  # Create API endpoint URL
  url <- paste0("https://api.microbiomedata.org/nmdcschema/ids/", id, "/collection-name")

  # Retrieve the JSON result from the API endpoint URL
  response <- jsonlite::fromJSON(URLencode(url, repeated = TRUE))
  
  # Extract the collection name from the response
  return(response$collection_name)
}