#!/bin/bash
# Script to analyze and fix em-dashes in THE FEED manuscript

FILE="/root/.openclaw/workspace/creative_projects/THE_FEED_Volume_1_Expanded.md"

echo "=== EM-DASH ANALYSIS ==="
echo ""

# Count total em-dashes
TOTAL=$(grep -c '—' "$FILE")
echo "Total em-dashes: $TOTAL"
echo ""

# Categorize em-dashes

echo "1. INTERRUPTED DIALOG (keep em-dash):"
grep -n '—"' "$FILE" | wc -l
echo "   Count: $(grep -n '—"' "$FILE" | wc -l)"
echo ""

echo "2. EM-DASHES IN ITALICIZED COMPANION DIALOGUE (keep - these are narrative interruptions):"
grep -n '\*.*—.*\*' "$FILE" | wc -l
echo "   Count: $(grep -n '\*.*—.*\*' "$FILE" | wc -l)"
echo ""

echo "3. HYPHENATED COMPOUNDS (keep em-dash):"
grep -n '[a-zA-Z]—[a-zA-Z]' "$FILE" | wc -l
echo "   Count: $(grep -n '[a-zA-Z]—[a-zA-Z]' "$FILE" | wc -l)"
echo ""

echo "4. OTHER EM-DASHES (need review):"
# These are em-dashes used for parenthetical breaks, appositives, etc.
# Should be replaced with commas, periods, or parentheses
