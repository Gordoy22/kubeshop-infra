output "backup_bucket" {
  description = "Bucket S3 com os backups de todos os ambientes."
  value       = aws_s3_bucket.backups.bucket
}

output "backup_retention_days" {
  description = "Retenção configurada dos backups (dias)."
  value       = var.backup_retention_days
}
