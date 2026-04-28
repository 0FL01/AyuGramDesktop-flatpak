#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 3 ]; then
	echo "usage: build-flatpak-bundle.sh <manifest> <bundle> <app-id>" >&2
	exit 64
fi

manifest="$1"
bundle="$2"
app_id="$3"
attempts="${CI_RETRY_ATTEMPTS:-3}"
delay="${CI_RETRY_DELAY_SECONDS:-30}"
attempt=1
status=0

while [ "$attempt" -le "$attempts" ]; do
	echo "flatpak-builder: attempt $attempt/$attempts"
	rm -rf repo build-dir
	if flatpak-builder --repo=repo --force-clean --disable-rofiles-fuse build-dir "$manifest"; then
		break
	fi
	status=$?
	if [ "$attempt" -eq "$attempts" ]; then
		exit "$status"
	fi
	sleep $((delay * attempt))
	attempt=$((attempt + 1))
done

flatpak build-bundle repo "$bundle" "$app_id"
