import requests
import pandas as pd
from io import StringIO
import plotly.express as px
import nmdc_api_utilities

from nmdc_api_utilities.biosample_search import BiosampleSearch
from nmdc_api_utilities.data_processing import DataProcessing
# Create a BiosampleSearch object
bs_client = BiosampleSearch()
# create a DataProcessing object
dp_client = DataProcessing()
# define the filter
filter = '{"soil_horizon":{"$exists": true}, "geo_loc_name.has_raw_value": {"$regex": "Colorado"}}'
# get the results
bs_results = bs_client.get_record_by_filter(filter=filter, fields="id,soil_horizon,geo_loc_name", max_page_size=100, all_pages=True)
# clarify names
for biosample in bs_results:
    biosample["biosample_id"] = biosample.pop("id")

# convert to df
biosample_df = dp_client.convert_to_df(bs_results)

# Adjust geo_loc_name to not be a dictionary
biosample_df["geo_loc_name"] = biosample_df["geo_loc_name"].apply(lambda x: x.get("has_raw_value"))
biosample_df

##########
print("Get all DataObjects that are related to the biosamples found in step 1")
biosample_dataobject_dictionary = bs_client.get_linked_instances_and_associate_ids(
    ids=biosample_df["biosample_id"].tolist()[0:5],
    types =["nmdc:DataObject"]
    )

# Gather all DataObject ids into a single list (from the dictionary of lists), then get their records
dojs = [item for sublist in biosample_dataobject_dictionary.values() for item in sublist]
from nmdc_api_utilities.data_object_search import DataObjectSearch
# create a DataObjectSearch object
do_client = DataObjectSearch()
do_results = do_client.get_batch_records(
    id_list=dojs,
    search_field="id",
    fields="id,data_object_type,url"
)
data_object_df = dp_client.convert_to_df(do_results)

# Filter to only include DataObjects of type "scaffold lineage tsv"
scaffold_lineage_df = data_object_df[data_object_df["data_object_type"] == "Scaffold Lineage tsv"]
scaffold_lineage_df

# Add biosample ID and associated metadata to scaffold_lineage_df using the biosample_dataobject_dictionary
# First define a function to get biosample_id from data_object_id
def get_biosample_id(data_object_id, biosample_dataobject_dict):
    for biosample_id, data_object_list in biosample_dataobject_dict.items():
        if data_object_id in data_object_list:
            return biosample_id
    return None
# Apply the function to create a new column in scaffold_lineage_df
scaffold_lineage_df["biosample_id"] = scaffold_lineage_df["id"].apply(lambda x: get_biosample_id(x, biosample_dataobject_dictionary))

# Get records of type "scaffold lineage tsv"
dobj_search = nmdc_api_utilities.dataobject_search.DataObjectSearch()
scaffold_lineage_tsv_records = []
for doj in dojs:
    record = dobj_search.get_record_by_id(doj['id'])
    if record['data_object_type'] == 'scaffold lineage tsv':
        scaffold_lineage_tsv_records.append(record)