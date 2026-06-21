#!/bin/bash

# This script automatically finds any modified files on your Mac
# and SCPs them directly to the exact same location on the VPS.

echo "Scanning for modified files..."

# git status --porcelain is a special flag that outputs a clean list designed for scripts!
# awk '{print $2}' strips out the "M" or "??" status codes and just grabs the file path.
modified_files=$(git status --porcelain | awk '{print $2}')

# Check if the list is empty
if [ -z "$modified_files" ]; then
  echo "You have no modified files to push!"
  exit 0
fi

# Loop through the clean list of files and SCP them
for file in $modified_files; do
  echo "Pushing: $file"
  scp -P 2222 -q "$file" "spectre@127.0.0.1:/home/spectre/Omnigent/$file"
done

echo ""
echo "✅ All modified files successfully pushed to the VPS!"
