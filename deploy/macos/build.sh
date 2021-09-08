#!/bin/bash

rm -rf ./venvs/passhfiles

rm -rf ./build

rm -rf ./dist

rm passhfiles*dmg

virtualenv -p python3 ./venvs/passhfiles

source ./venvs/passhfiles/bin/activate

pip install .

pip install py2app

python3 setup.py py2app --packages cffi
