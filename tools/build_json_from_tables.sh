#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/.."
python3 tools/build_json_from_tables.py
