#!/usr/bin/bash 

set -e -o pipefail
pandoc README.md --from markdown --to rst -o README.rst
grep -q -F 0.1.1 README.rst
