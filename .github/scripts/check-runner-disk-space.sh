#!/usr/bin/env bash
set -euo pipefail

min_free_gib="${MIN_FREE_GIB:-24}"
run_fstrim="${RUN_FSTRIM:-0}"

if ! [[ "$min_free_gib" =~ ^[0-9]+$ ]] || [ "$min_free_gib" -le 0 ]; then
	echo "::error::MIN_FREE_GIB must be a positive integer, got: $min_free_gib"
	exit 1
fi

gib=$((1024 * 1024 * 1024))
min_free_bytes=$((min_free_gib * gib))

existing_path() {
	local path="$1"
	while [ ! -e "$path" ]; do
		local parent
		parent="$(dirname "$path")"
		if [ "$parent" = "$path" ]; then
			path="/"
			break
		fi
		path="$parent"
	done
	printf '%s\n' "$path"
}

bytes_to_gib() {
	awk -v bytes="$1" 'BEGIN { printf "%.1f", bytes / 1024 / 1024 / 1024 }'
}

findmnt_value() {
	findmnt -T "$1" -no "$2" 2>/dev/null | head -n 1
}

add_path() {
	local path="$1"
	if [ -n "$path" ]; then
		paths+=("$path")
	fi
}

paths=()
add_path "${GITHUB_WORKSPACE:-$PWD}"
add_path "$PWD"
home_dir="${HOME:-}"
add_path "$home_dir"
if [ -n "$home_dir" ]; then
	add_path "$home_dir/.cache"
	add_path "$home_dir/.local/share/flatpak"
fi

if command -v docker >/dev/null 2>&1; then
	docker_root="$(docker info --format '{{.DockerRootDir}}' 2>/dev/null || true)"
	add_path "$docker_root"
fi

for path in "$@"; do
	add_path "$path"
done

if [ "$run_fstrim" = "1" ] && command -v fstrim >/dev/null 2>&1; then
	echo "Running fstrim before disk space check..."
	if command -v sudo >/dev/null 2>&1; then
		sudo -n fstrim -av || true
	else
		fstrim -av || true
	fi
fi

declare -A checked_mounts=()
failed=0

echo "Disk space preflight requires at least ${min_free_gib} GiB free on each relevant filesystem."
echo "This check uses free filesystem blocks, not apparent cache size, so compressed Btrfs caches do not inflate the requirement."

for requested_path in "${paths[@]}"; do
	path="$(existing_path "$requested_path")"
	mount_target="$(findmnt_value "$path" TARGET)"
	if [ -z "$mount_target" ]; then
		mount_target="$(df -P "$path" | awk 'NR==2 { print $6 }')"
	fi
	if [ -n "${checked_mounts[$mount_target]:-}" ]; then
		continue
	fi
	checked_mounts[$mount_target]=1

	read -r available_blocks block_size < <(stat -f -c '%a %S' "$path")
	available_bytes=$((available_blocks * block_size))
	fstype="$(findmnt_value "$path" FSTYPE)"
	if [ -z "$fstype" ]; then
		fstype="$(df -PT "$path" | awk 'NR==2 { print $2 }')"
	fi
	source="$(findmnt_value "$path" SOURCE)"
	if [ -z "$source" ]; then
		source="$(df -P "$path" | awk 'NR==2 { print $1 }')"
	fi
	available_gib="$(bytes_to_gib "$available_bytes")"

	echo "  $mount_target ($source, $fstype): ${available_gib} GiB available"

	if [ "$available_bytes" -lt "$min_free_bytes" ]; then
		echo "::error title=Runner disk space is too low::$mount_target has ${available_gib} GiB free, but this workflow requires at least ${min_free_gib} GiB before starting heavy build steps. Clean Docker/Flatpak caches, run fstrim, or increase runner storage."
		failed=1
	fi
done

if [ "$failed" -ne 0 ]; then
	echo "Filesystem summary:"
	df -hT || true

	if command -v btrfs >/dev/null 2>&1; then
		for mount_target in "${!checked_mounts[@]}"; do
			if [ "$(findmnt_value "$mount_target" FSTYPE || true)" = "btrfs" ]; then
				echo "Btrfs usage for $mount_target:"
				btrfs filesystem usage -T "$mount_target" || true
			fi
		done
	fi

	if command -v docker >/dev/null 2>&1; then
		echo "Docker storage summary:"
		docker system df || true
	fi

	exit 1
fi

echo "Disk space preflight passed."
