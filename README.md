# gh-licensecheck

Suggest outbound licenses based on the licenses of the dependencies.

## Usage

``` shell
❯ gh licensecheck --help
Suggest outbound licenses based on the licenses of the dependencies.

gh licensecheck TARGET [FLAGS]
  Extract dependencies in go.mod which hosted on GitHub, suggest licenses based on them.
  See gh licensecheck outbound --help for FLAGS.

gh licensecheck outbound [FLAGS]
  Read dependency repos from stdin, suggest outbound licenses.
  Repo is a string like astral-sh/uv (owner/repo).
  See gh licensecheck outbound --help for FLAGS.

gh licensecheck extract TARGET
  Extract direct dependencies in go.mod which hosted on GitHub.

TARGET: go, pipenv
```

## Installation

``` shell
uv sync
gh extension install .
```
