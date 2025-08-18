#!/usr/bin/env sh
set -e
host="$1"
shift
until nc -z "$host" 6379; do
  echo "Aguardando Redis em $host:6379..."
  sleep 1
done
exec "$@"
