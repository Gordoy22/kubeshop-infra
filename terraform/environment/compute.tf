# -----------------------------------------------------------------------------
# Máquinas virtuais: VM 1 (aplicação) e VM 2 (MongoDB exclusivo).
# -----------------------------------------------------------------------------

resource "aws_key_pair" "admin" {
  key_name   = "${local.name_prefix}-admin"
  public_key = var.ssh_public_key
  tags       = { Name = "${local.name_prefix}-admin" }
}

# ---------------------------------------------------------------- VM 1: aplicação
resource "aws_instance" "app" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.app_instance_type
  subnet_id              = aws_subnet.public.id
  private_ip             = local.app_private_ip
  vpc_security_group_ids = [aws_security_group.app.id]
  key_name               = aws_key_pair.admin.key_name

  # Necessário para a VM encaminhar (NAT) o tráfego de saída da sub-rede privada.
  source_dest_check = false

  metadata_options {
    http_tokens                 = "required" # IMDSv2 obrigatório
    http_put_response_hop_limit = 1
    http_endpoint               = "enabled"
  }

  root_block_device {
    volume_type           = "gp3"
    volume_size           = var.root_volume_gb
    encrypted             = true
    delete_on_termination = true
    tags                  = { Name = "${local.name_prefix}-app-root" }
  }

  tags = {
    Name = "${local.name_prefix}-app"
    Role = "app"
  }

  # AMI nova ou troca da chave SSH não recriam a VM (ver docs/05).
  lifecycle {
    ignore_changes = [ami, key_name]
  }
}

resource "aws_eip" "app" {
  domain   = "vpc"
  instance = aws_instance.app.id
  tags     = { Name = "${local.name_prefix}-app-eip" }

  depends_on = [aws_internet_gateway.main]
}

# ---------------------------------------------------------------- VM 2: MongoDB
resource "aws_instance" "db" {
  ami                         = data.aws_ami.ubuntu.id
  instance_type               = var.db_instance_type
  subnet_id                   = aws_subnet.private.id
  private_ip                  = local.db_private_ip
  associate_public_ip_address = false # REQ-02: sem IP público
  vpc_security_group_ids      = [aws_security_group.db.id]
  key_name                    = aws_key_pair.admin.key_name
  iam_instance_profile        = aws_iam_instance_profile.db.name

  metadata_options {
    http_tokens                 = "required"
    http_put_response_hop_limit = 1
    http_endpoint               = "enabled"
  }

  root_block_device {
    volume_type           = "gp3"
    volume_size           = var.root_volume_gb
    encrypted             = true
    delete_on_termination = true
    tags                  = { Name = "${local.name_prefix}-db-root" }
  }

  tags = {
    Name = "${local.name_prefix}-db"
    Role = "db"
  }

  lifecycle {
    ignore_changes = [ami, key_name]
  }
}
