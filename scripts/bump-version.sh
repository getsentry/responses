#!/bin/bash
set -eux

cd "$(dirname "$0")/.."

OLD_VERSION="${1}"
NEW_VERSION="${2}"

echo "Current version: $OLD_VERSION"
echo "Bumping version: $NEW_VERSION"

function replace() {
    ! grep "$2" "$3"
    sed -e "s/$1/$2/g" "$3" > "$3.tmp"  # -i is non-portable
    mv "$3.tmp" "$3"
    grep "$2" "$3"  # verify that replacement was successful
}

replace 'version="[^"]*"' "version=\"$NEW_VERSION\"" ./setup.py
