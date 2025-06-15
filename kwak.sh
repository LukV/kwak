#!/usr/bin/env bash
# ./kwak - host-facing CLI shim

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

docker build -q -t kwak-cli "$DIR" > /dev/null

docker run --rm -it \
  --volume "$DIR:/app" \
  --workdir /app \
  kwak-cli "$@"

# to run make kwak executable:
# chmod +x kwak.sh