#!/usr/bin/env bash
set -uo pipefail

attempts="${CI_RETRY_ATTEMPTS:-4}"
delay="${CI_RETRY_DELAY_SECONDS:-20}"

if [ "$#" -eq 0 ]; then
	echo "ci-retry: command is required" >&2
	exit 64
fi

attempt=1
status=0
while [ "$attempt" -le "$attempts" ]; do
	echo "ci-retry: attempt $attempt/$attempts: $*"
	"$@"
	status=$?
	if [ "$status" -eq 0 ]; then
		exit 0
	fi
	if [ "$attempt" -eq "$attempts" ]; then
		exit "$status"
	fi
	sleep $((delay * attempt))
	attempt=$((attempt + 1))
done

exit "$status"
