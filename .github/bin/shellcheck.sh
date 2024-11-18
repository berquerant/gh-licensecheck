#!/bin/bash

{
    git grep -l "^#\!/bin/bash"
    git ls-files | grep "\.sh$"
} | sort -u | xargs shellcheck --shell=bash
