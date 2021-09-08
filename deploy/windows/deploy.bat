@echo off

set passhfiles_dir=%cd%

rem the directory that will contain the python + deps + passhfiles
set target_dir=%passhfiles_dir%\ci-install

rem the path to python executable
set python_exe=%target_dir%\python.exe

for /F "tokens=*" %a in ('.\ci-install\python.exe -c "exec(open('.\src\passhfiles\__pkginfo__.py').read()) ; print(__version__)"') do set VERSION=%a

echo %VERSION%> version

set target_dir=%passhfiles_dir%\ci-install

rem copy the LICENSE and CHANGELOG files
copy %passhfiles_dir%\LICENSE %passhfiles_dir%\deploy\windows
copy %passhfiles_dir%\CHANGELOG.md %passhfiles_dir%\deploy\windows\CHANGELOG.txt

rem the path to nsis executable
set makensis="C:\Program Files (x86)\NSIS\Bin\makensis.exe"
set nsis_installer=%passhfiles_dir%\deploy\windows\installer.nsi

del /Q %target_dir%\passhfiles-%version%-win-amd64.exe

%makensis% /V4 /Onsis_log.txt /DVERSION=%version% /DARCH=win-amd64 /DTARGET_DIR=%target_dir% %nsis_installer%
