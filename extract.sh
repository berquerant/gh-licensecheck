#!/bin/bash

d="$PWD"

extract_from_gomod() {
    gomod="${d}/go.mod"

    read_packages() {
        grep -v "^$" "$gomod" |\
            grep -v "indirect" |\
            grep -v '^module' |\
            grep -E '^(require|\s)' |\
            grep -v '^require ($' |\
            sed -e 's|^\t||' -e 's|^require ||'
    }

    read_packages | grep -v -F "github.com" | while read -r repo ; do echo "IGNORE: ${repo}" ; done > /dev/stderr
    read_packages | grep -F "github.com" | awk '{print $1}' | cut -d "/" -f2,3
}

extract_from_pipfile() {
    pipfile="${d}/Pipfile"

    read_package_names() {
        awk '
write == 1 {
  print $1
}
$1 == "[packages]" {
  write = 1
}
$1 == "" {
  write = 0
}' "$pipfile" | grep -v "^$"
    }

    homepage_url() {
        pipenv run pip show "$1" | awk '$1 == "Home-page:" {print $2}'
    }

    list_urls() {
        read_package_names | while read -r name ; do homepage_url "$name" ; done
    }

    list_urls | grep -v -F "github.com" | while read -r url ; do echo "IGNORE: ${url}" ; done > /dev/stderr
    list_urls | grep -F "github.com" | grep -o 'github.com/.*' | cut -d "/" -f2,3
}

extract_from_cargo() {
    cargotoml="${d}/Cargo.toml"

    read_package_names() {
        awk '
write == 1 {
  print $1
}
$1 == "[dependencies]" {
  write = 1
}
$1 == "" {
  write = 0
}' "$cargotoml" | grep -v "^$"
    }

    repository() {
        cargo info "$1" | awk '$1 == "repository:" {print $2}'
    }

    list_urls() {
        read_package_names | while read -r name ; do repository "$name" ; done
    }

    list_urls | grep -v -F "github.com" | while read -r url ; do echo "IGNORE: ${url}" ; done > /dev/stderr
    list_urls | grep -F "github.com" | grep -o 'github.com/.*' | cut -d "/" -f2,3
}

case "$1" in
    "go") extract_from_gomod ;;
    "pipenv") extract_from_pipfile ;;
    "rust") extract_from_cargo ;;
    *)
        echo "Unknown argument: $1" > /dev/stderr
        exit 1
        ;;
esac
