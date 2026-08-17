# Runtime Integration Reference

This directory contains the public reference path from the Coordination Kernel to a local 8x8 runtime.

## Components

- `context_publisher.py` creates redacted, digest-bound context snapshots.
- `lease_broker.py` atomically rejects overlapping active write leases.
- `live_state_server.py` serves loopback-only read-only state.
- `install_termux_ubuntu_reference.sh` plans or performs a reversible file installation without activation.

## Quick validation

```bash
python -m unittest tests.test_runtime_integration -v
bash -n runtime_integration/install_termux_ubuntu_reference.sh
bash runtime_integration/install_termux_ubuntu_reference.sh
```

The installer defaults to plan-only. `--apply` copies files but does not start a service or expose a port.

## Truth state

Repository state: `IMPLEMENTED_REFERENCE_NOT_LIVE`.

Live Termux/Ubuntu activation requires a fresh local inventory, non-overlapping lease, signing decision, loopback canary, method restriction test, secret scan, cleanup, rollback test, and activation receipt.
