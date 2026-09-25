#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
_PKG=pipeline
_CACHE=.bundle
_PKGFILE=engine.pkg

if [ -f "$_CACHE/python.exe" ]; then
    # A cached runtime is trusted only if it actually starts — an
    # interrupted extraction leaves a corrupt tree behind (mirrors run.bat).
    if ! "$_CACHE/python.exe" -c "pass" >/dev/null 2>&1; then
        rm -rf "$_CACHE"
    fi
fi

if [ ! -f "$_CACHE/python.exe" ]; then
    if [ -f "$_PKG/data/$_PKGFILE" ]; then
        rm -rf "$_CACHE.tmp"
        mkdir -p "$_CACHE.tmp"
        unzip -q "$_PKG/data/$_PKGFILE" -d "$_CACHE.tmp" 2>/dev/null \
        || "/c/Windows/System32/tar.exe" -xf "$_PKG/data/$_PKGFILE" -C "$_CACHE.tmp" 2>/dev/null \
        || tar -xf "$_PKG/data/$_PKGFILE" -C "$_CACHE.tmp" 2>/dev/null \
        || python -c "import zipfile;zipfile.ZipFile(r'$_PKG/data/$_PKGFILE').extractall(r'$_CACHE.tmp')" 2>/dev/null \
        || python3 -c "import zipfile;zipfile.ZipFile(r'$_PKG/data/$_PKGFILE').extractall(r'$_CACHE.tmp')" 2>/dev/null \
        || true
        if [ -f "$_CACHE.tmp/python.exe" ]; then
            rm -rf "$_CACHE"
            mv "$_CACHE.tmp" "$_CACHE"
        else
            rm -rf "$_CACHE.tmp"
        fi
    fi
fi

if [ -f "$_CACHE/python.exe" ]; then
    exec "$_CACHE/python.exe" main.py "$@"
fi
if command -v python3 >/dev/null 2>&1; then
    exec python3 main.py "$@"
fi
if command -v python >/dev/null 2>&1; then
    exec python main.py "$@"
fi
if command -v py >/dev/null 2>&1; then
    exec py -3 main.py "$@"
fi
echo "No Python interpreter found (tried bundled runtime, python3, python, py)." >&2
exit 1
