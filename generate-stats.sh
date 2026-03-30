#!/bin/bash
# ═══════════════════════════════════════════════════════════════
#  generate-stats.sh — Counts real project stats and writes stats.json
#  Run from anywhere. Outputs to the github.io repo.
# ═══════════════════════════════════════════════════════════════

PROJECTS_DIR="$HOME/projects"
OUTPUT="$PROJECTS_DIR/studyalwaysbro.github.io/stats.json"

EXCLUDE="-not -path */.venv/* -not -path */venv/* -not -path */.git/* -not -path */__pycache__/* -not -path */node_modules/* -not -path */dist/* -not -path */.next/* -not -path */reports/*"

# Lines of code (source files only, no generated reports)
loc=$(find "$PROJECTS_DIR" -type f \( -name "*.py" -o -name "*.js" -o -name "*.ts" -o -name "*.jsx" -o -name "*.tsx" -o -name "*.sh" -o -name "*.sql" -o -name "*.css" -o -name "*.html" \) \
  -not -path "*/.venv/*" -not -path "*/venv/*" -not -path "*/.git/*" -not -path "*/__pycache__/*" \
  -not -path "*/node_modules/*" -not -path "*/dist/*" -not -path "*/.next/*" \
  -not -path "*/reports/*" -not -path "*studyalwaysbro.github.io/stats.json*" \
  -exec cat {} + 2>/dev/null | wc -l)

# Python scripts
python_scripts=$(find "$PROJECTS_DIR" -type f -name "*.py" \
  -not -path "*/.venv/*" -not -path "*/venv/*" -not -path "*/.git/*" -not -path "*/__pycache__/*" \
  -not -path "*/node_modules/*" 2>/dev/null | wc -l)

# Total projects (directories in projects/)
projects=$(find "$PROJECTS_DIR" -maxdepth 1 -mindepth 1 -type d 2>/dev/null | wc -l)

# Total commits across all repos
commits=0
for dir in "$PROJECTS_DIR"/*/; do
  if [ -d "$dir/.git" ]; then
    c=$(git -C "$dir" rev-list --count HEAD 2>/dev/null || echo 0)
    commits=$((commits + c))
  fi
done

# Data sources (hardcoded — these don't change often)
data_sources=8

# Format LOC as "85K+" style
if [ "$loc" -ge 1000 ]; then
  loc_display="$((loc / 1000))K+"
else
  loc_display="$loc"
fi

# Write JSON
cat > "$OUTPUT" << EOF
{
  "loc": $loc,
  "loc_display": "$loc_display",
  "python_scripts": $python_scripts,
  "projects": $projects,
  "commits": $commits,
  "data_sources": $data_sources,
  "updated": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF

echo "Stats written to $OUTPUT"
echo "  LOC: $loc ($loc_display)"
echo "  Python scripts: $python_scripts"
echo "  Projects: $projects"
echo "  Commits: $commits"
