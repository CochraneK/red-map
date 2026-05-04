#!/usr/bin/env bash
cd "$(dirname "$0")"
PORT=8000
echo "========================================"
echo " Long March Spark Routes - Local Server"
echo "========================================"
echo "Chinese home page: http://localhost:${PORT}/"
echo "English page:      http://localhost:${PORT}/index-en.html"
echo "Admin panel:       http://localhost:${PORT}/admin/index.html"
echo "Keep this terminal open while using the project."
if command -v xdg-open >/dev/null 2>&1; then xdg-open "http://localhost:${PORT}/" >/dev/null 2>&1 & fi
python3 -m http.server ${PORT}
