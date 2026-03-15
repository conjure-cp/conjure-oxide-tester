#!/bin/bash

usage() {
    echo "Usage: $0 <runner> [timeout] [operand]"
    echo ""
    echo "Run all Essence models in the 'models/' directory using the specified runner."
    echo "Runners are defined in 'settings.json'."
    echo ""
    echo "Arguments:"
    echo "  runner:  Name of the runner (e.g., conjure-oxide)"
    echo "  timeout: Optional. Default is 30s (e.g., 1m, 10s)"
    echo "  operand: Optional. Filter models that contain this string (e.g., 'min', 'max')"
    echo ""
    echo "Example:"
    echo "  $0 oxide_main_minion"
    echo "  $0 oxide_main_sat 1m"
    echo "  $0 oxide_main_sat min          # Run models containing 'min' with 30s timeout"
    echo "  $0 oxide_main_sat 1m max       # Run models containing 'max' with 1m timeout"
    exit 1
}

# Check if at least one argument is provided
if [ "$#" -lt 1 ] || [ "$#" -gt 3 ]; then
    usage
fi

RUNNER=$1
TIMEOUT="30s"
OPERAND=""

if [ "$#" -eq 2 ]; then
    # If the second argument starts with a digit, it's a timeout.
    # Otherwise, it's an operand.
    if [[ $2 =~ ^[0-9] ]]; then
        TIMEOUT=$2
    else
        OPERAND=$2
    fi
elif [ "$#" -eq 3 ]; then
    TIMEOUT=$2
    OPERAND=$3
fi

# Ensure we are in the project root
cd "$(dirname "$0")/.." || exit 1

# Check if parallel is installed
if ! command -v parallel &> /dev/null; then
    echo "Error: 'parallel' (GNU Parallel) is not installed."
    echo "Install it with: sudo apt install parallel"
    exit 1
fi

# Function to check if a file contains the given operand
# Usage: has_operand <operand> <filename>
has_operand() {
    local operand=$1
    local filename=$2
    if [ -z "$operand" ]; then
        return 0
    fi
    grep -q "$operand" "$filename"
}

if [ -n "$OPERAND" ]; then
    echo "Starting tests for runner: $RUNNER (Timeout: $TIMEOUT, Filtering by: $OPERAND)"
else
    echo "Starting tests for runner: $RUNNER (Timeout: $TIMEOUT)"
fi

# Find all .essence files in the models directory
# and run them through the timer utility in parallel.
# If an operand is provided, filter the files.
# TODO(Shikhar): Support multiple runners
find models -type f -name "*.essence" | while read -r f; do
    if has_operand "$OPERAND" "$f"; then
        echo "$f"
    fi
done | \
    parallel --jobs 100% --progress --timeout "$TIMEOUT" \
    "uv run python3 utils/timer.py $RUNNER {}"
