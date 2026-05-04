#!/bin/bash

# Check if today is Saturday or Sunday
day_of_week=$(date +%A)

if [ "$day_of_week" = "Saturday" ] || [ "$day_of_week" = "Sunday" ]; then
    # Do nothing and send nothing
    echo "Weekend detected. Doing nothing." > /dev/null
else
    # Monday - Friday: Execute the README prompt logic
    python audit_fetch.py > trades_data.json
    python screener.py
    python generate_report.py
fi
