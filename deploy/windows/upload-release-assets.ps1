if ($env:GITHUB_REF -like "refs/tags/*") {

    $REPO="$env:GITHUB_SERVER_URL/$env:GITHUB_REPOSITORY"

    $BRANCH_OR_TAG = $env:GITHUB_REF.substring(10)

    # see https://www.it-swarm-fr.com/fr/powershell/loperateur-est-reserve-pour-une-utilisation-future/968377122/ for info
    cmd /c "echo $env:ILL_GITHUB_TOKEN | gh auth login --with-token"

    gh auth status

    gh release upload ${BRANCH_OR_TAG} .\passhfiles-${BRANCH_OR_TAG}-win-amd64.exe --repo $REPO

}

