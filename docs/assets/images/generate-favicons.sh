#!/usr/bin/env bash
set -euo pipefail

umask 022

INPUT_LOGO="${1:-git-wrench-logo.png}"

if [ ! -f "$INPUT_LOGO" ]; then
  echo "Error: Input file '$INPUT_LOGO' not found."
  echo "Usage: ./generate-favicons.sh <path-to-logo.png>"
  exit 1
fi

echo "Processing $INPUT_LOGO into website icons..."

# Step 1: Trim padding, square-center the icon, and clean up canvas
magick "$INPUT_LOGO" \
  -trim \
  -gravity center \
  -background none \
  -extent "%[fx:max(w,h)]x%[fx:max(w,h)]" \
  square_temp.png

# Step 2: Generate PNG icons
magick square_temp.png -filter Lanczos -resize 16x16 favicon-16x16.png
magick square_temp.png -filter Lanczos -resize 32x32 favicon-32x32.png
magick square_temp.png -filter Lanczos -resize 180x180 apple-touch-icon.png
magick square_temp.png -filter Lanczos -resize 192x192 android-chrome-192x192.png
magick square_temp.png -filter Lanczos -resize 512x512 android-chrome-512x512.png

# Step 3: Combine 16x16 and 32x32 into a multi-resolution ICO file
magick favicon-16x16.png favicon-32x32.png favicon.ico

# Clean up temporary file
rm -f square_temp.png

echo "Done! Successfully generated:"
echo "  - favicon-16x16.png"
echo "  - favicon-32x32.png"
echo "  - apple-touch-icon.png"
echo "  - favicon.ico"
echo "  - android-chrome-192x192.png"
echo "  - android-chrome-512x512.png"
