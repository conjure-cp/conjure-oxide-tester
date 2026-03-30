#!/bin/bash

usage() {
    echo "Usage: $0 [--no-closures] <runner1> [runner2 ...] [timeout] [operand]"
    echo ""
    echo "Run all Essence models in the 'models/' directory using the specified runners."
    echo "Runners are defined in 'settings.json'."
    echo ""
    echo "Arguments:"
    echo "  --no-closures: Optional. Disable SAT closure collection."
    echo "  runner(s):     One or more runners (e.g., oxide_main_sat oxide_main_minion)"
    echo "  timeout:       Optional. Default is 30s (e.g., 1m, 10s)"
    echo "  operand:       Optional. Filter models that contain this string (e.g., 'min', 'max')"
    echo ""
    echo "Examples:"
    echo "  $0 oxide_main_minion"
    echo "  $0 --no-closures oxide_main_sat"
    echo "  $0 oxide_main_sat 1m"
    echo "  $0 oxide_main_sat oxide_main_minion 1m max"
    exit 1
}

if [ "$#" -lt 1 ]; then
    usage
fi

TIMEOUT="30s"
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

# Detect timeout / operand from the end of remaining args
ARGS=("${NEW_ARGS[@]}")
LAST_ARG=${ARGS[-1]}
SECOND_LAST_ARG=${ARGS[-2]}

if [[ $LAST_ARG =~ ^[0-9] ]]; then
    TIMEOUT=$LAST_ARG
    unset 'ARGS[-1]'
elif [[ $SECOND_LAST_ARG =~ ^[0-9] ]]; then
    TIMEOUT=$SECOND_LAST_ARG
    OPERAND=$LAST_ARG
    unset 'ARGS[-1]'
    unset 'ARGS[-1]'
elif [ "${#ARGS[@]}" -ge 2 ]; then
    OPERAND=$LAST_ARG
    unset 'ARGS[-1]'
fi

RUNNERS=("${ARGS[@]}")

cd "$(dirname "$0")/.." || exit 1

cleanup() {
    rm -f **.db-shm **.db-wal
    find -name "**.solution" -delete
    find -name "**.MINION*" -delete
    rm -rf conjure-output
    rm -rf temp-models
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
    grep -q "$operand" "$filename"
}

DB_PATH=$(python3 -c "import json; print(json.load(open('settings.json'))['outfile'])")

CURRENT_RUN=$(sqlite3 "$DB_PATH" "SELECT IFNULL(MAX(run_number), 0) FROM results;" 2>/dev/null || echo 0)
NEXT_RUN=$((CURRENT_RUN + 1))

echo "Starting tests"
echo "Runners: ${RUNNERS[*]}"
echo "Timeout: $TIMEOUT"
[ -n "$OPERAND" ] && echo "Filter: $OPERAND"
[ -n "$COLLECT_CLOSURES_FLAG" ] && echo "Closures: Disabled"
echo "Run: $NEXT_RUN"

FILES=$(find models -type f -name "*.essence" | while read -r f; do
    if has_operand "$OPERAND" "$f"; then
        echo "$f"
    fi
done)

parallel --jobs 90% --progress \
    python3 src/timer.py {1} {2} $NEXT_RUN $COLLECT_CLOSURES_FLAG \
    ::: "${RUNNERS[@]}" \
    ::: $FILES
