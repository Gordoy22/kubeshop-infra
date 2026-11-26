# Backend remoto S3 (configuração parcial).
# bucket/key/region são informados pela pipeline em `terraform init -backend-config=...`
# O bucket de state é criado e protegido por scripts/ensure-backend.sh
# (versionamento, criptografia, bloqueio de acesso público e TLS obrigatório).
# O lock usa o arquivo .tflock nativo do S3 (use_lockfile), sem DynamoDB.
terraform {
  backend "s3" {}
}
