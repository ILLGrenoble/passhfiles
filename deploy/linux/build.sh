#!/bin/bash

rm -rf ./venvs

virtualenv -p python3.8 ./venvs/passhfiles

source ./venvs/passhfiles/bin/activate

pip install appimage-builder

pip install .