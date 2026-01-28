#!/bin/zsh
# If any errors, undefineds, or pipe fails, exit completely:
set -euo pipefail

# Load environment variables (email creds, date, place id, etc.)
source "$HOME/campwatch/campwatch.env"

# Run using the venv's python directly (no need to "activate" in launchd)
"$HOME/campwatch/.venv/bin/python" "$HOME/campwatch/check_reserveca.py"
