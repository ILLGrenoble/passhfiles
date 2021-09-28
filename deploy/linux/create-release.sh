#!/bin/bash

REPO=${GITHUB_SERVER_URL}/${GITHUB_REPOSITORY}

# Log in to github
echo ${ILL_GITHUB_TOKEN} | gh auth login --with-token

if [[ $GITHUB_REF == refs/heads/* ]] ;
then
    BRANCH=${GITHUB_REF#refs/heads/}
    status=$(gh release delete ${BRANCH} -y --repo ${REPO} 2>&1)
    echo "Status: $status"
    gh release create ${BRANCH} --notes '' --title ${BRANCH} --repo ${REPO}
else
	if [[ $GITHUB_REF == refs/tags/* ]] ;
	then
        TAG=${GITHUB_REF#refs/tags/}
        gh release create ${TAG} --notes-file CHANGELOG.md --title ${TAG} --repo ${REPO}
	else
        echo 'Unknown branch or tag'
		exit 1
    fi
fi
