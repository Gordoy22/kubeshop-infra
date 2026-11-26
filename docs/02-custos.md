# 02 · Estimativa mensal de custos (ACE-09)

## Premissas

| Item | Valor |
|---|---|
| Provedor / região | AWS · us-east-1 (N. Virginia) |
| Moeda | dólar americano (USD). Conversão ilustrativa em BRL no final. |
| Data de referência | 25/11/2026 |
| Período | 1 mês = **730 horas**, ambiente ligado 24×7 |
| Ambientes | **1** (dev). Cada ambiente adicional (homolog, prod) soma o mesmo valor. |
| Modelo de compra | On-Demand, Linux, sem Reserved Instances ou Savings Plans |
| Tráfego | até 100 GB/mês de saída para a internet (loja de demonstração) |
| Fontes | tabelas públicas de preço da AWS: [EC2 On-Demand](https://aws.amazon.com/ec2/pricing/on-demand/), [EBS](https://aws.amazon.com/ebs/pricing/), [VPC/IPv4 público](https://aws.amazon.com/vpc/pricing/), [S3](https://aws.amazon.com/s3/pricing/). Os preços unitários usados são os de tabela para us-east-1. **Antes de apresentar, confira na [AWS Pricing Calculator](https://calculator.aws/)**, porque a AWS pode ter reajustado algum valor. |

## Composição (configuração padrão)

| Recurso | Quantidade / dimensionamento | Preço unitário | Mensal (USD) |
|---|---|---|---|
| **VM 1 · aplicação** | 1 × t3.micro (2 vCPU, 1 GiB) | US$ 0,0104/h | **7,59** |
| **VM 2 · MongoDB** | 1 × t3.small (2 vCPU, 2 GiB) | US$ 0,0208/h | **15,18** |
| Disco do SO das VMs | 2 × 20 GiB gp3 | US$ 0,08/GiB-mês | 3,20 |
| Volume de dados do MongoDB | 1 × 10 GiB gp3 (3000 IOPS e 125 MB/s inclusos) | US$ 0,08/GiB-mês | 0,80 |
| IPv4 público (Elastic IP da loja) | 1 endereço em uso | US$ 0,005/h | 3,65 |
| Backups no S3 | ~30 cópias diárias × < 1 MB, versionado, retenção de 30 dias | US$ 0,023/GB-mês | < 0,05 |
| Terraform State no S3 | < 1 MB + versões | US$ 0,023/GB-mês | < 0,01 |
| Requisições S3 | ~3 mil PUT/GET por mês | US$ 0,005 / mil PUT | < 0,05 |
| Tráfego de saída | até 100 GB/mês (faixa gratuita permanente da AWS) | US$ 0,09/GB depois | 0,00 |
| VPC, sub-redes, IGW, Security Groups, endpoint S3 gateway, IAM | — | sem custo | 0,00 |
| NAT | feito pela VM da aplicação (sem NAT Gateway) | — | 0,00 |
| Logs | ficam no Docker (rotação de 3 × 10 MB) e no artefato da pipeline. Sem CloudWatch Logs. | — | 0,00 |
| GitHub Actions | repositório público: minutos ilimitados. Privado: 2.000 min/mês grátis (~15 min por deploy). | — | 0,00 |
| **Total recorrente** | | | **≈ US$ 30,50 / mês** |

Conversão ilustrativa: com câmbio de **R$ 5,40/US$** (premissa, verifique a cotação do dia), dá **≈ R$ 165/mês**, sem IOF/impostos do cartão.

## Por que este valor (coerência arquitetura × custo)

- As **duas VMs são obrigatórias** (REQ-01) e correspondem a 75% do custo. Os tipos escolhidos são os menores que rodam a carga com folga (ver dimensionamento em [01-arquitetura.md](01-arquitetura.md#dimensionamento)).
- **Economias deliberadas:**
  - NAT na VM da aplicação em vez de **NAT Gateway**: economiza **US$ 32,85/mês** mais US$ 0,045/GB processado, o que dobraria o custo.
  - **Endpoint S3 gateway** (grátis): o backup não passa por NAT nem por tráfego pago.
  - **Sem Load Balancer** (cerca de US$ 16/mês): há uma única VM de aplicação.
  - Banco **sem IP público** (cerca de US$ 3,65/mês a menos e mais seguro).
- **O que encareceria:**

| Mudança | Impacto mensal |
|---|---|
| VM app t3.micro → t3.small (Cenário 2) | + US$ 7,59 → ≈ US$ 38 |
| NAT Gateway gerenciado (`use_nat_gateway = true`) | + US$ 32,85 + tráfego |
| Região São Paulo (sa-east-1) | ≈ +55% → ≈ US$ 47 |
| ALB + certificado ACM (TLS gerenciado) | + ≈ US$ 16–18 |
| homolog + prod ligados 24×7 | × 3 → ≈ US$ 92 |
| Tráfego acima de 100 GB/mês | + US$ 0,09/GB |
| Reserved Instance / Savings Plan de 1 ano (VMs) | − ≈ 35% a 40% nas VMs |

## Créditos e faixas gratuitas (separados, para não esconder o custo recorrente)

- Contas AWS criadas a partir de 15/07/2025 recebem **US$ 100 em créditos** no cadastro e **até US$ 100 adicionais** ao concluir atividades, válidos por até **6 meses**.
  Durante esse período, o custo acima é **abatido dos créditos** e a fatura tende a ficar em US$ 0.
- A faixa permanente de **100 GB/mês de saída** já está considerada.
- **Depois dos créditos, o custo recorrente é o da tabela (≈ US$ 30,50/mês por ambiente).**

## Limitações da estimativa

- Não inclui impostos, IOF ou variação cambial.
- Créditos de CPU da família T3 em modo *unlimited* (padrão) podem gerar cobrança extra se a CPU ficar acima da linha de base (10% na t3.micro, 20% na t3.small) por muito tempo. Isso não acontece com a carga de demonstração.
- Snapshots não são usados. Se forem criados manualmente, custam US$ 0,05/GB-mês.
- Recursos que **continuam cobrando depois da desativação**: só os buckets de backup e de state (centavos). Veja [03-manual-operacao.md](03-manual-operacao.md#desativar).

## Recomendação de uso no laboratório

Rodar a pipeline **9 · Desativar** depois da apresentação. Um ambiente que fica ligado só por 3 dias custa **≈ US$ 3**.
