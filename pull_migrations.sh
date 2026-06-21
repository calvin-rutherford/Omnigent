#!/bin/bash

# This script siphons all newly generated migration files from the VPS
# back down to the local Mac so they can be committed to GitHub.

echo "Connecting to VPS to siphon migration files..."

for app in */ ; do
  if [ -d "${app}migrations" ]; then
    echo "Checking for new migrations in ${app}..."
    scp -P 2222 -q "spectre@127.0.0.1:/home/spectre/Django-Dash/${app}migrations/*.py" "/Users/WatchDog/Dev/Django-Dash/${app}migrations/" 2>/dev/null
  fi
done

echo ""
echo "✅ All migrations successfully siphoned from the VPS!"
echo "Run 'git status' to see the newly downloaded files."
