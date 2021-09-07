#!/bin/bash

#############################
# Create DMG
#############################

cd ${CI_PROJECT_DIR}

rm -rf ${CI_PROJECT_DIR}/venvs/passhfiles

rm -rf ${CI_PROJECT_DIR}/build

rm -rf ${CI_PROJECT_DIR}/dist

virtualenv -p python3 ${CI_PROJECT_DIR}/venvs/passhfiles

source ${CI_PROJECT_DIR}/venvs/passhfiles/bin/activate

pip install .

pip install py2app

python3 setup.py py2app --packages cffi

VERSION_NAME=`python -c "exec(open('${CI_PROJECT_DIR}/src/passhfiles/__pkginfo__.py').read()) ; print(__version__)"`

cd ${CI_PROJECT_DIR}/deploy/macos

PASSHFILES_DMG=PASSHFILES-${VERSION_NAME}-macOS-amd64.dmg
hdiutil unmount /Volumes/passhfiles -force -quiet
sleep 5
${CI_PROJECT_DIR}/depoy/macos/create-dmg --background "${CI_PROJECT_DIR}/deploy/macos/resources/dmg/dmg_background.jpg" \
                                         --volname "passhfiles" \
										 --window-pos 200 120 \
										 --window-size 800 400 \
										 --icon passhfiles.app 200 190 \
										 --hide-extension passhfiles.app \
										 --app-drop-link 600 185 \
										 "${PASSHFILES_DMG}" \
										 ${CI_PROJECT_DIR}/dist
