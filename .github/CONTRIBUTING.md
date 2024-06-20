# Contributing to NMDC-notebooks

:+1: First of all: Thank you for taking the time to contribute!

The following is a set of guidelines for contributing to [nmdc_notebooks repo](https://github.com/microbiomedata/nmdc_notebooks). This guide
is aimed primarily at the developers for the notebooks and this repo, although anyone is welcome
to contribute.

## Table Of Contents

- [Code of Conduct](#code-of-conduct)
- [Guidelines for Contributions and Requests](#contributions)
    * [Reporting issues](#reporting-issues)
    * [Making pull requests](#pull-requests)
- [Best practices](#best-practices)
- [Adding new notebooks](#adding-new-notebooks)
- [Dependency Management](#dependency-management)

<a id="code-of-conduct"></a>

## Code of Conduct

The NMDC team strives to create a
welcoming environment for editors, users and other contributors.

Please carefully read NMDC's [Code of Conduct](https://github.com/microbiomedata/nmdc-schema/blob/main/CODE_OF_CONDUCT.md).

<a id="contributions"></a>

## Guidelines for Contributions and Requests

<a id="reporting-issues"></a>

### Reporting issues with exisiting notebooks

Please use the [Issue Tracker](https://github.com/microbiomedata/nmdc_notebooks/issues/) for reporting problems or suggest enhancements for the notebooks. Issues should be focused and actionable (a PR could close an issue). Complex issues should be broken down into simpler issues where possible.

Please review GitHub's overview article,
["Tracking Your Work with Issues"][about-issues].

### Pull Requests

See [Pull Requests](https://github.com/microbiomedata/nmdc-schema/pulls/) for all pull requests. Every pull request should be associated with an issue.

Please review GitHub's article, ["About Pull Requests"][about-pulls],
and make your changes on a [new branch][about-branches].

We recommend also reading [GitHub Pull Requests: 10 Tips to Know](https://blog.mergify.com/github-pull-requests-10-tips-to-know/)

## Best Practices

<a id="best-practices"></a>

- Read ["About Issues"][about-issues] and ["About Pull Requests"][about-pulls]
- Issues should be focused and actionable
- Bugs should be reported with a clear description of the problem and steps to reproduce.  If bugs are found within a notebook, please include the link to the notebook in the issue and the specific cell that is causing the issue.
- Complex issues should be broken down into simpler issues where possible
- Pull Requests (PRs) should be atomic and aim to close a single issue
- PRs should reference issues following standard conventions (e.g. “Fixes #123”)
- Never work on the main branch, always work on an issue/feature branch
- Core developers can work on branches off origin rather than forks
- If possible create a draft or work-in-progress PR on a branch to maximize transparency of what you are doing
- PRs should be reviewed and merged in a timely fashion
- In the case of git conflicts, the contributor should try and resolve the conflict


[about-branches]: https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/about-branches
[about-issues]: https://docs.github.com/en/issues/tracking-your-work-with-issues/about-issues
[about-pulls]: https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/about-pull-requests

## Adding new notebooks

<a id="adding-new-notebooks"></a>

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
5. Run the entire notebook to ensure it is working as expected and save the *rendered* notebook in the folder.
6. Update the `README.md` in the folder to include links to the rendered notebook (using [nbviewer](https://nbviewer.org/) and [google colab](https://colab.research.google.com/)).


## Dependency Management

<a id="dependency-management"></a>

### R

This project uses `renv` for package management.  After cloning the github repository, open the R project and run `renv::restore()` to make sure your packages match. To learn more about how renv works, [see this resource](https://rstudio.github.io/renv/articles/renv.html).

### Python

This project uses pip paired with venv to manage dependencies. Note that requirements_dev.txt should be used and updated for local development dependencies, and requirements.txt should be used for production/binder dependencies (updated manually and with discretion).

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
