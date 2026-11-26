# -----------------------------------------------------------------------------
# Armazenamento persistente do MongoDB: volume EBS separado do disco do sistema.
# Mudar o tipo da VM, recriá-la ou reiniciá-la NÃO apaga os pedidos: o volume
# é apenas desanexado e anexado de novo. Aumentar db_data_volume_gb é feito
# online (sem parar a VM) e o Ansible expande o sistema de arquivos.
# -----------------------------------------------------------------------------

resource "aws_ebs_volume" "mongo_data" {
  availability_zone = local.az
  size              = var.db_data_volume_gb
  type              = "gp3"
  encrypted         = true

  tags = {
    Name = "${local.name_prefix}-mongo-data"
    Role = "db-data"
  }
}

resource "aws_volume_attachment" "mongo_data" {
  device_name                    = "/dev/sdf"
  volume_id                      = aws_ebs_volume.mongo_data.id
  instance_id                    = aws_instance.db.id
  stop_instance_before_detaching = true
}
