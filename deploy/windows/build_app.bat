@echo off

set current_dir=%cd%

rem the path to the python installer executable
set python_installer=%1

rem the path to the git directory for bastion_browser
set git_dir=%2

rem the version to install
set version=%3

rem the directory that will contain the python + deps + bastion_browser
set target_dir=%4

rem uninstall python
%python_installer% /quiet /uninstall

rem remove(if existing) target directory
rmdir /S /Q %target_dir%

rem create the target directory that will contains the python installation
mkdir %target_dir%

rem install python to the select target directory
%python_installer% /quiet TargetDir=%target_dir%

rem the path to pip executable
set pip_exe=%target_dir%\Scripts\pip.exe

rem install dependencies
%pip_exe% install -r %git_dir%\requirements.txt

rem the path to python executable
set python_exe=%target_dir%\python.exe

rem cleanup previous installations
cd %target_dir%\Lib\site-packages
for /f %%i in ('dir /a:d /S /B bastion_browser*') do rmdir /S /Q %%i
del /Q %target_dir%\Scripts\bastion_browser

rem checkout selected version of the bastion_browser project
set git_exe="C:\Program Files\Git\bin\git.exe"
cd %git_dir%
%git_exe% fetch --all
%git_exe% checkout %version%

rem build and install bastion_browser using the python installed in the target directory
rmdir /S /Q %git_dir%\build
%python_exe% setup.py build install

rem copy the LICENSE and CHANGELOG files
copy %git_dir%\LICENSE %git_dir%\deploy\windows
copy %git_dir%\CHANGELOG.md %git_dir%\deploy\windows\CHANGELOG.txt

rem the path to nsis executable
set makensis="C:\Program Files (x86)\NSIS\Bin\makensis.exe"
set nsis_installer=%git_dir%\deploy\windows\installer.nsi

del /Q %target_dir%\bastion_browser-%version%-win-amd64.exe

%makensis% /V4 /Onsis_log.txt /DVERSION=%version% /DARCH=win-amd64 /DTARGET_DIR=%target_dir% %nsis_installer%

cd %current_dir%
