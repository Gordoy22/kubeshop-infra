variable "aws_region" {
  description = "Região AWS onde os recursos são criados."
  type        = string
  default     = "us-east-2"
}

variable "project" {
  description = "Nome curto do projeto (prefixo dos recursos)."
  type        = string
  default     = "kubeshop"
}

variable "backup_retention_days" {
  description = "Dias que cada backup permanece no S3 antes de expirar."
  type        = number
  default     = 30

  validation {
    condition     = var.backup_retention_days >= 7 && var.backup_retention_days <= 365
    error_message = "A retenção deve ficar entre 7 e 365 dias."
  }
}

variable "force_destroy_backups" {
  description = "Permite apagar o bucket mesmo com backups dentro (use só na desativação completa)."
  type        = bool
  default     = false
}
