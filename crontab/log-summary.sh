#!/usr/bin/env bash
# Sends a summary of the connectivity monitor in an email to the given email
PARSER_BIN=$HOME/code/DowntimeMonitor/parseConnectivityLog.py
if ! [[ -f "$PARSER_BIN" ]]; then
  echo "$PARSER_BIN not found."
  exit 1
fi

if [[ "$#" -ne 3 ]]; then
  echo "Usage: log-summary.sh logfile from to"
  exit 1
fi

LOG_FILE="$1"
FROM="$2"
TO="$3"
if ! [[ -f "$LOG_FILE" ]]; then
  echo "$LOG_FILE does not exist."
  exit 1
fi

python3 "$PARSER_BIN" "$LOG_FILE" | mail -r "$FROM" -s "Downtime Monitor Summary" "$TO"
