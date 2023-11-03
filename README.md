# NMDC Data and Metadata R and Python Sample Jupyter Notebooks

## Overview 

This repository includes jupyter notebooks that explore and analyze microbiome data from the National Microbiome Data Collaborative's (NMDC) data portal. These notebooks aim to:

- highlight the NMDC's metadata and data
- demonstrate how the NMDC's API may be used to retrieve metadata and data of various microbiome research
- illustrate example use cases of using the NMDC's (meta)data to answer scientific questions
- encourage scientists to programmaticly access the NMDC Data Portal
- promote the accessiblity of microbiome research by demonstrating various modes of finding, accessing, and reusing existing microbiome data.

Each folder's scope attempts to explore a scientific question using the NMDC's (meta)data. A folder includes a `README.md` that outlines the question or analysis posed as well as two sub-folders, one labeled `R`, and the other `python` that comprises the sample notebooks using the R and Python programming languages, respectively. 

R and Python were chosen since they are popular languages among scientists to explore and visualize data. Jupyter Notebook is used because of its interactive code and data exploration features, effectiveness in teaching, language independency, and ease of sharing code.

A challenging aspect that has been highlighted with this process is accessing the (meta)data in a user-friendly way via the NMDC API. Because the NMDC metadata schema is highly modular, retrieving metadata is not straight forward without extensive knowledge of the metadata schema's infrastructure, modeling language ([LinkML](https://linkml.io/)), and naming conventions. A proposed solution to this challenge is the creation of an R or Python package that would allow users to access NMDC's data in an easier and more straight forward way.

## Adding new notebooks

To add a new notebook to this repository:

1.  Create a folder in the base directory 
    - Name the folder with a short version of the analysis/question that will be explored.
    - Make name of folder `snake_case`
2. Create a `README.md` in the folder outlining the analysis or question.
3. Create a sub-folder for each language that will be demonstrated
    - e.g. one subfolder named `R` and one subfolder named `python`
4. Instantiate a Jupyter Notebook for each folder coded in its corresponding language
_or_
4. Create a .Rmd and convert it to a Jupyter Notebook. Several methods for this exist and none are perfect, but [this open source method](https://github.com/mkearney/rmd2jupyter) currently works.

## Dependency Management

### R

This project uses `renv` for package management.  After cloning the github repository, open the R project and run `renv::restore()` to make sure your packages match. To learn more about how renv works, [see this resource](https://rstudio.github.io/renv/articles/renv.html).

### Python

This project uses pip paired with venv to manage dependencies. Note that requirements_dev.txt should be used for development dependencies, and requirements.txt should be used for production/binder dependencies (added manually and with discretion).

#### To install the dependencies:

1. Clone the github repository
2. create a virtual environment:
    `python -m venv venv`
3. Activate the virtual environment:
    `source venv/bin/activate`
4. Install the necessary packages:
    `pip install -r requirements_dev.txt`
    **Note** to update your package installations:
        `pip install -U -r requirements_dev.txt`

#### To add new packages:

1. Activate the virtual environment:
    `source venv/bin/activate`
2. Install any new packages:
    `pip install <package>`
3. Capture the new requirements:
    `pip freeze > requirements_dev.txt`
4. Push changes to github


### RStudio (for R)
[Binder](http://mybinder.org/badge.svg)](http://mybinder.org/v2/gh/microbiomedata/notebook_hackathons/rmd_dev?urlpath=rstudio)



