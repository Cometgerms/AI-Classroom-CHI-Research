param([ValidateSet('simulation','mac-local','windows-local','hardware-xvf')][string]$Profile = 'simulation')
$ErrorActionPreference = 'Stop'
Push-Location (Join-Path $PSScriptRoot '..')
try {
    if (!(Test-Path backend/.venv)) { python -m venv backend/.venv }
    & backend/.venv/Scripts/python.exe -m pip install -r backend/requirements.txt
    if ($LASTEXITCODE -ne 0) { throw 'Dependency install failed' }
    & backend/.venv/Scripts/python.exe -m backend --profile $Profile
    if ($LASTEXITCODE -ne 0) { throw 'Backend exited with an error' }
} finally { Pop-Location }
