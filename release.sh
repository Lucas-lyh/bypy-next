#!/bin/sh
# Build by default. Publishing requires an explicit repository argument.
set -eu

cd "$(dirname "$0")"
repository=${1:-build}
if [ "$#" -gt 1 ]; then
    echo "Usage: $0 [build|testpypi|pypi]" >&2
    exit 2
fi
case "$repository" in
    build|testpypi|pypi) ;;
    *) echo "Usage: $0 [build|testpypi|pypi]" >&2; exit 2 ;;
esac
command -v uv >/dev/null 2>&1 || { echo "uv is required" >&2; exit 1; }
mkdir -p dist
release_dir=$(mktemp -d dist/release.XXXXXXXX)
uv tool run --python 3.14 --from build pyproject-build --outdir "$release_dir"
uv tool run --python 3.14 twine check "$release_dir"/*
echo "Artifacts: $release_dir"
case "$repository" in
    testpypi) uv tool run --python 3.14 twine upload --repository testpypi "$release_dir"/* ;;
    pypi) uv tool run --python 3.14 twine upload "$release_dir"/* ;;
esac
