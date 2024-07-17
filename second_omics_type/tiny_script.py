import requests
import pandas as pd

def get_first_page_results(collection: str, filter: str, max_page_size: int, fields: str):
    og_url = f'https://api.microbiomedata.org/nmdcschema/{collection}?&filter={filter}&max_page_size={max_page_size}&projection={fields}'
    resp = requests.get(og_url)
    data = resp.json()
    
    return data

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
            url = f'https://api.microbiomedata.org/nmdcschema/{collection}?&filter={filter}&max_page_size={max_page_size}&page_token={next_page_token}&projection={fields}'
            response = requests.get(url)
            data_next = response.json()
            
            results = data_next.get("resources", [])
            result_list.extend(results)
            next_page_token = data_next.get("next_page_token")
        
            if not next_page_token:
                break

    return result_list

def convert_df(results_list: list):

    df = pd.DataFrame(results_list)

    return df

# pull all NOM data objects
all_dataobj=get_next_results(collection='data_object_set',\
                       filter='{"data_object_type":{"$regex": "FT ICR-MS Analysis Results"}}',\
                        max_page_size=100,fields='id,url,was_generated_by')

# clarify names
for dataobject in all_dataobj:
    dataobject["nom_dataobj_id"] = dataobject.pop("id")

# convert to df
all_dataobj_df = convert_df(all_dataobj)
all_dataobj_df
