db.getCollection("biosample_set").aggregate(
[
{$match:{'soil_horizon': {'$in': ['O horizon', 'M horizon']}}},
{
$project: {
"id": 1,
"soil_horizon": 1
}
},
{
$lookup:
{
from: "pooling_set",
localField: "id",
foreignField: "has_input",
as: "pooling_set"
}
},
{
$project: {
"id": 1,
"soil_horizon": 1,
"pooling_set.has_input": 1,
"pooling_set.has_output": 1   
}
},
{
$lookup:
{
from: "processed_sample_set",
localField: "pooling_set.has_output",
foreignField: "id",
as: "processed_sample_set"
}
},
{
$project: {
"id": 1,
"soil_horizon": 1,
"pooling_set.has_input": 1,
"pooling_set.has_output": 1,
"processed_sample_set.id": 1
}
},
{
$lookup:
{
from: "extraction_set",
localField: "processed_sample_set.id",
foreignField: "has_input",
as: "extraction_set"
}
},
{
$project: {
"id": 1,
"soil_horizon": 1,
"pooling_set.has_input": 1,
"pooling_set.has_output": 1,
"processed_sample_set.id": 1,
"extraction_set.has_input": 1,
"extraction_set.has_output": 1, 
"extraction_set.id": 1
}
},
{
$lookup:
{
from: "processed_sample_set",
localField: "extraction_set.has_output",
foreignField: "id",
as: "processed_sample_set2"
}
},
{
$project: {
"id": 1,
"soil_horizon": 1,
"pooling_set.has_input": 1,
"pooling_set.has_output": 1,
"processed_sample_set.id": 1,
"extraction_set.has_input": 1,
"extraction_set.has_output": 1, 
"extraction_set.id": 1,
"processed_sample_set2.id": 1
}
},
{
$lookup:
{
from: "library_preparation_set",
localField: "processed_sample_set2.id",
foreignField: "has_input",
as: "library_preparation_set"
}
},
{
$project: {
"id": 1,
"soil_horizon": 1,
"pooling_set.has_input": 1,
"pooling_set.has_output": 1,
"processed_sample_set.id": 1,
"extraction_set.has_input": 1,
"extraction_set.has_output": 1, 
"extraction_set.id": 1,
"processed_sample_set2.id": 1,
"library_preparation_set.has_input": 1,
"library_preparation_set.has_output": 1,
"library_preparation_set.id": 1
}
},
{
$lookup:
{
from: "processed_sample_set",
localField: "library_preparation_set.has_output",
foreignField: "id",
as: "processed_sample_set3"
}
},
{
$project: {
"id": 1,
"soil_horizon": 1,
"pooling_set.has_input": 1,
"pooling_set.has_output": 1,
"processed_sample_set.id": 1,
"extraction_set.has_input": 1,
"extraction_set.has_output": 1, 
"extraction_set.id": 1,
"processed_sample_set2.id": 1,
"library_preparation_set.has_input": 1,
"library_preparation_set.has_output": 1,
"library_preparation_set.id": 1,
"processed_sample_set3.id": 1
}
},
{
$lookup: 
{
from: "omics_processing_set",
localField: "processed_sample_set3.id",
foreignField: "has_input",
as: "omics_processing_set"
}
},
{
$project: {
"id": 1,
"soil_horizon": 1,
"pooling_set.has_input": 1,
"pooling_set.has_output": 1,
"processed_sample_set.id": 1,
"extraction_set.has_input": 1,
"extraction_set.has_output": 1, 
"extraction_set.id": 1,
"processed_sample_set2.id": 1,
"library_preparation_set.has_input": 1,
"library_preparation_set.has_output": 1,
"library_preparation_set.id": 1,
"processed_sample_set3.id": 1,
"omics_processing_set.has_input": 1,
"omics_processing_set.id": 1
}
},
{
$lookup:
{
from: "metagenome_annotation_activity_set",
localField: "omics_processing_set.id",
foreignField: "was_informed_by",
as: "metagenome_annotation_activity_set"
}
},
{
$project: {
"id": 1,
"soil_horizon": 1,
"pooling_set.has_input": 1,
"pooling_set.has_output": 1,
"processed_sample_set.id": 1,
"extraction_set.has_input": 1,
"extraction_set.has_output": 1, 
"extraction_set.id": 1,
"processed_sample_set2.id": 1,
"library_preparation_set.has_input": 1,
"library_preparation_set.has_output": 1,
"library_preparation_set.id": 1,
"processed_sample_set3.id": 1,
"omics_processing_set.has_input": 1,
"omics_processing_set.id": 1,
"metagenome_annotation_activity_set.was_informed_by": 1,
"metagenome_annotation_activity_set.has_output": 1
}
},
{
$lookup:
{
from: "data_object_set",
localField: "metagenome_annotation_activity_set.has_output",
foreignField: "id",
as: "data_object_set"
}
},
{
$project: {
"id": 1,
"soil_horizon": 1,
"pooling_set.has_input": 1,
"pooling_set.has_output": 1,
"processed_sample_set.id": 1,
"extraction_set.has_input": 1,
"extraction_set.has_output": 1, 
"extraction_set.id": 1,
"processed_sample_set2.id": 1,
"library_preparation_set.has_input": 1,
"library_preparation_set.has_output": 1,
"library_preparation_set.id": 1,
"processed_sample_set3.id": 1,
"omics_processing_set.has_input": 1,
"omics_processing_set.id": 1,
"metagenome_annotation_activity_set.was_informed_by": 1,
"metagenome_annotation_activity_set.has_output": 1,
"data_object_set.id": 1,
"data_object_set.data_object_type": "Scaffold Lineage tsv",
"data_object_set.url": 1
}
}
]
)