output "environment" {
  value = var.environment
}

output "store_url" {
  description = "Endereço de acesso à loja."
  value       = "http://${aws_eip.app.public_ip}"
}

output "app_public_ip" {
  description = "Elastic IP da VM da aplicação (entrada pública única)."
  value       = aws_eip.app.public_ip
}

output "app_private_ip" {
  value = aws_instance.app.private_ip
}

output "db_private_ip" {
  description = "IP privado do MongoDB (usado pela API)."
  value       = aws_instance.db.private_ip
}

output "db_public_ip" {
  description = "Deve ser vazio: a VM do banco não tem IP público (evidência REQ-02)."
  value       = aws_instance.db.public_ip
}

output "app_security_group_id" {
  value = aws_security_group.app.id
}

output "db_security_group_id" {
  value = aws_security_group.db.id
}

output "private_subnet_cidr" {
  value = aws_subnet.private.cidr_block
}

output "db_data_volume_id" {
  description = "Volume EBS com os dados do MongoDB."
  value       = aws_ebs_volume.mongo_data.id
}

output "backup_bucket" {
  value = local.backup_bucket
}

output "aws_region" {
  value = var.aws_region
}

output "inventory" {
  description = "Inventário dos recursos (ACE-02)."
  value = {
    vpc = { id = aws_vpc.main.id, cidr = aws_vpc.main.cidr_block }
    app_vm = {
      name          = aws_instance.app.tags["Name"]
      id            = aws_instance.app.id
      instance_type = aws_instance.app.instance_type
      private_ip    = aws_instance.app.private_ip
      public_ip     = aws_eip.app.public_ip
      subnet        = "public ${aws_subnet.public.cidr_block}"
      role          = "Nginx (React) + API Node.js/Express em Docker; NAT da sub-rede privada"
    }
    db_vm = {
      name          = aws_instance.db.tags["Name"]
      id            = aws_instance.db.id
      instance_type = aws_instance.db.instance_type
      private_ip    = aws_instance.db.private_ip
      public_ip     = aws_instance.db.public_ip
      subnet        = "private ${aws_subnet.private.cidr_block}"
      role          = "MongoDB autenticado exclusivo em Docker"
      data_volume   = "${aws_ebs_volume.mongo_data.id} (${aws_ebs_volume.mongo_data.size} GiB gp3, criptografado)"
    }
    nat = var.use_nat_gateway ? "NAT Gateway gerenciado" : "VM da aplicação (NAT instance)"
  }
}
