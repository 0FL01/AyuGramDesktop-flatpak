#!/usr/bin/env bash
set -euo pipefail

jobs="${JOBS:-2}"
parallelism="${BUILDKIT_MAX_PARALLELISM:-2}"
builder_name="${BUILDKIT_BUILDER_NAME:-tdesktop-ci-${GITHUB_RUN_ID:-local}-${GITHUB_RUN_ATTEMPT:-1}-$$}"
config_path="$(mktemp)"

cleanup() {
	docker buildx rm "$builder_name" >/dev/null 2>&1 || true
	rm -f "$config_path"
}

trap cleanup EXIT

cat > "$config_path" <<EOF
[worker.oci]
  max-parallelism = $parallelism
EOF

cd Telegram/build/docker/centos_env
poetry install
docker buildx rm "$builder_name" >/dev/null 2>&1 || true
docker buildx create \
	--name "$builder_name" \
	--driver docker-container \
	--driver-opt network=host \
	--config "$config_path" \
	--use
docker buildx inspect --bootstrap
DEBUG="${DEBUG-}" LTO="${LTO-}" JOBS="$jobs" poetry run gen_dockerfile \
	| docker buildx build \
		--builder "$builder_name" \
		--load \
		--progress=plain \
		-t tdesktop:centos_env -
