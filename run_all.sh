#!/usr/bin/env bash
# Classify cases: IP-or-not (yes/no/unclear) + rights_asserted, case-level.
# Runs on your Claude Pro subscription via Claude Code headless mode. Resume-safe.
#
#   bash run_all.sh              # run everything (skips cases already done)
#   bash run_all.sh test         # run only the small validation set first
#   bash run_all.sh 800 900      # run cases CS_COMM_800_2023 to CS_COMM_900_2023
#   bash run_all.sh 1 50         # run cases CS_COMM_1_2023 to CS_COMM_50_2023

set -u
MODEL="claude-sonnet-5"
INDIR="prompts_full"; OUTDIR="raw"; mkdir -p "$OUTDIR"

if [ "${1:-}" = "test" ]; then
  LIST="CS_COMM_221_2023 CS_COMM_824_2023 CS_COMM_605_2023 CS_COMM_44_2023 \
CS_COMM_288_2023 CS_COMM_931_2023 CS_COMM_10_2023 CS_COMM_120_2023"
  FILES=""; for c in $LIST; do FILES="$FILES $INDIR/$c.txt"; done
elif [ -n "${1:-}" ] && [ -n "${2:-}" ]; then
  # Range mode: bash run_all.sh START END
  START="${1}"; END="${2}"
  FILES=""
  for num in $(seq "$START" "$END"); do
    FILES="$FILES $INDIR/CS_COMM_${num}_2023.txt"
  done
else
  FILES="$INDIR"/*.txt
fi

total=$(echo $FILES | wc -w | tr -d ' '); i=0
for f in $FILES; do
  cid=$(basename "$f" .txt); i=$((i+1))
  out="$OUTDIR/$cid.json"
  if [ -s "$out" ] && ! grep -q '"is_error":true\|Not logged in' "$out"; then
    echo "[$i/$total] skip $cid"; continue
  fi
  echo "[$i/$total] $cid"
  claude -p --model "$MODEL" --output-format json --max-turns 1 < "$f" > "$out" 2> "$OUTDIR/$cid.err"
  sleep 0.3
done
echo "done -> python3 parse_all.py"
