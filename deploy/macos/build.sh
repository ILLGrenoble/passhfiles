#!/bin/bash

cd ${CI_PROJECT_DIR}

rm -rf ${CI_PROJECT_DIR}/venvs/passhfiles

rm -rf ${CI_PROJECT_DIR}/build

rm -rf ${CI_PROJECT_DIR}/dist

virtualenv -p python3 ${CI_PROJECT_DIR}/venvs/passhfiles

source ${CI_PROJECT_DIR}/venvs/passhfiles/bin/activate

pip install .

pip install py2app

python3 setup.py py2app --packages cffi
