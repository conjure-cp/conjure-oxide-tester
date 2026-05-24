#!/bin/bash

usage() {
    echo "Usage: $0 [--no-closures] <runner1> [runner2 ...] [operand]"
    echo ""
    echo "Run all Essence models in the 'models/' directory using the specified runners."
    echo "Runners are defined in 'settings.json'."
    echo ""
    echo "Arguments:"
    echo "  --no-closures: Optional. Disable SAT closure and var number collection."
    echo "  runner(s):     One or more runners (e.g., oxide_main_sat oxide_main_minion)"
    echo "  operand:       Optional. Filter models that contain this string (e.g., 'min', 'max')"
    echo ""
    echo "Examples:"
    echo "  $0 oxide_main_minion"
    echo "  $0 --no-closures oxide_main_sat"
    echo "  $0 oxide_main_sat max"
    echo "  $0 oxide_main_sat oxide_main_minion max"
    exit 1
}

if [ "$#" -lt 1 ]; then
    usage
fi

OPERAND=""
COLLECT_CLOSURES_FLAG=""

# Detect --no-closures anywhere in arguments
NEW_ARGS=()
for arg in "$@"; do
    if [ "$arg" == "--no-closures" ]; then
        COLLECT_CLOSURES_FLAG="--no-closures"
    else
        NEW_ARGS+=("$arg")
    fi
done

# Detect runners and operand
RUNNER_LIST=$(python3 -c "import json; print(' '.join(json.load(open('settings.json'))['runner_commands'].keys()))")
RUNNERS=()
OPERAND=""

for arg in "${NEW_ARGS[@]}"; do
    if [[ " $RUNNER_LIST " =~ " $arg " ]]; then
        RUNNERS+=("$arg")
    else
        OPERAND="$arg"
    fi
done

if [ ${#RUNNERS[@]} -eq 0 ]; then
    echo "Error: No valid runners specified."
    usage
fi

cd "$(dirname "$0")/.." || exit 1

cleanup() {
    rm -f **.db-shm **.db-wal
    find -name "**.solution" -delete
    find -name "**.MINION*" -delete
    rm -rf conjure-output
    rm -rf temp-models
    rm -f .temp_files
}

trap cleanup EXIT INT TERM


if ! command -v parallel &> /dev/null; then
    echo "Error: 'parallel' (GNU Parallel) is not installed."
    echo "Install it with: sudo apt install parallel"
    exit 1
fi

has_operand() {
    local operand=$1
    local filename=$2
    if [ -z "$operand" ]; then
        return 0
    fi
    # Check if filename contains operand OR file content contains operand
    [[ "$filename" == *"$operand"* ]] || grep -q "$operand" "$filename"
}

DB_PATH=$(python3 -c "import json; print(json.load(open('settings.json'))['outfile'])")

CURRENT_RUN=$(sqlite3 "$DB_PATH" "SELECT IFNULL(MAX(run_number), 0) FROM results;" 2>/dev/null || echo 0)
NEXT_RUN=$((CURRENT_RUN + 1))

echo "Starting tests"
echo "Runners: ${RUNNERS[*]}"
[ -n "$OPERAND" ] && echo "Filter: $OPERAND"
[ -n "$COLLECT_CLOSURES_FLAG" ] && echo "Closures: Disabled"
echo "Run: $NEXT_RUN"

find models -type f -name "*.essence" -o -name "*.eprime" | while read -r f; do
    if has_operand "$OPERAND" "$f"; then
        echo "$f"
    fi
done > .temp_files

if [ ! -s .temp_files ]; then
    echo "No files found matching filter: $OPERAND"
    exit 0
fi

parallel --jobs 90% --progress \
    python3 src/runner_settings/benchmark_runner.py {1} {2} $NEXT_RUN $COLLECT_CLOSURES_FLAG \
    ::: "${RUNNERS[@]}" \
    :::: .temp_files