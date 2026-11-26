# -----------------------------------------------------------------------------
# Rede: VPC com sub-rede pública (aplicação) e privada (banco, sem rota de entrada).
# -----------------------------------------------------------------------------

resource "aws_vpc" "main" {
  cidr_block           = local.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = { Name = "${local.name_prefix}-vpc" }
}

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id
  tags   = { Name = "${local.name_prefix}-igw" }
}

resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = local.public_cidr
  availability_zone       = local.az
  map_public_ip_on_launch = false # o IP público da aplicação é um Elastic IP explícito

  tags = { Name = "${local.name_prefix}-public", Tier = "public" }
}

resource "aws_subnet" "private" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = local.private_cidr
  availability_zone       = local.az
  map_public_ip_on_launch = false

  tags = { Name = "${local.name_prefix}-private", Tier = "private" }
}

# ---- Tabela pública: saída direta pela internet.
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id
  tags   = { Name = "${local.name_prefix}-rt-public" }
}

resource "aws_route" "public_internet" {
  route_table_id         = aws_route_table.public.id
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = aws_internet_gateway.main.id
}

resource "aws_route_table_association" "public" {
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.public.id
}

# ---- Tabela privada: só SAÍDA (atualizações/imagens) via NAT; nada entra da internet.
resource "aws_route_table" "private" {
  vpc_id = aws_vpc.main.id
  tags   = { Name = "${local.name_prefix}-rt-private" }
}

resource "aws_route_table_association" "private" {
  subnet_id      = aws_subnet.private.id
  route_table_id = aws_route_table.private.id
}

# Opção econômica (padrão): a VM da aplicação atua como NAT (configurada pelo Ansible).
resource "aws_route" "private_via_app_nat" {
  count                  = var.use_nat_gateway ? 0 : 1
  route_table_id         = aws_route_table.private.id
  destination_cidr_block = "0.0.0.0/0"
  network_interface_id   = aws_instance.app.primary_network_interface_id
}

# Opção gerenciada (produção com orçamento): NAT Gateway.
resource "aws_eip" "nat" {
  count  = var.use_nat_gateway ? 1 : 0
  domain = "vpc"
  tags   = { Name = "${local.name_prefix}-nat-eip" }
}

resource "aws_nat_gateway" "main" {
  count         = var.use_nat_gateway ? 1 : 0
  allocation_id = aws_eip.nat[0].id
  subnet_id     = aws_subnet.public.id
  tags          = { Name = "${local.name_prefix}-nat" }
  depends_on    = [aws_internet_gateway.main]
}

resource "aws_route" "private_via_nat_gateway" {
  count                  = var.use_nat_gateway ? 1 : 0
  route_table_id         = aws_route_table.private.id
  destination_cidr_block = "0.0.0.0/0"
  nat_gateway_id         = aws_nat_gateway.main[0].id
}

# Endpoint Gateway do S3 (gratuito): o backup do banco vai ao S3 pela rede da AWS,
# sem passar pelo NAT nem pela internet.
resource "aws_vpc_endpoint" "s3" {
  vpc_id            = aws_vpc.main.id
  service_name      = "com.amazonaws.${var.aws_region}.s3"
  vpc_endpoint_type = "Gateway"
  route_table_ids   = [aws_route_table.private.id, aws_route_table.public.id]
  tags              = { Name = "${local.name_prefix}-s3-endpoint" }
}
