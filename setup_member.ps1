<#
Give ONE clone the identity of a tutorial member, to play members A, B and C on one PC.

    .\setup_member.ps1 C:\work\epss-git-demo\memberB\epss-git-tutorial-g00
    .\setup_member.ps1 <clone> -Undo

Reads a .env (see .env.example) from the clone folder or, if absent, from its parent folder.
Everything is set in that clone only (git config --local, files inside .git, an ignored
.vscode/settings.json). Global git settings and other clones are untouched. Without a .env
nothing is changed, which is the students' situation: they use their own sign-in.
The token stays in the .env: git reads it from there at push time.
#>
param(
  [Parameter(Mandatory)][string]$Clone,
  [switch]$Undo
)
$ErrorActionPreference = 'Stop'
$Clone = (Resolve-Path $Clone).Path
if (-not (Test-Path (Join-Path $Clone '.git'))) { throw "$Clone is not a git clone." }
$helper = Join-Path $Clone '.git\git-credential-env.sh'
$settings = Join-Path $Clone '.vscode\settings.json'
$mark = '// written by setup_member.ps1'

function Git { git.exe -C $Clone @args }  # .exe: a bare "git" here would call this function again
# how this PowerShell passes an empty argument to a program
$empty = if ($PSVersionTable.PSVersion -ge [version]'7.3' -and $PSNativeCommandArgumentPassing -ne 'Legacy') { '' } else { '""' }

if ($Undo) {
  Git config --local --unset-all credential.helper 2>$null
  Git config --local --unset user.name 2>$null
  Git config --local --unset user.email 2>$null
  if (Test-Path $helper) { Remove-Item $helper }
  if ((Test-Path $settings) -and ((Get-Content $settings -TotalCount 1) -eq $mark)) { Remove-Item $settings }
  Write-Host "Member identity removed from $Clone"
  return
}

$envFile = @((Join-Path $Clone '.env'), (Join-Path (Split-Path $Clone -Parent) '.env')) | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $envFile) { Write-Host "No .env in $Clone or its parent: nothing changed."; return }

$cfg = @{}
foreach ($line in Get-Content $envFile) {
  if ($line -match '^\s*([A-Z_]+)\s*=\s*(.*?)\s*$') { $cfg[$Matches[1]] = $Matches[2].Trim('"') }
}
foreach ($k in 'MEMBER', 'GIT_USER_NAME', 'GIT_USER_EMAIL') { if (-not $cfg[$k]) { throw "$k is missing in $envFile" } }
$member = $cfg['MEMBER'].ToUpper()
$colour = @{ A = '#1d4ed8'; B = '#15803d'; C = '#c2410c' }[$member]
if (-not $colour) { throw "MEMBER must be A, B or C (found '$member')." }

Git config --local user.name $cfg['GIT_USER_NAME']
Git config --local user.email $cfg['GIT_USER_EMAIL']

if ($cfg['GITHUB_TOKEN']) {
  # sh needs LF line endings whatever the checkout produced
  $sh = (Get-Content (Join-Path $PSScriptRoot 'git-credential-env.sh') -Raw) -replace "`r`n", "`n"
  [IO.File]::WriteAllText($helper, $sh)
  # an empty first value discards the system helper (Git Credential Manager) for this clone
  Git config --local --unset-all credential.helper 2>$null
  Git config --local --add credential.helper $empty
  Git config --local --add credential.helper ("!sh '{0}' '{1}'" -f ($helper -replace '\\', '/'), ($envFile -replace '\\', '/'))
  if (@(Git config --local --get-all credential.helper)[0] -ne '') { throw 'Could not reset the credential helper for this clone.' }
  try {
    $who = Invoke-RestMethod 'https://api.github.com/user' -Headers @{ Authorization = "Bearer $($cfg['GITHUB_TOKEN'])"; 'User-Agent' = 'setup-member' }
    if ($cfg['GITHUB_USER'] -and $who.login -ne $cfg['GITHUB_USER']) { Write-Warning "The token belongs to '$($who.login)', but GITHUB_USER says '$($cfg['GITHUB_USER'])'." }
    else { Write-Host "Token accepted by GitHub for user '$($who.login)'." }
  } catch { Write-Warning "GitHub did not accept the token: $($_.Exception.Message)" }
} else {
  Write-Host 'No GITHUB_TOKEN in the .env: pushes use your normal sign-in (fine for member A = you).'
}

if ((Test-Path $settings) -and ((Get-Content $settings -TotalCount 1) -ne $mark)) {
  Write-Warning "$settings exists and is not mine: window colour not set."
} else {
  New-Item -ItemType Directory -Force (Split-Path $settings) | Out-Null
  @"
$mark
{
  "window.title": "MEMBER $member `${separator}`${activeEditorShort}`${separator}`${rootName}",
  "workbench.colorCustomizations": {
    "titleBar.activeBackground": "$colour", "titleBar.activeForeground": "#ffffff",
    "titleBar.inactiveBackground": "$colour", "titleBar.inactiveForeground": "#ffffffcc",
    "statusBar.background": "$colour", "statusBar.foreground": "#ffffff",
    "activityBar.activeBorder": "$colour"
  },
  "github.gitAuthentication": false,
  "git.terminalAuthentication": false
}
"@ | Set-Content $settings -Encoding utf8
}

Write-Host ("Member {0}: {1} <{2}> in {3}" -f $member, $cfg['GIT_USER_NAME'], $cfg['GIT_USER_EMAIL'], $Clone)
