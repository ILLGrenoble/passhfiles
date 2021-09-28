$PYTHON_ROOT="C:\\Python39"

$PIP_EXE = -join($PYTHON_ROOT,"\Scripts\pip.exe")

$CMD = -join($PIP_EXE," ","-r .\requirements.txt")
invoke-expression $CMD

$PYTHON_EXE = -join($PYTHON_ROOT,"\python.exe")

rmdir .\build
rmdir .\dist
$CMD = -join($PYTHON_EXE," setup.py build install")
invoke-expression $CMD
