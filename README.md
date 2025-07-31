# NMDC Data and Metadata R and Python Jupyter Notebooks

## Examples
Notebooks that are available:

- [NEON Soil MetaData](https://github.com/microbiomedata/nmdc_notebooks/tree/main/NEON_soil_metadata)
- [Bio-Scales Biogeochemical MetaData](https://github.com/microbiomedata/nmdc_notebooks/tree/main/bioscales_biogeochemical_metadata)
- [NEON Soil Microbial Community Composition](https://github.com/microbiomedata/nmdc_notebooks/tree/main/taxonomic_dist_by_soil_layer)
- [Natural Organic Matter Composition by Sample Type](https://github.com/microbiomedata/nmdc_notebooks/tree/main/NOM_visualizations)
- [Proteomic Data Aggregation](https://github.com/microbiomedata/nmdc_notebooks/tree/main/proteomic_aggregation)
- [Proteomic Overrepresentation](https://github.com/microbiomedata/nmdc_notebooks/tree/main/over_representation)
- [Omics Types Data Integration](https://github.com/microbiomedata/nmdc_notebooks/tree/main/omics_types_integration)


## Overview 

This repository provides Jupyter Notebooks that illustrate how NMDC’s standardized sample metadata, experimental process structured metadata, and workflow annotations can be leveraged for multi-omic investigation of microbiome samples.

A key goal of these notebooks is to provide examples of navigating the NMDC database. Because the NMDC schema is highly modular, retrieving metadata and data programmatically via the NMDC API requires knowledge of the metadata schema's infrastructure, modeling language ([LinkML](https://linkml.io/)), and naming conventions. To address this challenge, we created R and Python notebooks and a Python package to help our users access NMDC's data in an easy and straightforward way. 

The notebooks demonstrate:
- how to programmatically query and retrieve metadata and data using the NMDC’s API
- how to use the [nmdc_api_utilities](https://github.com/microbiomedata/nmdc_api_utilities) package to make NMDC API requests easier
- example use cases of querying the NMDC’s (meta)data store to locate data of interest, visualize the data in the context of sample metadata, explore data annotations (e.g., taxonomy, chemical formula assignments), and aggregate related data (e.g., data generated within a comparative study, various omics data from the same sample)

Each notebook’s scope is framed by a straightforward scientific question and has a folder with a `README.md` that outlines the question or analysis posed as well as two sub-folders, one labeled `R`, and the other `python` that comprises the sample notebooks using the R and Python programming languages, respectively. Jupyter Notebook is paired with Google Colab to provide interactive code and data exploration features, language independency, and ease of sharing code. 

## Contributing

We welcome feedback and contributions to this repository. Please see the [Contributing document](.github/CONTRIBUTING.md) for more information.



