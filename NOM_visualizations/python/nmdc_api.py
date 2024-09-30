#!venv/bin python

#packages used in these functions
import requests
import pandas as pd

## Define a general API call function to nmdc-runtime
    # This function provides a general-purpose way to make an API request to NMDC's runtime API. Note that this 
    # function will only return the first page of results. The function's input includes the name of the collection to access (e.g. `biosample_set`), 
    # the filter to be performed, the maximum page size, and a list of the fields to be retrieved. It returns the metadata as a json object.

def get_first_page_results(collection: str, filter: str, max_page_size: int, fields: str):
    #TODO: update branch to main after berkely rollout
    og_url = f'https://api-berkeley.microbiomedata.org/nmdcschema/{collection}?&filter={filter}&max_page_size={max_page_size}&projection={fields}'
    resp = requests.get(og_url)
    data = resp.json()
    
    return data


## Define an nmdc-runtime API call function to include pagination
    # The `get_next_results` function uses the `get_first_page_results` function, defined above, 
    # to retrieve the rest of the results from a call with multiple pages. It takes the same inputs as 
    # the `get_first_page_results` function above: the name of the collection to be retrieved, the filter string, 
    # the maximum page size, and a list of the fields to be returned. This function returns the list of the results.
    # It uses the `next_page_token` key in each page of results to retrieve the following page.

def get_next_results(collection: str, filter: str, max_page_size: int, fields: str):

    # Get initial results (before next_page_token is given in the results)
    result_list = []
    initial_data = get_first_page_results(collection, filter, max_page_size, fields)
    results = initial_data["resources"]
    
    # append first page of results to an empty list
    for result in results:
        result_list.append(result)
    
    # if there are multiple pages of results returned
    if initial_data.get("next_page_token"):
        next_page_token = initial_data["next_page_token"]

        while True:
            #TODO: update branch to main after berkely rollout
            url = f'https://api-berkeley.microbiomedata.org/nmdcschema/{collection}?&filter={filter}&max_page_size={max_page_size}&page_token={next_page_token}&projection={fields}'
            response = requests.get(url)
            data_next = response.json()
            
            results = data_next.get("resources", [])
            result_list.extend(results)
            next_page_token = data_next.get("next_page_token")
        
            if not next_page_token:
                break

    return result_list

# Define a data frame convert function
    # This function converts a list (for example, the output of the `get_first_page_results` or the `get_next_results` function) into 
    # a dataframe using Python's Pandas library. It returns a data frame.

def convert_df(results_list: list):

    df = pd.DataFrame(results_list)

    return df

## Define a function to split a list into chunks 
    # Since we will need to use a list of ids to query a new collection in the API, we need to limit the number of ids we put in a query. 
    # This function splits a list into chunks of 100. Note that the `chunk_size` has a default of 100, but can be adjusted.

def split_list(input_list, chunk_size=100):
    result = []
    
    for i in range(0, len(input_list), chunk_size):
        result.append(input_list[i:i + chunk_size])
        
    return result


## Define a function to use double quotation marks
    # Since the mongo-like filtering criteria for the API requests require double quotation marks (") instead of 
    # single quotation marks ('), a function is defined to replace single quotes with double quotes to properly 
    # structure a mongo filter paramter. The function takes a list (usually of ids) and returns a string with the 
    # ids listed with double quotation marks. E.g the input is `['A','B','C']` and the output would be `'"A","B",C"'`.

def string_mongo_list(a_list: list):
    
    string_with_double_quotes = str(a_list).replace("'", '"')

    return string_with_double_quotes


## Define a function to get a list of ids from initial results
    # In order to use the identifiers retrieved from an initial API request in another API request, this function is defined to 
    # take the initial request results and use the `id_name` key from the results to create a list of all the ids. The input 
    # is the initial result list and the name of the id field.

def get_id_list(result_list: list, id_name: str):
    id_list = []
    for item in result_list:
        if type(item[id_name]) == str:
            id_list.append(item[id_name])
        elif type(item[id_name]) == list:
            for another_item in item[id_name]:
                id_list.append(another_item)

    return id_list


## Define an API request function that uses a list of ids to filter a new collection
    # This function takes the `newest_results` request (e.g. `biosamples`) and 
    # constructs a list of ids using `get_id_results`.
    # It then uses the `split_list` function to chunk the list of ids into sets of 100 to query the API. 
    # `id_field` is a field in `newest_results` containing the list of ids to search for in the query_collection (e.g. `biosample_id`).
    # `match_id_field` is the field in query_collection that will be searched. query_fields is a list of the fields to be returned.

def get_id_results(newest_results: list, id_field: str, query_collection: str, match_id_field: str, query_fields: str):

    # split old results into list
    result_ids = get_id_list(newest_results, id_field)

    # chunk up the results into sets of 100 using the split_list function and call the get_first_page_results function and append
    # results to list
    chunked_list = split_list(result_ids)
    next_results = []
    for chunk in chunked_list:
        filter_string = string_mongo_list(chunk)
        # quotes around match_id_field need to look a lot different for the final data object query
        if "data_object_type" in match_id_field:
            data = get_first_page_results(query_collection, f'{{{match_id_field}: {{"$in": {filter_string}}}}}', 100, query_fields)
        else: 
            data = get_first_page_results(query_collection, f'{{"{match_id_field}": {{"$in": {filter_string}}}}}', 100, query_fields)
        next_results.extend(data["resources"])

    return next_results


## Define a merging function to join results
    # This function merges new results with the previous results that were used for the new API request. It uses two keys from each result to match on. `df1` 
    # is the data frame whose matching `key1` value is a STRING. `df2` is the other data frame whose matching `key2` has either a string OR list as a value. 
    # df1_explode_list and df2_explode_list are optional lists of columns in either dataframe that need to be exploded because they are lists (this is because 
    # drop_duplicates cant take list input in any column). Note that each if statement includes dropping duplicates after merging as the dataframes are being 
    # exploded which creates many duplicate rows after merging takes place.

def merge_df(df1, df2, key1: str, key2: str,df1_explode_list=None,df2_explode_list=None):
    if df1_explode_list is not None:
        # Explode the lists in the df (necessary for drop duplicates)
        for list in df1_explode_list:
            df1 = df1.explode(list)
    if df2_explode_list is not None:
        # Explode the lists in the df (necessary for drop duplicates)
        for list in df2_explode_list:
            df2 = df2.explode(list)  
    # Merge dataframes
    merged_df=pd.merge(df1,df2,left_on=key1, right_on=key2)
    # Drop any duplicated rows
    merged_df.drop_duplicates(keep="first", inplace=True)
    return(merged_df)


