#!/usr/bin/env bash
# Evidência de isolamento do banco (ACE-03), executada de FORA da AWS (runner do GitHub).
# Uso: scripts/isolation-test.sh <tf-outputs.json>
set -euo pipefail
OUT_JSON="${1:?outputs json}"
APP_IP="$(jq -r .app_public_ip.value "${OUT_JSON}")"
DB_PUBLIC="$(jq -r '.db_public_ip.value // ""' "${OUT_JSON}")"
DB_SG="$(jq -r .db_security_group_id.value "${OUT_JSON}")"

echo "1) VM do banco sem IP público:"
[[ -z "${DB_PUBLIC}" ]] && echo "   PASS  db_public_ip vazio" || { echo "   FAIL  banco com IP público ${DB_PUBLIC}"; exit 1; }

echo "2) Porta 27017 não aceita conexões pela internet (IP público da aplicação):"
if timeout 8 bash -c "exec 3<>/dev/tcp/${APP_IP}/27017" 2>/dev/null; then
  echo "   FAIL  27017 aberta em ${APP_IP}"; exit 1
else
  echo "   PASS  conexão recusada/expirada em ${APP_IP}:27017"
fi

echo "3) Regras de entrada do Security Group do banco (origem deve ser o SG da aplicação):"
aws ec2 describe-security-group-rules --filters "Name=group-id,Values=${DB_SG}" \
  --query 'SecurityGroupRules[?IsEgress==`false`].[FromPort,ToPort,CidrIpv4,ReferencedGroupInfo.GroupId,Description]' \
  --output table
OPEN="$(aws ec2 describe-security-group-rules --filters "Name=group-id,Values=${DB_SG}" \
  --query 'length(SecurityGroupRules[?IsEgress==`false` && CidrIpv4!=null])' --output text)"
[[ "${OPEN}" == "0" ]] && echo "   PASS  nenhuma regra de entrada por CIDR no banco" \
  || { echo "   FAIL  há ${OPEN} regra(s) de entrada por CIDR no SG do banco"; exit 1; }
echo "ISOLATION_RESULT=PASS"
