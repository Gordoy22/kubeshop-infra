# -----------------------------------------------------------------------------
# Security Groups. As regras são recursos separados (aws_vpc_security_group_*_rule)
# para que a regra TEMPORÁRIA de SSH do runner (criada e removida pela pipeline)
# não apareça como "drift" no plan.
# -----------------------------------------------------------------------------

resource "aws_security_group" "app" {
  name        = "${local.name_prefix}-sg-app"
  description = "VM da aplicacao: HTTP publico, SSH restrito, NAT para a subrede privada"
  vpc_id      = aws_vpc.main.id
  tags        = { Name = "${local.name_prefix}-sg-app" }
}

resource "aws_security_group" "db" {
  name        = "${local.name_prefix}-sg-db"
  description = "VM do MongoDB: 27017 e SSH somente a partir da VM da aplicacao"
  vpc_id      = aws_vpc.main.id
  tags        = { Name = "${local.name_prefix}-sg-db" }
}

# ------------------------------------------------------------------ app: entrada
resource "aws_vpc_security_group_ingress_rule" "app_http" {
  security_group_id = aws_security_group.app.id
  description       = "Loja KubeShop (HTTP publico)"
  ip_protocol       = "tcp"
  from_port         = 80
  to_port           = 80
  cidr_ipv4         = "0.0.0.0/0"
}

resource "aws_vpc_security_group_ingress_rule" "app_ssh_admin" {
  for_each          = toset(var.admin_cidrs)
  security_group_id = aws_security_group.app.id
  description       = "SSH administrativo permanente (admin_cidrs)"
  ip_protocol       = "tcp"
  from_port         = 22
  to_port           = 22
  cidr_ipv4         = each.value
}

# NAT: a VM da aplicação recebe o tráfego de saída HTTP/HTTPS da VM do banco.
resource "aws_vpc_security_group_ingress_rule" "app_nat_from_db" {
  for_each                     = var.use_nat_gateway ? toset([]) : toset(["80", "443"])
  security_group_id            = aws_security_group.app.id
  description                  = "NAT: saida ${each.value}/tcp da VM do banco"
  ip_protocol                  = "tcp"
  from_port                    = tonumber(each.value)
  to_port                      = tonumber(each.value)
  referenced_security_group_id = aws_security_group.db.id
}

# ------------------------------------------------------------------ app: saída
resource "aws_vpc_security_group_egress_rule" "app_all" {
  security_group_id = aws_security_group.app.id
  description       = "Saida liberada (pacotes, imagens, NAT do banco)"
  ip_protocol       = "-1"
  cidr_ipv4         = "0.0.0.0/0"
}

# ------------------------------------------------------------------ db: entrada
resource "aws_vpc_security_group_ingress_rule" "db_mongo_from_app" {
  security_group_id            = aws_security_group.db.id
  description                  = "MongoDB somente a partir da VM da aplicacao (rede privada)"
  ip_protocol                  = "tcp"
  from_port                    = 27017
  to_port                      = 27017
  referenced_security_group_id = aws_security_group.app.id
}

resource "aws_vpc_security_group_ingress_rule" "db_ssh_from_app" {
  security_group_id            = aws_security_group.db.id
  description                  = "SSH administrativo via salto (ProxyJump) pela VM da aplicacao"
  ip_protocol                  = "tcp"
  from_port                    = 22
  to_port                      = 22
  referenced_security_group_id = aws_security_group.app.id
}

# ------------------------------------------------------------------ db: saída (mínima)
resource "aws_vpc_security_group_egress_rule" "db_https" {
  security_group_id = aws_security_group.db.id
  description       = "HTTPS: imagens Docker, S3 (backups), repositorios"
  ip_protocol       = "tcp"
  from_port         = 443
  to_port           = 443
  cidr_ipv4         = "0.0.0.0/0"
}

resource "aws_vpc_security_group_egress_rule" "db_http" {
  security_group_id = aws_security_group.db.id
  description       = "HTTP: repositorios apt do Ubuntu"
  ip_protocol       = "tcp"
  from_port         = 80
  to_port           = 80
  cidr_ipv4         = "0.0.0.0/0"
}

resource "aws_vpc_security_group_egress_rule" "db_dns_udp" {
  security_group_id = aws_security_group.db.id
  description       = "DNS do VPC"
  ip_protocol       = "udp"
  from_port         = 53
  to_port           = 53
  cidr_ipv4         = local.vpc_cidr
}

resource "aws_vpc_security_group_egress_rule" "db_dns_tcp" {
  security_group_id = aws_security_group.db.id
  description       = "DNS do VPC (TCP)"
  ip_protocol       = "tcp"
  from_port         = 53
  to_port           = 53
  cidr_ipv4         = local.vpc_cidr
}
