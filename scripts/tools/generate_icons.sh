#!/bin/bash
# Generate PNG icons from an SVG source file.
#
# Usage: scripts/tools/generate_icons.sh resources/img-src/icon-name.svg
#
# Generates the following PNGs in resources/images/:
#   16x16/icon-name.png      (16x16)
#   16x16/icon-name@2x.png   (64x64)
#   22x22/icon-name.png      (22x22)
#   22x22/icon-name@2x.png   (88x88)
#
# Requires: inkscape

set -euo pipefail

if [ $# -eq 0 ]; then
    echo "Usage: $0 <svg-file> [<svg-file> ...]"
    echo "Example: $0 resources/img-src/isrc-submit.svg"
    exit 1
fi

if ! command -v inkscape &>/dev/null; then
    echo "Error: inkscape is required but not found in PATH"
    exit 1
fi

IMAGES_DIR="resources/images"

# Icon sizes: directory -> (base_size, hidpi_size)
declare -A SIZES=(
    ["16x16"]="16 64"
    ["22x22"]="22 88"
)

for svg in "$@"; do
    if [ ! -f "$svg" ]; then
        echo "Error: $svg not found"
        exit 1
    fi

    name=$(basename "$svg" .svg)
    echo "Generating icons for: $name"

    for dir in "${!SIZES[@]}"; do
        read -r base hidpi <<< "${SIZES[$dir]}"

        echo "  ${dir}/${name}.png (${base}x${base})"
        inkscape --export-type=png \
            --export-filename="${IMAGES_DIR}/${dir}/${name}.png" \
            --export-width="$base" --export-height="$base" \
            "$svg" 2>/dev/null

        echo "  ${dir}/${name}@2x.png (${hidpi}x${hidpi})"
        inkscape --export-type=png \
            --export-filename="${IMAGES_DIR}/${dir}/${name}@2x.png" \
            --export-width="$hidpi" --export-height="$hidpi" \
            "$svg" 2>/dev/null
    done

    echo "Done: $name"
done
