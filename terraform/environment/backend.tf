# Backend remoto S3 (configuração parcial). A pipeline informa:
#   bucket       = kubeshop-tfstate-<conta>-<região>   (criado por scripts/ensure-backend.sh)
#   key          = kubeshop/<ambiente>/terraform.tfstate (um state por ambiente)
#   region       = <região>
#   use_lockfile = true   (lock nativo no S3, impede execuções simultâneas)
#   encrypt      = true
terraform {
  backend "s3" {}
}
