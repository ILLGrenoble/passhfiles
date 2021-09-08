#!/bin/bash

#############################
# Create DMG
#############################

VERSION_NAME=`python -c "exec(open('./src/passhfiles/__pkginfo__.py').read()) ; print(__version__)"`

echo ${VERSION} > version

PASSHFILES_DMG=passhfiles-${VERSION_NAME}-macOS-amd64.dmg
hdiutil unmount /Volumes/passhfiles -force -quiet
sleep 5
./deploy/macos/create-dmg --background "./deploy/macos/resources/dmg/dmg_background.jpg" \
                                                     --volname "passhfiles" \
									             	 --window-pos 200 120 \
										 			 --window-size 800 400 \
										 			 --icon passhfiles.app 200 190 \
										 			 --hide-extension passhfiles.app \
										 			 --app-drop-link 600 185 \
										 			 "${PASSHFILES_DMG}" \
										 			 ./dist
