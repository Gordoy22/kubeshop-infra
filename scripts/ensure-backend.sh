#!/usr/bin/env bash
# Garante (de forma idempotente) o bucket S3 do Terraform State:
#   versionamento (recuperar versões anteriores do state), criptografia SSE,
#   bloqueio de acesso público e política que exige TLS.
# Saída: exporta TF_STATE_BUCKET e AWS_ACCOUNT_ID em $GITHUB_ENV (quando existir).
set -euo pipefail

REGION="${AWS_REGION:?defina AWS_REGION}"
ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text)"
BUCKET="${TF_STATE_BUCKET:-}"
if [[ -z "${BUCKET}" ]]; then
  BUCKET="kubeshop-tfstate-${ACCOUNT_ID}-${REGION}"
fi

if aws s3api head-bucket --bucket "${BUCKET}" 2>/dev/null; then
  echo "Bucket de state já existe: ${BUCKET}"
else
  echo "Criando bucket de state: ${BUCKET}"
  if [[ "${REGION}" == "us-east-1" ]]; then
    aws s3api create-bucket --bucket "${BUCKET}" --region "${REGION}" >/dev/null
  else
    aws s3api create-bucket --bucket "${BUCKET}" --region "${REGION}" \
      --create-bucket-configuration "LocationConstraint=${REGION}" >/dev/null
  fi
  aws s3api wait bucket-exists --bucket "${BUCKET}"
fi

aws s3api put-public-access-block --bucket "${BUCKET}" --public-access-block-configuration \
  BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
aws s3api put-bucket-versioning --bucket "${BUCKET}" --versioning-configuration Status=Enabled
aws s3api put-bucket-encryption --bucket "${BUCKET}" --server-side-encryption-configuration \
  '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"},"BucketKeyEnabled":true}]}'
aws s3api put-bucket-policy --bucket "${BUCKET}" --policy "$(cat <<EOF
{"Version":"2012-10-17","Statement":[{"Sid":"DenyInsecureTransport","Effect":"Deny","Principal":"*","Action":"s3:*",
"Resource":["arn:aws:s3:::${BUCKET}","arn:aws:s3:::${BUCKET}/*"],"Condition":{"Bool":{"aws:SecureTransport":"false"}}}]}
EOF
)"
aws s3api put-bucket-lifecycle-configuration --bucket "${BUCKET}" --lifecycle-configuration \
  '{"Rules":[{"ID":"versoes-antigas-do-state","Status":"Enabled","Filter":{},"NoncurrentVersionExpiration":{"NoncurrentDays":90}}]}'
aws s3api put-bucket-tagging --bucket "${BUCKET}" --tagging \
  'TagSet=[{Key=Project,Value=KubeShop},{Key=Purpose,Value=terraform-state},{Key=ManagedBy,Value=pipeline}]'

echo "Bucket de state protegido: versionamento, SSE-S3, acesso público bloqueado, TLS obrigatório."
if [[ -n "${GITHUB_ENV:-}" ]]; then
  {
    echo "TF_STATE_BUCKET=${BUCKET}"
    echo "AWS_ACCOUNT_ID=${ACCOUNT_ID}"
  } >> "${GITHUB_ENV}"
fi
