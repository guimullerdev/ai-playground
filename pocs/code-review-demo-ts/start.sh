#!/bin/bash
set -e

if [ ! -f .env ]; then
  echo "Error: .env file not found. Copy .env.example and fill in your values."
  exit 1
fi

docker compose up --build "$@"
