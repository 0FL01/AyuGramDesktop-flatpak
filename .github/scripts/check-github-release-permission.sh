#!/usr/bin/env bash
set -euo pipefail

token="${GH_RELEASE_TOKEN:-}"
repo="${GITHUB_REPOSITORY:-}"
api_url="${GITHUB_API_URL:-https://api.github.com}"

if [ -z "$token" ]; then
	echo "::error title=GitHub release token is missing::GH_RELEASE_TOKEN is empty. Provide secrets.RELEASE_TOKEN or secrets.GITHUB_TOKEN."
	exit 1
fi

if [ -z "$repo" ]; then
	echo "::error::GITHUB_REPOSITORY is not set."
	exit 1
fi

response_file="$(mktemp)"
trap 'rm -f "$response_file"' EXIT

http_code="$(
	curl --silent --show-error \
		--output "$response_file" \
		--write-out '%{http_code}' \
		--request POST \
		--header 'Accept: application/vnd.github+json' \
		--header "Authorization: Bearer ${token}" \
		--header 'X-GitHub-Api-Version: 2022-11-28' \
		--data '{}' \
		"${api_url}/repos/${repo}/releases"
)"

case "$http_code" in
	400|422)
		echo "Release permission preflight passed. The create-release endpoint is reachable; validation failed as expected for the empty dry-run payload."
		;;
	401|403|404)
		message="$(tr '\n' ' ' < "$response_file" | sed 's/[[:space:]][[:space:]]*/ /g')"
		echo "::error title=GitHub release token cannot create releases::The token cannot create releases for ${repo} (HTTP ${http_code}). Enable Settings > Actions > General > Workflow permissions > Read and write permissions, or add a fine-grained PAT secret named RELEASE_TOKEN with repository Contents: Read and write. GitHub response: ${message}"
		exit 1
		;;
	*)
		message="$(tr '\n' ' ' < "$response_file" | sed 's/[[:space:]][[:space:]]*/ /g')"
		echo "::error title=GitHub release permission preflight failed::Unexpected GitHub API response HTTP ${http_code}. Response: ${message}"
		exit 1
		;;
esac
