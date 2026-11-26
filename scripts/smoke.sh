#!/usr/bin/env bash
# Teste funcional pela internet (mesmas verificações do scripts/smoke.mjs original).
# Uso: scripts/smoke.sh <url-da-loja> [--write]
#   sem --write : somente leitura (página, saúde, catálogo, histórico)
#   com --write : também cria um pedido fictício e confere que ele aparece no histórico
set -euo pipefail
BASE="${1:?url}"; BASE="${BASE%/}"
WRITE="${2:-}"
pass() { echo "PASS  $*"; }
fail() { echo "FAIL  $*"; exit 1; }
c() { curl -fsS --retry 5 --retry-all-errors --retry-delay 3 --max-time 15 "$@"; }

c "${BASE}/" | grep -q "KubeShop" && pass "GET / -> HTML da loja" || fail "página inicial"
READY="$(c "${BASE}/api/health/ready")"
[[ "$(jq -r .ready <<<"${READY}")" == "true" && "$(jq -r .database <<<"${READY}")" == "true" ]] \
  && pass "GET /api/health/ready -> ${READY}" || fail "saúde: ${READY}"
PRODUCTS="$(c "${BASE}/api/products")"
COUNT="$(jq '.products | length' <<<"${PRODUCTS}")"
[[ "${COUNT}" -ge 1 ]] && pass "GET /api/products -> ${COUNT} produtos" || fail "catálogo"
ORDERS="$(c "${BASE}/api/orders" | jq '.orders | length')"
pass "GET /api/orders -> ${ORDERS} pedidos no histórico"

if [[ "${WRITE}" == "--write" ]]; then
  PID="$(jq -r '.products[0].id' <<<"${PRODUCTS}")"
  CREATED="$(c -X POST -H 'Content-Type: application/json' \
    -d "{\"items\":[{\"productId\":\"${PID}\",\"quantity\":1}]}" "${BASE}/api/orders")"
  OID="$(jq -r .order.id <<<"${CREATED}")"
  [[ -n "${OID}" && "${OID}" != "null" ]] && pass "POST /api/orders -> 201 pedido ${OID}" || fail "criar pedido"
  c "${BASE}/api/orders" | jq -e --arg id "${OID}" '.orders | any(.id == $id)' >/dev/null \
    && pass "Pedido ${OID} consultado no histórico" || fail "pedido não aparece no histórico"
fi
for R in /api/metrics /api/lab/cpu; do
  CODE="$(curl -s -o /dev/null -w '%{http_code}' --max-time 10 "${BASE}${R}")"
  [[ "${CODE}" == "404" ]] && pass "GET ${R} -> 404 (rota inexistente)" || fail "${R} retornou ${CODE}"
done
echo "SMOKE_RESULT=PASS"
