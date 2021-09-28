if ($env:GITHUB_REF -like "refs/heads/*") {
    $BRANCH_OR_TAG = $env:GITHUB_REF.substring(11)
} else {
    if ($env:GITHUB_REF -like "refs/tags/*") {
        $BRANCH_OR_TAG = $env:GITHUB_REF.substring(10)
    } else {
        write-output "Unknown branch or tag"
        exit 1
    }
}

copy LICENSE .\deploy\windows
copy CHANGELOG.md .\deploy\windows\CHANGELOG.txt

$MAKENSIS="C:\Program Files (x86)\NSIS\Bin\makensis.exe"
$NSIS_CONFIG_FILE=".\deploy\windows\installer.nsi"

$PYTHON_ROOT="C:\\Python39"

$PASSHFILES_INSTALLER = -join("passhfiles-",$BRANCH_OR_TAG,"-win-amd64.exe")
del $PASSHFILES_INSTALLER

$CMD = "& `"$MAKENSIS`" /V4 /Onsis_log.txt /DARCH=win-amd64 /DVERSION=$BRANCH_OR_TAG /DTARGET_DIR=$PYTHON_ROOT $NSIS_CONFIG_FILE"
invoke-expression $CMD

mv "$PYTHON_ROOT\$PASSHFILES_INSTALLER" .
