#!/usr/bin/env bash
# Finalize one language: normalize markup, build, and auto-clear any residual
# translation-introduced warnings (revert those few entries to English), looping
# until the build has no new warnings beyond the English baseline.
# Usage: finalize.sh <lang_code>
# Run from anywhere; paths are resolved relative to this script.
set -u
L="$1"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCS="$(cd "$SCRIPT_DIR/../.." && pwd)"        # docs/tools/i18n -> docs
POT="$SCRIPT_DIR/potool.py"
BASE="$SCRIPT_DIR/baseline_warnings.txt"
cd "$DOCS" || exit 2

# Generate the English baseline once if it's missing (it's a regenerable artifact).
if [ ! -f "$BASE" ]; then
  echo "baseline missing -- generating from an English build..."
  rm -rf "_build/doctrees-en" "_build/html/en"
  python3 -m sphinx -b html -D language=en -d "_build/doctrees-en" . "_build/html/en" 2>&1 \
    | grep -E " (WARNING|ERROR):" | sed 's#/home/[^ ]*/docs/##' \
    | sed -E 's/:<translated>:[0-9]+:/:/' | sort -u > "$BASE"
fi

python3 "$POT" normalize --glob "locale/${L}/LC_MESSAGES/**/*.po" 2>&1 | tail -1

build() {
  rm -rf "_build/html/${L}" "_build/doctrees-${L}"
  python3 -m sphinx -b html -D "language=${L}" -d "_build/doctrees-${L}" . "_build/html/${L}" 2>&1 \
    | grep -E " (WARNING|ERROR):" | sed 's#/home/[^ ]*/docs/##' \
    | sed -E 's/:<translated>:[0-9]+:/:/' | sort -u > "/tmp/warn_${L}.txt"
  comm -13 "$BASE" "/tmp/warn_${L}.txt" > "/tmp/new_${L}.txt"
}

for attempt in 1 2 3 4; do
  build
  n=$(wc -l < "/tmp/new_${L}.txt")
  echo "[${L}] attempt ${attempt}: $(wc -l < /tmp/warn_${L}.txt) total warnings, ${n} new"
  if [ "$n" -eq 0 ]; then
    echo "[${L}] CLEAN: no new warnings beyond baseline."
    exit 0
  fi
  echo "--- new warnings this round ---"; cat "/tmp/new_${L}.txt"
  python3 "$POT" autoclear --lang "$L" --warnings "/tmp/new_${L}.txt"
done

build
n=$(wc -l < "/tmp/new_${L}.txt")
if [ "$n" -eq 0 ]; then echo "[${L}] CLEAN after final pass."; exit 0; fi
echo "[${L}] RESIDUAL ${n} new warnings remain after 4 passes:"; cat "/tmp/new_${L}.txt"
exit 1
