#!/usr/bin/env bash
set -e

if [ ! -f .env ]; then
  echo "ERROR: .env file not found. Copy .env.example and fill in your keys:"
  echo "  cp .env.example .env"
  exit 1
fi

docker compose up --build "$@"
