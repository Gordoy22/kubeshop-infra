#!/usr/bin/env bash
# terraform init com backend remoto S3 (um state por stack/ambiente).
# Uso: scripts/tf-init.sh <global|environment> [ambiente]
set -euo pipefail
STACK="${1:?informe global ou environment}"
ENVIRONMENT="${2:-}"
: "${TF_STATE_BUCKET:?rode scripts/ensure-backend.sh antes}"
: "${AWS_REGION:?defina AWS_REGION}"

if [[ "${STACK}" == "global" ]]; then
  KEY="kubeshop/global/terraform.tfstate"
else
  KEY="kubeshop/${ENVIRONMENT:?informe o ambiente}/terraform.tfstate"
fi

terraform -chdir="terraform/${STACK}" init -input=false -reconfigure \
  -backend-config="bucket=${TF_STATE_BUCKET}" \
  -backend-config="key=${KEY}" \
  -backend-config="region=${AWS_REGION}" \
  -backend-config="use_lockfile=true" \
  -backend-config="encrypt=true"
echo "State: s3://${TF_STATE_BUCKET}/${KEY}"
