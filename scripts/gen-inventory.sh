#!/usr/bin/env bash
# Gera o inventário do Ansible a partir dos outputs do Terraform (integração TF -> Ansible).
# Uso: scripts/gen-inventory.sh <tf-outputs.json> <saida.yml> <arquivo-chave-ssh>
set -euo pipefail
OUT_JSON="${1:?outputs json}"
DEST="${2:?arquivo de saída}"
KEY="${3:?chave ssh}"

v() { jq -er --arg k "$1" '.[$k].value' "${OUT_JSON}"; }

ENVIRONMENT="$(v environment)"
APP_IP="$(v app_public_ip)"
DB_IP="$(v db_private_ip)"
APP_NAME="$(jq -er '.inventory.value.app_vm.name' "${OUT_JSON}")"
DB_NAME="$(jq -er '.inventory.value.db_vm.name' "${OUT_JSON}")"

cat > "${DEST}" <<EOF
---
# GERADO AUTOMATICAMENTE por scripts/gen-inventory.sh a partir do Terraform. Não editar.
all:
  vars:
    ansible_user: ubuntu
    ansible_ssh_private_key_file: ${KEY}
    env_name: ${ENVIRONMENT}
    aws_region: $(v aws_region)
    app_public_ip: ${APP_IP}
    db_private_ip: ${DB_IP}
    private_subnet_cidr: $(v private_subnet_cidr)
    backup_bucket: $(v backup_bucket)
    db_data_volume_id: $(v db_data_volume_id)
  children:
    app:
      hosts:
        ${APP_NAME}:
          ansible_host: ${APP_IP}
    db:
      hosts:
        ${DB_NAME}:
          ansible_host: ${DB_IP}
          ansible_ssh_common_args: >-
            -o ProxyCommand="ssh -W %h:%p -q -i ${KEY}
            -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null ubuntu@${APP_IP}"
EOF
echo "Inventário gerado: app=${APP_NAME} (${APP_IP}) db=${DB_NAME} (${DB_IP}, privado, via salto)"
