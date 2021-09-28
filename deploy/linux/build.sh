#!/bin/bash

rm -rf .env

virtualenv -p python3.8 .env

source .env/bin/activate

pip install appimage-builder

pip install .