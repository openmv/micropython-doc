#!/usr/bin/env bash
# Build one language and report any warnings NOT in the English baseline.
# Usage: buildcheck.sh <lang_code>
# Exit 0 => clean (no new warnings); exit 1 => new warnings (printed).
# Run from anywhere; paths are resolved relative to this script.
set -u
LANG_CODE="$1"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCS="$(cd "$SCRIPT_DIR/../.." && pwd)"        # docs/tools/i18n -> docs
POT="$SCRIPT_DIR/potool.py"
BASE="$SCRIPT_DIR/baseline_warnings.txt"
cd "$DOCS" || exit 2

# Safety net: re-pad/validate before building (idempotent).
python3 "$POT" normalize --glob "locale/${LANG_CODE}/LC_MESSAGES/**/*.po" 2>&1 | tail -1

rm -rf "_build/html/${LANG_CODE}" "_build/doctrees-${LANG_CODE}"
python3 -m sphinx -b html -D "language=${LANG_CODE}" \
  -d "_build/doctrees-${LANG_CODE}" . "_build/html/${LANG_CODE}" 2>&1 \
  | grep -E " (WARNING|ERROR):" | sed 's#/home/[^ ]*/docs/##' \
  | sed -E 's/:<translated>:[0-9]+:/:/' | sort -u > "/tmp/warn_${LANG_CODE}.txt"

NEW=$(comm -13 "$BASE" "/tmp/warn_${LANG_CODE}.txt")
TOTAL=$(wc -l < "/tmp/warn_${LANG_CODE}.txt")
echo "=== ${LANG_CODE}: ${TOTAL} total warnings, baseline $(wc -l < "$BASE") ==="
if [ -n "$NEW" ]; then
  echo "=== NEW warnings (translation-introduced): ==="
  echo "$NEW"
  exit 1
fi
echo "CLEAN: no new warnings beyond baseline."
exit 0
