#!/usr/bin/env bash
# find_example.sh — locate verified NI Measurement Plug-In examples that use a given
# DataType (measurement.py) or UI control (.measui).
#
# The example files are the source of truth. This script only points you to file:line
# so you Read and copy the real block — it deliberately does not transcribe XML, so it
# can never go stale.
set -euo pipefail

# Resolve the repo root from the script location (robust to the current directory).
ROOT="$(git -C "$(dirname "${BASH_SOURCE[0]}")" rev-parse --show-toplevel 2>/dev/null || true)"
if [ -z "$ROOT" ]; then
  ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
fi
EXAMPLES_DIR="$ROOT/src/examples/meas-plugin"

if [ ! -d "$EXAMPLES_DIR" ]; then
  echo "Examples directory not found: $EXAMPLES_DIR" >&2
  exit 2
fi

if [ $# -eq 0 ]; then
  echo "Usage: find_example.sh <term>"
  echo "  <term> = a DataType (e.g. Enum, DoubleXYData) or a .measui tag (e.g. ChannelLED)"
  echo ""
  echo "DataTypes present in the examples:"
  grep -rhoE "DataType\.[A-Za-z0-9]+" "$EXAMPLES_DIR" --include=measurement.py \
    | sort | uniq -c | sort -rn | sed 's/^/  /'
  exit 0
fi

term="$1"
rel() { sed "s#${EXAMPLES_DIR}/##"; }
found=0

# 1) measurement.py — DataType.<term>
py_hits="$(grep -rnE "DataType\.${term}\b" "$EXAMPLES_DIR" --include=measurement.py || true)"
if [ -n "$py_hits" ]; then
  found=1
  echo "### measurement.py — DataType.${term}"
  echo "$py_hits" | rel
  echo ""
  echo "### .measui in those same plug-ins (UI counterpart to copy from)"
  echo "$py_hits" | cut -d: -f1 | xargs -r -n1 dirname | sort -u | while read -r d; do
    for m in "$d"/*.measui; do
      [ -e "$m" ] && echo "  ${m#"$EXAMPLES_DIR"/}"
    done
  done
  echo ""
fi

# 2) .measui — <term ...> element usage
measui_hits="$(grep -rnE "<${term}[ />]" "$EXAMPLES_DIR" --include='*.measui' || true)"
if [ -n "$measui_hits" ]; then
  found=1
  echo "### .measui — <${term}> element usage (first 40 hits)"
  echo "$measui_hits" | rel | head -40
  echo ""
fi

if [ "$found" -eq 0 ]; then
  echo "No examples found for '${term}'."
  echo "Try a DataType (run with no args to list them) or a .measui control tag such as:"
  echo "  ChannelNumericText ChannelEnumSelector ChannelLED ChannelArrayViewer ArrayGraph HmiGraphPlot ChannelPinSelector"
  exit 1
fi
