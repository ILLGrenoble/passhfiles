#!/bin/bash

REPO=${GITHUB_SERVER_URL}/${GITHUB_REPOSITORY}

# Log in to github
echo ${ILL_GITHUB_TOKEN} | gh auth login --with-token

if [[ $GITHUB_REF == refs/tags/* ]] ;
then
    TAG=${GITHUB_REF#refs/tags/}
    gh release create ${TAG} --notes-file CHANGELOG.md --title ${TAG} --repo ${REPO}
else
    echo 'Unknown branch or tag'
    exit 1
fi
