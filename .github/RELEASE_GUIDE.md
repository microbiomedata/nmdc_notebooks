# NMDC_NOTEBOOKS Release Guide

## Introduction
The following is a set of guidelines for generating releases for nmdc_notebooks. This documentation is solely for the maintainers of the nmdc_notebooks repo. A release is generated on the first business day of every month if there have been pull requests merged into main. If there are no changes on main, then no release is generated.

## Preparing for Release

### Versioning Scheme
This project adheres to the semantic versioning as outlined by [semver.org](https://semver.org/): MAJOR.MINOR.PATCH
* Patch: e.g. 1.0.1 -> 1.0.2 
   * indicates bug fixes and trivial updates
   * fixing notebook bugs or typos are examples of patch-level changes.
* Minor: e.g. 1.0.2 -> 1.1.0 
   * indicates change to functionality but is still backwards compatible 
   * examples include functionality changes, updates, adding new functionality, and potentially removing functionality depending on the degree of it.
   * Adding new notebooks and documentation and adding functionality to notebooks (such as adding a new visual, etc.) are examples of minor changes.
* Major: e.g. 1.1.0 -> 2.0.0 
   * changes the introduce breaking functionality and are not backwards compatible 
   * examples include removing deprecated code or introducing a new architecture.
   * Major updates to the notebooks architecture (such as major api endpoints and schema traversals) and removing notebooks are considered major changes.

## Release Steps 
Use [Github's documentation](https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository) to create a release by clicking on `Releases` on the repo's main page.
1. Make a new tag when drafting a new release that follows the convention `v.1.0.0`
2. Set the target branch to `main`
3. Set the previous tag as the previous release number. e.g. `v.1.2.0`
4. Generate release notes so a list of all the merge requests and contributors auto-populates.
5. Save as draft release until ready to release or publish if ready.
   * Recommend saving as draft while updating the `CHANGELOG.md`. 

## Post Release Steps
* After publishing, update the `CHANGELOG.md`, create a PR with changelog updates, review, and merge.

### Branching Strategy to update CHANGELOG.md
A release branch is a branch created for preparing for the release. This is the branch used to update the CHANGELOG.md that goes with the release
* A release branch should be named as `release-<version>`. For examples `release-v1.1.0`. 
* Update any release documentation (i.e. the CHANGELOG.md) on this branch to prepare for a release. 
* Create a PR when ready for release

### Updating the CHANGELOG.md
The `CHANGELOG.md` is formatted based on [Keep a Changelog](http://keepachangelog.com/)
The change log is meant to be easily understood by humans. It is formatted with the types of changes as subheadings for each release:
* Added
* Changed
* Deprecated
* Removed
* Fixed
* Security
The newest release should be at the top of the `CHANGELOG.md` with older releases below.

