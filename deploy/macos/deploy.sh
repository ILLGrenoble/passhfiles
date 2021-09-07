#!/bin/bash

#############################
# Create DMG
#############################

VERSION_NAME = `sed -e 's/Here\(.*\)String/\1/' ../../src/passhfiles/__pkginfo__.py`

PASSHFILES_DMG=PASSHFILES-${VERSION_NAME}-macOS-amd64.dmg
hdiutil unmount /Volumes/passhfiles -force -quiet
sleep 5
${CI_PROJECT_DIR}/depoy/macos/create-dmg --background "${CI_PROJECT_DIR}/deploy/macos/resources/dmg/dmg_background.jpg" /
                                         --volname "passhfiles" /
										 --window-pos 200 120 /
										 --window-size 800 400 /
										 --icon passhfiles.app 200 190 /
										 --hide-extension passhfiles.app /
										 --app-drop-link 600 185 /
										 "${PASSHFILES_DMG}" /
										 ${CI_PROJECT_DIR}/dist
