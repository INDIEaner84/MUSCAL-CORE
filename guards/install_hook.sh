#!/bin/bash
# install_hook.sh — Installiert den Pre-Commit Hook fuer MUSCAL CORE
#
# Nutzung: bash guards/install_hook.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
HOOK_SRC="$SCRIPT_DIR/pre_commit_hook.py"
GIT_DIR="$ROOT_DIR/.git"
HOOK_DST="$GIT_DIR/hooks/pre-commit"

# Pruefen ob .git existiert
if [ ! -d "$GIT_DIR" ]; then
    echo "ERROR: Kein .git Verzeichnis gefunden in $ROOT_DIR"
    echo "Initialisiere zuerst ein Git-Repository: git init"
    exit 1
fi

# Hook erstellen
cat > "$HOOK_DST" << 'HOOKEOF'
#!/bin/bash
# MUSCAL CORE — Pre-Commit Governance Hook
# Automatisch installiert von guards/install_hook.sh

python "$(git rev-parse --show-toplevel)/guards/pre_commit_hook.py" "$@"
HOOKEOF

chmod +x "$HOOK_DST"

echo "OK: Pre-Commit Hook installiert: $HOOK_DST"
echo "    Core-Dateien werden bei jedem Commit geprueft."
echo "    Override: git commit --allow-core-write ..."
