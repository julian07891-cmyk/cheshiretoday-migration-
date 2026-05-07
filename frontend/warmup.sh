#!/bin/bash

URL="https://cheshiretoday.co.uk/api/articles?limit=1"

echo "Warming API at $(date)"
curl -s "$URL" > /dev/null
