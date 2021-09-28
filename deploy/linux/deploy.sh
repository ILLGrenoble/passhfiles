#!/bin/bash

if [[ $GITHUB_REF == refs/heads/* ]] ;
then
    VERSION=${GITHUB_REF#refs/heads/}
else
	if [[ $GITHUB_REF == refs/tags/* ]] ;
	then
		VERSION=${GITHUB_REF#refs/tags/}
	else
		exit 1
	fi
fi

source .env/bin/activate

cd deploy/linux

# Remove previous images
rm passhfiles-*-x86_64.AppImage*

sed -i "s/version: 0.0.0/version: ${VERSION}/g" AppImageBuilder.yml

# Run app builder
appimage-builder

mv passhfiles-*-x86_64.AppImage ${GITHUB_WORKSPACE}