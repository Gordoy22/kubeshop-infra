# ---------------------------------------------------------------- Parâmetros da pipeline

variable "environment" {
  description = "Ambiente de destino (parâmetro `environment` da pipeline)."
  type        = string

  validation {
    condition     = contains(["dev", "homolog", "prod"], var.environment)
    error_message = "environment deve ser dev, homolog ou prod."
  }
}

variable "instance_name" {
  description = "Prefixo do nome das VMs (parâmetro `instance_name`). Gera <nome>-<ambiente>-app e <nome>-<ambiente>-db."
  type        = string
  default     = "kubeshop"

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{1,20}$", var.instance_name))
    error_message = "instance_name: 2 a 21 caracteres, minúsculas, números e hífen, começando por letra."
  }
}

variable "app_instance_type" {
  description = "Tipo da VM da aplicação (parâmetro `instance_type`)."
  type        = string
  default     = "t3.micro"

  validation {
    condition     = can(regex("^[a-z][a-z0-9]*\\.[a-z0-9]+$", var.app_instance_type))
    error_message = "app_instance_type inválido (ex.: t3.micro)."
  }
}

variable "db_instance_type" {
  description = "Tipo da VM exclusiva do MongoDB (parâmetro `db_instance_type`)."
  type        = string
  default     = "t3.small"

  validation {
    condition     = can(regex("^[a-z][a-z0-9]*\\.[a-z0-9]+$", var.db_instance_type))
    error_message = "db_instance_type inválido (ex.: t3.small)."
  }
}

variable "db_data_volume_gb" {
  description = "Tamanho (GiB) do volume EBS dedicado aos dados do MongoDB. Só pode aumentar."
  type        = number
  default     = 10

  validation {
    condition     = var.db_data_volume_gb >= 8 && var.db_data_volume_gb <= 500
    error_message = "db_data_volume_gb deve ficar entre 8 e 500."
  }
}

variable "ssh_public_key" {
  description = "Chave pública SSH administrativa (derivada do secret SSH_PRIVATE_KEY pela pipeline)."
  type        = string

  validation {
    condition     = can(regex("^(ssh-ed25519|ssh-rsa|ecdsa-sha2-nistp256) ", var.ssh_public_key))
    error_message = "ssh_public_key precisa estar no formato OpenSSH."
  }
}

# ---------------------------------------------------------------- Configuração geral

variable "aws_region" {
  description = "Região AWS."
  type        = string
  default     = "us-east-2"
}

variable "project" {
  description = "Nome curto do projeto."
  type        = string
  default     = "kubeshop"
}

variable "availability_zone" {
  description = "AZ das VMs e do volume. Vazio = primeira AZ disponível da região."
  type        = string
  default     = ""
}

variable "admin_cidrs" {
  description = "CIDRs com SSH permanente na VM da aplicação (ex.: IP fixo da equipe). Vazio = SSH fechado; a pipeline abre só para o próprio runner, temporariamente."
  type        = list(string)
  default     = []

  validation {
    condition     = alltrue([for c in var.admin_cidrs : can(cidrhost(c, 0)) && c != "0.0.0.0/0"])
    error_message = "admin_cidrs deve conter CIDRs válidos e nunca 0.0.0.0/0."
  }
}

variable "root_volume_gb" {
  description = "Disco do sistema de cada VM (GiB)."
  type        = number
  default     = 20
}

variable "use_nat_gateway" {
  description = "true = NAT Gateway gerenciado (~US$ 33/mês). false = a VM da aplicação faz NAT para a sub-rede privada (sem custo extra)."
  type        = bool
  default     = false
}
