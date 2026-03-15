#!/bin/bash

usage() {
    echo "Usage: $0 <runner>"
    echo ""
    echo "Run all Essence models in the 'models/' directory using the specified runner."
    echo "Runners are defined in 'settings.json'."
    echo ""
    echo "Example:"
    echo "  $0 conjure-oxide"
    echo "  $0 oxide_main_minion"
    exit 1
}

# Check if runner argument is not provided
if [ "$#" -ne 1 ]; then
    usage
fi

RUNNER=$1

echo "Starting tests for runner: $RUNNER"

find models -name "*.essence" | \
    parallel --jobs 100% --progress \
    "uv run python3 utils/timer.py $RUNNER {}"
