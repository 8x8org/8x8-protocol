#!/usr/bin/env bash
set -Eeuo pipefail

# 8x8 Runtime Integration Kernel 0.0.1 reference installer.
# Defaults to plan-only. --apply copies files and writes configuration, but does
# not start services, modify databases, expose ports, or replace active agents.

MODE="plan"
PREFIX="${PREFIX:-/data/data/com.termux/files/usr}"
ROOT="${HOME}/.8x8-runtime-integration-0.0.1"
SOURCE_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"

for arg in "$@"; do
  case "$arg" in
    --apply) MODE="apply" ;;
    --root=*) ROOT="${arg#*=}" ;;
    *) echo "Unknown argument: $arg" >&2; exit 2 ;;
  esac
done

stamp="$(date -u +%Y%m%dT%H%M%SZ)"
backup="${ROOT}.backup.${stamp}"

echo "PRODUCT_VERSION=0.0.1"
echo "MODE=$MODE"
echo "TARGET_ROOT=$ROOT"
echo "BACKUP_ROOT=$backup"
echo "SERVICE_START=NO"
echo "DATABASE_MUTATION=NO"
echo "REMOTE_EXPOSURE=NO"
echo "ACTIVE_LEASE_REQUIRED_BEFORE_ACTIVATION=YES"

if [[ "$MODE" != "apply" ]]; then
  exit 0
fi

if [[ -e "$ROOT" ]]; then
  cp -a "$ROOT" "$backup"
fi
mkdir -p "$ROOT/bin" "$ROOT/state" "$ROOT/run" "$ROOT/receipts"
install -m 0755 "$SOURCE_DIR/context_publisher.py" "$ROOT/bin/context_publisher.py"
install -m 0755 "$SOURCE_DIR/lease_broker.py" "$ROOT/bin/lease_broker.py"
install -m 0755 "$SOURCE_DIR/live_state_server.py" "$ROOT/bin/live_state_server.py"

cat > "$ROOT/ACTIVATION_REQUIRED.md" <<'EOF'
# Activation required

Files are installed but no process is running. Before activation, record:

- exact task and agent identity;
- active write lease and non-conflict evidence;
- target node and ports;
- current service and repository baselines;
- signing-key custody decision;
- local-only or authenticated transport;
- canary tests;
- cleanup and rollback commands;
- final activation receipt.
EOF

python3 - <<PY
import hashlib, json
from pathlib import Path
root = Path(${ROOT@Q})
files = []
for path in sorted((root / "bin").iterdir()):
    files.append({"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
receipt = {
    "product_version": "0.0.1",
    "status": "INSTALLED_NOT_ACTIVATED",
    "created_at": ${stamp@Q},
    "target_root": str(root),
    "backup_root": ${backup@Q} if Path(${backup@Q}).exists() else None,
    "files": files,
    "service_started": False,
    "database_mutated": False,
    "remote_exposure_enabled": False,
}
(root / "receipts" / "install.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
PY

echo "INSTALL_STATUS=INSTALLED_NOT_ACTIVATED"
