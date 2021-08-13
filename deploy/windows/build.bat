@echo off

set bastion_browser_dir=%cd%

rem the path to the python installer executable
set python_installer=C:\\temp\python-3.8.6.exe

rem the directory that will contain the python + deps + bastion_browser
set target_dir=C:\temp\bastion_browser-install

rem uninstall python
%python_installer% /quiet /uninstall

rem remove(if existing) target directory
rmdir /S /Q %target_dir%

rem create the target directory that will contains the python installation
mkdir %target_dir%

rem install python to the select target directory
%python_installer% /quiet TargetDir=%target_dir% Include_test=0

rem the path to pip executable
set pip_exe=%target_dir%\Scripts\pip.exe

rem install dependencies
%pip_exe% install -r %bastion_browser_dir%\requirements.txt

rem the path to python executable
set python_exe=%target_dir%\python.exe

rem build and install bastion_browser using the python installed in the target directory
rmdir /S /Q %bastion_browser_dir%\build
%python_exe% setup.py build install
