# Instala as ferramentas locais necessarias (Windows 10/11) via winget.
# Terraform e Ansible rodam nos runners do GitHub Actions; localmente so precisamos
# de Git + GitHub CLI (Terraform local e opcional, para validar o codigo).
# Uso:  powershell -ExecutionPolicy Bypass -File scripts\windows\install-tools.ps1
$ErrorActionPreference = "Stop"

$tools = @(
  @{ Id = "Git.Git";             Cmd = "git" },
  @{ Id = "GitHub.cli";          Cmd = "gh" },
  @{ Id = "Hashicorp.Terraform"; Cmd = "terraform" }
)

if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
  throw "winget nao encontrado. Instale o 'App Installer' pela Microsoft Store e rode de novo."
}

foreach ($t in $tools) {
  if (Get-Command $t.Cmd -ErrorAction SilentlyContinue) {
    Write-Host "[ok] $($t.Cmd) ja instalado" -ForegroundColor Green
    continue
  }
  Write-Host "[..] instalando $($t.Id)" -ForegroundColor Cyan
  winget install --id $t.Id -e --silent --accept-package-agreements --accept-source-agreements
}

# Recarrega o PATH desta sessao
$env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [Environment]::GetEnvironmentVariable("Path", "User")

Write-Host ""
foreach ($t in $tools) {
  $c = Get-Command $t.Cmd -ErrorAction SilentlyContinue
  if ($c) { Write-Host ("[ok] {0,-10} {1}" -f $t.Cmd, $c.Source) -ForegroundColor Green }
  else    { Write-Host ("[!!] {0,-10} nao encontrado - feche e abra o terminal" -f $t.Cmd) -ForegroundColor Yellow }
}
if (-not (Get-Command ssh-keygen -ErrorAction SilentlyContinue)) {
  Write-Host "[!!] ssh-keygen ausente: ative 'Cliente OpenSSH' em Configuracoes > Sistema > Recursos opcionais" -ForegroundColor Yellow
}
