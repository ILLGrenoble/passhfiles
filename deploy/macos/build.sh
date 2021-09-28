#!/bin/bash

rm -rf ./.env

rm -rf ./build

rm -rf ./dist

rm passhfiles*dmg

virtualenv -p python3 ./.env

source ./.env/bin/activate

pip install .

pip install py2app

python3 setup.py py2app --packages cffi
