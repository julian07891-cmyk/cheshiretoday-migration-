#!/bin/bash

URL="https://cheshiretoday-migration.onrender.com/api/articles"

echo "Warming API at $(date)"
curl -s "$URL" > /dev/null
