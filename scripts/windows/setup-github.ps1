# Configura TUDO no GitHub de uma vez (rode uma unica vez, na pasta do projeto):
#   1. cria o repositorio e envia o codigo
#   2. gera a chave SSH administrativa e as senhas do MongoDB (aleatorias)
#   3. grava tudo como GitHub Secrets (nada fica no codigo; as senhas nao sao exibidas)
#   4. pede as chaves da AWS (digitadas por voce, ocultas) e grava como Secrets
#   5. define as variaveis do repositorio (regiao etc.)
#
# Uso:  powershell -ExecutionPolicy Bypass -File scripts\windows\setup-github.ps1
#       [-RepoName kubeshop-infra] [-Visibility public|private] [-Region us-east-2]
param(
  [string]$RepoName = "kubeshop-infra",
  [ValidateSet("public", "private")][string]$Visibility = "public",
  [string]$Region = "us-east-2",
  [switch]$RotateDbPasswords
)
# Comandos externos (gh, git) escrevem avisos no stderr; no PowerShell 5.1 "Stop" os tornaria fatais.
# Os erros sao tratados pelo codigo de saida ($LASTEXITCODE) e por throw.
$ErrorActionPreference = "Continue"
$env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [Environment]::GetEnvironmentVariable("Path", "User")

function Step($m) { Write-Host "`n==> $m" -ForegroundColor Cyan }
function Ok($m)   { Write-Host "    [ok] $m" -ForegroundColor Green }
function New-RandomSecret {
  $b = New-Object byte[] 32
  [System.Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($b)
  ($b | ForEach-Object { $_.ToString("x2") }) -join ""
}
function Set-GhSecret($name, $value) {
  gh secret set $name --repo $script:Repo --body $value | Out-Null
  if ($LASTEXITCODE -ne 0) { throw "Falha ao gravar o secret $name" }
  Ok "secret $name gravado"
}

$root = Resolve-Path (Join-Path $PSScriptRoot "..\..") -ErrorAction Stop
Set-Location $root -ErrorAction Stop

foreach ($c in "git", "gh", "ssh-keygen") {
  if (-not (Get-Command $c -ErrorAction SilentlyContinue)) { throw "$c nao encontrado. Rode antes scripts\windows\install-tools.ps1" }
}

# ---------------------------------------------------------------- 1. login no GitHub
Step "Login no GitHub"
gh auth status 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
  Write-Host "    Vai abrir o navegador para voce autorizar o GitHub CLI." -ForegroundColor Yellow
  gh auth login --hostname github.com --git-protocol https --web --scopes "repo,workflow,write:packages"
  if ($LASTEXITCODE -ne 0) { throw "Login no GitHub nao concluido" }
}
gh auth setup-git | Out-Null
$login = gh api user --jq .login
$uid   = gh api user --jq .id
$script:Repo = "$login/$RepoName"
Ok "autenticado como $login"

# ---------------------------------------------------------------- 2. repositorio
Step "Repositorio $script:Repo"
if (-not (Test-Path .git)) { git init -b main | Out-Null }
git config user.name  $login
git config user.email "$uid+$login@users.noreply.github.com"
git add -A
git diff --cached --quiet
if ($LASTEXITCODE -ne 0) { git commit -q -m "KubeShop: infraestrutura AWS com Terraform, Ansible e GitHub Actions" }

gh repo view $script:Repo 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
  gh repo create $script:Repo --$Visibility --source . --remote origin --push --description "KubeShop na AWS: Terraform + Ansible + GitHub Actions (PM-04)"
  if ($LASTEXITCODE -ne 0) { throw "Falha ao criar o repositorio" }
  Ok "repositorio criado e codigo enviado"
} else {
  if (-not (git remote 2>$null | Select-String -Quiet "^origin$")) { git remote add origin "https://github.com/$script:Repo.git" }
  git push -u origin main
  Ok "codigo enviado"
}

# ---------------------------------------------------------------- 3. chave SSH
Step "Chave SSH administrativa"
$sshDir = Join-Path $HOME ".ssh"
if (-not (Test-Path $sshDir)) { New-Item -ItemType Directory $sshDir | Out-Null }
$key = Join-Path $sshDir "kubeshop"
if (-not (Test-Path $key)) {
  cmd /c "ssh-keygen -t ed25519 -N `"`" -C kubeshop-pipeline -q -f `"$key`""
  if (-not (Test-Path $key)) { throw "Falha ao gerar a chave SSH" }
  Ok "chave gerada em $key (guarde: e o seu acesso administrativo)"
} else { Ok "reutilizando $key" }
$priv = ((Get-Content -Raw $key -ErrorAction Stop) -replace "`r", "").Trim() + "`n"
Set-GhSecret "SSH_PRIVATE_KEY" $priv

# ---------------------------------------------------------------- 4. senhas do MongoDB
Step "Senhas do MongoDB (geradas aleatoriamente, nunca exibidas)"
$existing = (gh secret list --repo $script:Repo --json name --jq ".[].name") -split "`n"
if ($RotateDbPasswords -or -not ($existing -contains "MONGO_ROOT_PASSWORD")) {
  Set-GhSecret "MONGO_ROOT_PASSWORD" (New-RandomSecret)
  Set-GhSecret "MONGO_APP_PASSWORD"  (New-RandomSecret)
} else {
  Ok "senhas ja existem (mantidas). Use -RotateDbPasswords so ANTES do primeiro deploy."
}

# ---------------------------------------------------------------- 5. credenciais AWS
Step "Credenciais da AWS (usuario IAM 'kubeshop-pipeline')"
if ($existing -contains "AWS_ACCESS_KEY_ID") {
  $ans = Read-Host "    Ja existem credenciais AWS. Substituir? (s/N)"
} else { $ans = "s" }
if ($ans -match "^[sS]") {
  $ak = Read-Host "    Cole o Access key ID"
  $sk = Read-Host "    Cole o Secret access key (fica oculto)" -AsSecureString
  $skPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($sk))
  if ($ak -notmatch "^(AKIA|ASIA)[A-Z0-9]{16}$") { throw "Access key ID com formato inesperado" }
  Set-GhSecret "AWS_ACCESS_KEY_ID" $ak.Trim()
  Set-GhSecret "AWS_SECRET_ACCESS_KEY" $skPlain.Trim()
  $skPlain = $null
}

# ---------------------------------------------------------------- 6. variaveis
Step "Variaveis do repositorio"
gh variable set AWS_REGION --repo $script:Repo --body $Region | Out-Null
Ok "AWS_REGION = $Region"
gh variable set APP_REPOSITORY --repo $script:Repo --body "LaercioMLB/kube-shop-v2" | Out-Null
Ok "APP_REPOSITORY = LaercioMLB/kube-shop-v2"

Write-Host "`nPronto! Repositorio: https://github.com/$script:Repo" -ForegroundColor Green
Write-Host "Proximo passo: aba Actions > '2 - Infra - Provisionar / Atualizar' > Run workflow" -ForegroundColor Green
Write-Host "Ou pelo terminal:  gh workflow run infra-deploy.yml --repo $script:Repo -f environment=dev" -ForegroundColor Green
