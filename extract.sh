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

    read_packages | grep -v -F "github.com" | while read repo ; do echo "IGNORE: ${repo}" ; done > /dev/stderr
    read_packages | grep -F "github.com" | awk '{print $1}' | cut -d "/" -f2,3
}

case "$1" in
    "go") extract_from_gomod ;;
    *)
        echo "Unknown argument: $1" > /dev/stderr
        exit 1
        ;;
esac
