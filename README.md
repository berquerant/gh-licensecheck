# gh-licensecheck

Suggest outbound licenses based on the licenses of the dependencies.

## Usage

``` shell
❯ gh licensecheck --help
Suggest outbound licenses based on the licenses of the dependencies.

gh licensecheck TARGET [FLAGS]
  Extract dependencies which hosted on GitHub, suggest licenses based on them.
  See gh licensecheck outbound --help for FLAGS.

gh licensecheck outbound [FLAGS]
  Read dependency repos from stdin, suggest outbound licenses.
  Repo is a string like astral-sh/uv (owner/repo).
  See gh licensecheck outbound --help for FLAGS.

gh licensecheck extract TARGET
  Extract direct dependencies which hosted on GitHub.

TARGET: go, pipenv, rust

The Dependencies are read from the following file:
- go: go.mod
- pipenv: Pipfile
- rust: Cargo.toml
```

## Installation

``` shell
uv sync
gh extension install .
```
