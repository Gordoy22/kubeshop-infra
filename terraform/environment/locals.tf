data "aws_caller_identity" "current" {}

data "aws_availability_zones" "available" {
  state = "available"
}

# Ubuntu Server 24.04 LTS oficial (Canonical). A AMI só é lida na criação:
# `ignore_changes = [ami]` nas instâncias evita recriar VMs quando sair AMI nova.
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"]

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

locals {
  name_prefix = "${var.instance_name}-${var.environment}"

  # Faixas de rede diferentes por ambiente para permitirem coexistir (e um peering futuro).
  vpc_cidrs = {
    dev     = "10.20.0.0/16"
    homolog = "10.30.0.0/16"
    prod    = "10.40.0.0/16"
  }
  vpc_cidr     = local.vpc_cidrs[var.environment]
  public_cidr  = cidrsubnet(local.vpc_cidr, 8, 1) # x.x.1.0/24 -> VM da aplicação
  private_cidr = cidrsubnet(local.vpc_cidr, 8, 2) # x.x.2.0/24 -> VM do banco

  # IPs privados fixos: a API sempre encontra o banco no mesmo endereço,
  # mesmo que a VM do banco seja recriada.
  app_private_ip = cidrhost(local.public_cidr, 10)
  db_private_ip  = cidrhost(local.private_cidr, 10)

  az = var.availability_zone != "" ? var.availability_zone : data.aws_availability_zones.available.names[0]

  # Mesmo nome calculado pela stack global (sem dependência de state entre stacks).
  backup_bucket = "${var.project}-backups-${data.aws_caller_identity.current.account_id}-${var.aws_region}"

  common_tags = {
    Project     = "KubeShop"
    Owner       = "Zibiska Korp"
    Environment = var.environment
    ManagedBy   = "Terraform"
    Stack       = "environment"
    Repository  = "kubeshop-infra"
  }
}
