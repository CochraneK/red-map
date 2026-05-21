#!/usr/bin/env bash
cd "$(dirname "$0")/.."
if [ "$#" -eq 0 ]; then
  echo 'Usage: tools/extract_steam_texts.sh "/path/to/SteamLibrary/steamapps/common/Long March 1934-1936"'
  echo 'Optional: python3 tools/extract_steam_texts.py --game-keyword "Long March" --include-binary'
  exit 2
fi
python3 tools/extract_steam_texts.py "$@"
