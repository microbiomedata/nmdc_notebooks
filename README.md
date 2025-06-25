# NMDC Data and Metadata R and Python Sample Jupyter Notebooks

## Quick Start
Notebooks that are ready for use and exploration.

- [NEON Soil MetaData](https://github.com/microbiomedata/nmdc_notebooks/tree/main/NEON_soil_metadata)
- [Bio-Scales Biogeochemical MetaData](https://github.com/microbiomedata/nmdc_notebooks/tree/main/bioscales_biogeochemical_metadata)
- [NEON Soil Microbial Community Composition](https://github.com/microbiomedata/nmdc_notebooks/tree/main/taxonomic_dist_by_soil_layer)
- [Natural Organic Matter Composition by Sample Type](https://github.com/microbiomedata/nmdc_notebooks/tree/main/NOM_visualizations)
- [Proteomic Data Aggregation](https://github.com/microbiomedata/nmdc_notebooks/tree/main/proteomic_aggregation)
- [Proteomic Overrepresentation](https://github.com/microbiomedata/nmdc_notebooks/tree/main/over_representation)
- [Omics Types Data Integration](https://github.com/microbiomedata/nmdc_notebooks/tree/main/omics_types_integration)


## Overview 

This repository includes Jupyter Notebooks that explore and analyze microbiome data from the National Microbiome Data Collaborative's (NMDC) data portal. These notebooks aim to:

- highlight the NMDC's metadata and data
- demonstrate how the NMDC's API may be used to retrieve metadata and data of various microbiome research
- illustrate example use cases of using the NMDC's (meta)data to answer scientific questions
- encourage scientists to programmatically access the NMDC Data Portal
- promote the accessiblity of microbiome research by demonstrating various modes of finding, accessing, and reusing existing microbiome data.

Each folder's scope attempts to explore a scientific question using the NMDC's (meta)data. A folder includes a `README.md` that outlines the question or analysis posed as well as two sub-folders, one labeled `R`, and the other `python` that comprises the sample notebooks using the R and Python programming languages, respectively. 

R and Python were chosen since they are popular languages among scientists to explore and visualize data. Jupyter Notebook paired with Google Colab is used because of its interactive code and data exploration features, effectiveness in teaching, language independency, and ease of sharing code.

A challenging aspect that has been highlighted with this process is accessing the (meta)data in a user-friendly way via the NMDC API. Because the NMDC metadata schema is highly modular, retrieving metadata is not straightforward without extensive knowledge of the metadata schema's infrastructure, modeling language ([LinkML](https://linkml.io/)), and naming conventions. A proposed solution to this challenge is the creation of R and Python packages that would allow users to access NMDC's data in an easier and more straightforward way. The Python package used in the notebooks is being developed here: https://github.com/microbiomedata/nmdc_api_utilities

## Contributing

We welcome contributions to this repository. Please see the [Contributing document](.github/CONTRIBUTING.md) for more information on how to contribute.



