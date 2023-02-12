#!/usr/bin/env bash
# Compresses any files within a particular larger than 100 MB into a file with
# the date of compression
if [[ "$#" -ne 1 ]]; then
  echo "Usage: log-compressor.sh directory"
  exit 1
fi
if ! type lrzip &> /dev/null; then
  echo "lrzip not found. Bailing"
  exit 1
fi
LOG_DIR="$1"
if ! [[ -d "$LOG_DIR" ]]; then
  echo "No directory $LOG_DIR found."
fi

DATE=$(date -I)
find "$LOG_DIR" -type f -size +100M -exec lrzip -g -o "$LOG_DIR/$DATE.lrz" {} \;
