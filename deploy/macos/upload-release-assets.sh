#!/bin/bash

if [[ $GITHUB_REF == refs/tags/* ]] ;
then

    REPO=${GITHUB_SERVER_URL}/${GITHUB_REPOSITORY}

    BRANCH_OR_TAG=${GITHUB_REF#refs/tags/}

    # Log in to github
    echo ${ILL_GITHUB_TOKEN} | gh auth login --with-token

    gh release upload ${BRANCH_OR_TAG} ./passhfiles-${BRANCH_OR_TAG}-macOS-amd64.dmg --repo ${REPO}

fi

