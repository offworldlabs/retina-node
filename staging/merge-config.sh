#!/usr/bin/env bash
# Manually merge config files for staging
# Combines: default.yml → user.yml → forced.yml = config.yml
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RETINA_NODE_DIR="$(dirname "$SCRIPT_DIR")"

DEFAULT_YML="$RETINA_NODE_DIR/config/default.yml"
FORCED_YML="$RETINA_NODE_DIR/config/forced.yml"
USER_YML="$SCRIPT_DIR/config/user.yml"
OUTPUT_YML="$SCRIPT_DIR/config/config.yml"

echo "Merging configuration files..."
echo "  Default: $DEFAULT_YML"
echo "  User:    $USER_YML"
echo "  Forced:  $FORCED_YML"
echo "  Output:  $OUTPUT_YML"

# Check dependencies
if ! command -v python3 &>/dev/null; then
  echo "Error: python3 not found"
  exit 1
fi

if ! python3 -c "import yaml" 2>/dev/null; then
  echo "Error: PyYAML not installed. Install with: pip3 install pyyaml"
  exit 1
fi

# Create merge script
python3 - <<'PYTHON'
import sys
import yaml
from pathlib import Path

def deep_merge(base, override):
    """Recursively merge override into base"""
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            deep_merge(base[key], value)
        else:
            base[key] = value
    return base

# Read files
default = yaml.safe_load(Path(sys.argv[1]).read_text())
user = yaml.safe_load(Path(sys.argv[2]).read_text()) if Path(sys.argv[2]).exists() else {}
forced = yaml.safe_load(Path(sys.argv[3]).read_text()) if Path(sys.argv[3]).exists() else {}

# Merge: default → user → forced
config = default.copy()
deep_merge(config, user)
deep_merge(config, forced)

# Write output
Path(sys.argv[4]).write_text(yaml.dump(config, default_flow_style=False, sort_keys=False))
print(f"✓ Config merged successfully: {sys.argv[4]}")
PYTHON "$DEFAULT_YML" "$USER_YML" "$FORCED_YML" "$OUTPUT_YML"
