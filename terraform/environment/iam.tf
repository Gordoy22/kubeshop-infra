# -----------------------------------------------------------------------------
# Perfil IAM da VM do banco: só pode gravar/ler backups do PRÓPRIO ambiente
# (prefixo <ambiente>/ no bucket de backups). Nenhuma chave de acesso fica na VM.
# -----------------------------------------------------------------------------

data "aws_iam_policy_document" "ec2_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "db" {
  name               = "${local.name_prefix}-db-role"
  assume_role_policy = data.aws_iam_policy_document.ec2_assume.json
}

data "aws_iam_policy_document" "db_backups" {
  statement {
    sid       = "ListOwnPrefix"
    actions   = ["s3:ListBucket"]
    resources = ["arn:aws:s3:::${local.backup_bucket}"]
    condition {
      test     = "StringLike"
      variable = "s3:prefix"
      values   = ["${var.environment}/*", "${var.environment}/"]
    }
  }

  statement {
    sid       = "ReadWriteOwnPrefix"
    actions   = ["s3:PutObject", "s3:GetObject"]
    resources = ["arn:aws:s3:::${local.backup_bucket}/${var.environment}/*"]
  }
}

resource "aws_iam_role_policy" "db_backups" {
  name   = "kubeshop-backups-${var.environment}"
  role   = aws_iam_role.db.id
  policy = data.aws_iam_policy_document.db_backups.json
}

resource "aws_iam_instance_profile" "db" {
  name = "${local.name_prefix}-db-profile"
  role = aws_iam_role.db.name
}
