#!/bin/bash

usage() {
    echo "Usage: $0 <runner> [timeout]"
    echo ""
    echo "Run all Essence models in the 'models/' directory using the specified runner."
    echo "Runners are defined in 'settings.json'."
    echo ""
    echo "Arguments:"
    echo "  runner:  Name of the runner (e.g., conjure-oxide)"
    echo "  timeout: Optional. Default is 30s (e.g., 1m, 10s)"
    echo ""
    echo "Example:"
    echo "  $0 oxide_main_minion"
    echo "  $0 oxide_main_sat 1m"
    exit 1
}

# Check if at least one argument is provided
if [ "$#" -lt 1 ] || [ "$#" -gt 2 ]; then
    usage
fi

RUNNER=$1
TIMEOUT=${2:-30s}

# Ensure we are in the project root
cd "$(dirname "$0")/.." || exit 1

# Check if parallel is installed
if ! command -v parallel &> /dev/null; then
    echo "Error: 'parallel' (GNU Parallel) is not installed."
    echo "Install it with: sudo apt install parallel"
    exit 1
fi

echo "Starting tests for runner: $RUNNER (Timeout: $TIMEOUT)"

# Find all .essence files in the models directory
# and run them through the timer utility in parallel.
# TODO(Shikhar): Support multiple runners
find models -name "*.essence" | \
    parallel --jobs 100% --progress --timeout "$TIMEOUT" \
    "uv run python3 utils/timer.py $RUNNER {}"
