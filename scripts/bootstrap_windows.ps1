$ErrorActionPreference = 'Stop'
Push-Location (Join-Path $PSScriptRoot '..')
try { python scripts/bootstrap_models.py @args; if ($LASTEXITCODE -ne 0) { throw 'Model bootstrap failed' } }
finally { Pop-Location }
