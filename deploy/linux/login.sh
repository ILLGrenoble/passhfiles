#!/bin/bash

# Log in to github
echo ${ILL_GITHUB_TOKEN} | gh auth login --with-token
