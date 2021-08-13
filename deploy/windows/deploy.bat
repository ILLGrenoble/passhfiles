@echo off

set bastion_browser_dir=%1%

set version=%2%

set target_dir=%bastion_browser_dir%\ci-install

rem copy the LICENSE and CHANGELOG files
copy %bastion_browser_dir%\LICENSE %bastion_browser_dir%\deploy\windows
copy %bastion_browser_dir%\CHANGELOG.md %bastion_browser_dir%\deploy\windows\CHANGELOG.txt

rem the path to nsis executable
set makensis="C:\Program Files (x86)\NSIS\Bin\makensis.exe"
set nsis_installer=%bastion_browser_dir%\deploy\windows\installer.nsi

del /Q %target_dir%\bastion_browser-%version%-win-amd64.exe

%makensis% /V4 /Onsis_log.txt /DVERSION=%version% /DARCH=win-amd64 /DTARGET_DIR=%target_dir% %nsis_installer%
