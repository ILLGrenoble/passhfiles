@echo off

set passhfiles_dir=%cd%

set version=%CI_COMMIT_REF_NAME%

echo %version% > version

set target_dir=%passhfiles_dir%\ci-install

rem copy the LICENSE and CHANGELOG files
copy %passhfiles_dir%\LICENSE %passhfiles_dir%\deploy\windows
copy %passhfiles_dir%\CHANGELOG.md %passhfiles_dir%\deploy\windows\CHANGELOG.txt

rem the path to nsis executable
set makensis="C:\Program Files (x86)\NSIS\Bin\makensis.exe"
set nsis_installer=%passhfiles_dir%\deploy\windows\installer.nsi

del /Q %target_dir%\passhfiles-%version%-win-amd64.exe

%makensis% /V4 /Onsis_log.txt /DVERSION=%version% /DARCH=win-amd64 /DTARGET_DIR=%target_dir% %nsis_installer%
