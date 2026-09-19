param([string]$Model = "qwen3:8b")
if (-not (Get-Command ollama -ErrorAction SilentlyContinue)) {
  Write-Host "Ollama is not installed. Download it from https://ollama.com/download"
  exit 1
}
Write-Host "Pulling $Model ..."
ollama pull $Model
Write-Host "Testing local model..."
ollama run $Model "Reply with exactly: AGENT READY"
