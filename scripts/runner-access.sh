#!/usr/bin/env bash
# Abre/fecha SSH (22/tcp) na VM da aplicação SOMENTE para o IP público deste runner,
# apenas durante a execução da pipeline. Fora disso o SSH fica fechado (REQ-04).
# Uso: scripts/runner-access.sh open|close <security-group-id>
set -euo pipefail
ACTION="${1:?open|close}"
SG_ID="${2:?security group id}"
STATE_FILE="${RUNNER_TEMP:-/tmp}/kubeshop-runner-access"

case "${ACTION}" in
  open)
    IP="$(curl -fsS --retry 3 https://checkip.amazonaws.com | tr -d '[:space:]')"
    [[ "${IP}" =~ ^[0-9]{1,3}(\.[0-9]{1,3}){3}$ ]] || { echo "IP do runner inválido"; exit 1; }
    RULE_ID="$(aws ec2 authorize-security-group-ingress --group-id "${SG_ID}" \
      --ip-permissions "IpProtocol=tcp,FromPort=22,ToPort=22,IpRanges=[{CidrIp=${IP}/32,Description=pipeline-runner-temporario-${GITHUB_RUN_ID:-local}}]" \
      --query 'SecurityGroupRules[0].SecurityGroupRuleId' --output text 2>/dev/null || true)"
    if [[ -z "${RULE_ID}" || "${RULE_ID}" == "None" ]]; then
      echo "Regra já existia para ${IP}/32 (mantida)."
      RULE_ID=""
    fi
    printf '%s %s\n' "${SG_ID}" "${RULE_ID}" > "${STATE_FILE}"
    echo "SSH temporário liberado para o runner (${IP}/32) no ${SG_ID}."
    ;;
  close)
    if [[ -f "${STATE_FILE}" ]]; then
      read -r SAVED_SG RULE_ID < "${STATE_FILE}" || true
      if [[ -n "${RULE_ID:-}" ]]; then
        aws ec2 revoke-security-group-ingress --group-id "${SAVED_SG}" \
          --security-group-rule-ids "${RULE_ID}" >/dev/null
        echo "Regra temporária ${RULE_ID} removida."
      fi
      rm -f "${STATE_FILE}"
    fi
    # Limpeza defensiva: remove qualquer regra temporária esquecida por execuções anteriores.
    for STALE in $(aws ec2 describe-security-group-rules --filters "Name=group-id,Values=${SG_ID}" \
        --query "SecurityGroupRules[?starts_with(Description||'', 'pipeline-runner-temporario')].SecurityGroupRuleId" \
        --output text); do
      aws ec2 revoke-security-group-ingress --group-id "${SG_ID}" --security-group-rule-ids "${STALE}" >/dev/null
      echo "Regra temporária antiga ${STALE} removida."
    done
    echo "SSH do runner fechado."
    ;;
  *) echo "Ação inválida: ${ACTION}"; exit 2 ;;
esac
