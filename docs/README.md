## Install
    pip install -U sphinx

## Step 1: Generate the .rst files using 'apidoc':
For details, see [sphinx-apidoc](https://www.sphinx-doc.org/en/master/man/sphinx-apidoc.html)
from inside `PHX` (root) folder, run:

    sphinx-apidoc -f -e -d 4 -o ./docs/sphinx/source/_rst ./PHX

This will generate .rst files for all of the packages and modules inside `./PHX` and store them in `./docs/source/_rst/` folder.

## Step 2: Generate the .html files from the .rst:
from inside `./docs/sphinx/` folder, run:

    make html

This will generate the new html files and store them in `./docs/build/html/...`

## Step 3: Cleanup
Be sure to delete the `./docs/sphinx/build/` and `./docs/sphinx/source/_rst/...` directories when done, or whenever regenerating the docs.
