# 06 · Matriz de requisitos → solução

## Escopo KubeShop (v1.2)

| Requisito | Como é atendido | Onde | Evidência |
|---|---|---|---|
| **REQ-01** Duas VMs, uma exclusiva do MongoDB | `aws_instance.app` e `aws_instance.db`. Recursos extras justificados (EIP, EBS, S3, IAM, endpoint). | `terraform/environment/compute.tf` · doc 01 §3 | output `inventory`, resumo do pipeline 2 |
| **REQ-02** Banco isolado, sem porta pública | VM do banco em sub-rede privada **sem IP público**, porta 27017 publicada só no IP privado | `compute.tf` (`associate_public_ip_address=false`), `roles/mongodb` | `isolation-test.sh` (passos 1 e 2), `verify/db.yml` (ss -ltn) |
| **REQ-03** Conexão ao banco só a partir da VM app, pela rede privada; procedimento administrativo separado | SG do banco aceita 27017/22 **só do SG da aplicação**. A API usa `MONGO_HOST=10.20.2.10`. Acesso administrativo por ProxyJump. | `security.tf`, `roles/containers` · **doc 05** | `isolation-test.sh` (passo 3), `verify/app.yml` (conexão privada + recusa sem senha) |
| **REQ-04** Acesso administrativo restrito; credenciais fora do repo e dos logs | SSH só por chave, sem root e sem senha; porta 22 fechada (aberta só para o runner, temporariamente); GitHub Secrets; `no_log`; arquivos `*_FILE`; gitleaks no CI | `roles/hardening`, `scripts/runner-access.sh`, workflows, `ci.yml` | logs dos pipelines sem valores; job `secrets` do CI |
| **REQ-05** Pedidos mantidos após reinício e após alteração de infraestrutura | Volume **EBS dedicado** (`/data/mongo`). O Docker só inicia depois do volume montado. Alteração de tipo de VM é in-place. | `storage.tf`, `roles/data_volume` | Cenário 2 + `restart` (doc 07) |
| §5 Adaptação para hosts separados | endereço privado do banco, credenciais por arquivo, ordem de inicialização por healthcheck | doc 01 §1 | — |
| §5 Endereço da loja, DNS e TLS | `http://<Elastic IP>`; DNS/TLS não usados, com justificativa e caminho para produção | doc 01 §5 | output `store_url` |
| §8 IaC versionada + state documentado | Terraform no Git; state S3 versionado, criptografado, com lock | `terraform/`, `scripts/ensure-backend.sh` · doc 01 §6 | — |
| §9 Validar e planejar | `fmt`, `validate`, `plan` (e `run_mode=plan`); CI a cada push | `infra-deploy.yml`, `ci.yml` | resumo "Terraform plan" |
| §9 Provisionar e configurar | Terraform → inventário gerado → Ansible | `infra-deploy.yml` | Cenário 1 |
| §9 Atualizar com registro e recuperação | plan/apply registrados em artefatos; reversão por tag; manual de falhas | doc 03 §Recuperação | Cenário 2 |
| §9 Manter e diagnosticar | `health`, `logs`, `restart`, `smoke-test` | `ops.yml`, `ansible/playbooks/` | execuções do pipeline 3 |
| §9 Proteger e recuperar dados | backup diário (systemd timer) → S3; restore com SHA-256 e contagem de pedidos | `roles/backup` | `BACKUP_OK` / `RESTORE_OK` |
| §9 Desativar | `destroy.yml` com confirmação e backup final; relatório do que fica e do que custa | doc 03 §Desativar | resumo do pipeline 9 |
| §10 Operação pelo cliente | parâmetros, resultado esperado e ação em falha para cada rotina; rotinas diárias separadas das destrutivas | **doc 03** | — |
| §12 Estimativa de custos | premissas, composição, fontes, créditos separados, limitações | **doc 02** | — |

## Critérios de aceite

| Critério | Evidência no projeto |
|---|---|
| ACE-01 Reprodução | pipeline 2 a partir do zero; pré-requisitos e parâmetros no doc 00 |
| ACE-02 Duas VMs | output `inventory` (resumo do pipeline 2) + console EC2 |
| ACE-03 Isolamento | `ISOLATION_RESULT=PASS` + "Mongo sem senha: RECUSADO" + escuta só em 10.20.2.10 |
| ACE-04 Aplicação | navegador: catálogo → pedido → F5 → *Meus pedidos*; `smoke-test` |
| ACE-05 Persistência | contagem de pedidos antes/depois de `restart` e do Cenário 2 (mudança de `instance_type`/`db_instance_type`) |
| ACE-06 CI/CD | pipeline 1 (build/publicação) + `deploy_environment` → `deploy-app`; doc 04 |
| ACE-07 Recuperação | timer diário + `backup` → `restore` com `pedidos_backup = pedidos_depois` |
| ACE-08 Administração | histórico de execuções no Actions, artefatos de 90 dias, doc 03, credenciais só em Secrets |
| ACE-09 Custos | doc 02 |
| ACE-10 Transferência | README, docs 00–07, tags `Project=KubeShop` nos recursos |

## PM-04 · Critérios de avaliação

| Critério (pontos) | Atendimento |
|---|---|
| Pipeline funcional com parâmetros dinâmicos (2,0) | `workflow_dispatch` com 10 parâmetros. Cada um altera infra ou configuração (tabela no README). Logs claros (summary + artefatos), parada no primeiro erro (`set -euo pipefail`, `needs`). |
| Provisionamento e atualização com Terraform (2,0) | variáveis, `init/validate/plan/apply` na pipeline, state remoto preservado, atualização in-place (`instance_type`, `db_volume_gb`), `ignore_changes` evita recriações |
| Configuração e manutenção com Ansible (2,0) | roles `os_updates` (`update_os`), `packages` (`extra_packages`), `docker` (instala só se faltar), `containers` (tag, pull controlado, recriação), `verify` (serviços e contêineres em execução), idempotência |
| Adequação ao documento de demanda (1,5) | matriz acima; duas VMs, banco isolado, persistência, backups, operação documentada |
| Integração Terraform + Ansible e testes dos cenários (1,5) | outputs → `gen-inventory.sh` → Ansible no mesmo pipeline; cenários 1, 2 e 3 no doc 07 |
| Documentação e explicação técnica (1,0) | README + docs 00–07 |

| Parâmetro recomendado (PM-04 §4) | Input | Efeito |
|---|---|---|
| environment | `environment` | state, VPC, nomes e tags por ambiente |
| instance_name | `instance_name` | nome das VMs |
| instance_type | `instance_type` (+ `db_instance_type`) | tipo das VMs |
| docker_image | `docker_image` | prefixo das imagens |
| docker_tag | `docker_tag` | versão dos contêineres |
| update_os | `update_os` | `apt dist-upgrade` + reinício condicional |
| extra_packages | `extra_packages` | pacotes apt adicionais |
| *(extra da demanda)* | `run_mode`, `db_volume_gb` | só planejar; capacidade do disco do banco |
