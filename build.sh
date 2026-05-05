#!/usr/bin/env bash
# Build the Solidean Blender addon zip, verifying that all required files
# (including a platform-appropriate native library) are present.

set -euo pipefail
cd "$(dirname "$0")"

pkg='solidean'
out='solidean.zip'

if [ ! -d "$pkg" ]; then
    echo "Package folder '$pkg' not found." >&2
    exit 1
fi

required=(__init__.py blender_manifest.toml live.py utils.py solidean.py)
missing=()
for f in "${required[@]}"; do
    [ -f "$pkg/$f" ] || missing+=("$f")
done
if [ ${#missing[@]} -gt 0 ]; then
    echo "Missing required file(s) in $pkg/: ${missing[*]}" >&2
    exit 1
fi

libs=(solidean.dll libsolidean.so libsolidean.dylib)
found=()
for l in "${libs[@]}"; do
    [ -f "$pkg/$l" ] && found+=("$l")
done
if [ ${#found[@]} -eq 0 ]; then
    echo "No Solidean native library found in $pkg/. Expected one of: ${libs[*]}." >&2
    echo "See https://solidean.com/download/solidean/." >&2
    exit 1
fi
echo "Native library: ${found[*]}"

find "$pkg" -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

rm -f "$out"
zip -r "$out" "$pkg" >/dev/null
echo "Created $out"
