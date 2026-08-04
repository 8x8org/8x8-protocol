#!/usr/bin/env python3
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "msg215_auth_lifecycle_cases.json"
DATA = json.loads(FIXTURE.read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def parse_utc(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def test_credential_boundary() -> None:
    credential = DATA["positive"]["credential"]
    require(credential["password_storage"] in {"ARGON2ID", "SCRYPT", "PBKDF2_APPROVED", "NOT_APPLICABLE"}, "approved password storage required")
    require(credential["passkey_private_material_server_stored"] is False, "passkey private material must not be stored server-side")
    require(credential["step_up_required_for_sensitive_actions"] is True, "sensitive actions require step-up authentication")
    require(DATA["negative"]["plaintext_password"]["password_storage"] == "PLAINTEXT", "plaintext-password fixture must be rejected")
    require(DATA["negative"]["server_stored_passkey_secret"]["passkey_private_material_server_stored"] is True, "server-stored passkey secret must be rejected")


def test_session_replay_and_revocation() -> None:
    session = DATA["positive"]["session"]
    require(session["session_id"].startswith("ses_"), "typed session ID required")
    require(len(session["nonce"]) >= 22, "session nonce must provide sufficient entropy representation")
    require(session["replay_cache_required"] is True, "replay cache is required")
    require(session["revocation_supported"] is True, "session revocation is required")
    require(session["rotation_counter"] >= 0, "rotation counter must be monotonic-compatible")
    require(parse_utc(session["expires_at"]) > parse_utc(session["issued_at"]), "session expiry must follow issue time")
    bad_replay = DATA["negative"]["replayable_session"]
    require(len(bad_replay["nonce"]) < 22 and bad_replay["replay_cache_required"] is False, "replayable-session fixture must be rejected")
    require(DATA["negative"]["non_revocable_session"]["revocation_supported"] is False, "non-revocable session must be rejected")


def test_recovery_lifecycle() -> None:
    recovery = DATA["positive"]["recovery"]
    require(recovery["token_hash_only"] is True, "recovery tokens must be stored hash-only")
    require(recovery["single_use"] is True, "recovery tokens must be single use")
    require(300 <= recovery["expires_in_seconds"] <= 3600, "recovery token lifetime must be bounded")
    require(recovery["invalidates_existing_sessions"] is True, "successful recovery must invalidate existing sessions")
    require(recovery["audit_receipt_required"] is True, "recovery requires an audit receipt")
    bad = DATA["negative"]["reusable_recovery"]
    require(not bad["token_hash_only"] and not bad["single_use"] and not bad["invalidates_existing_sessions"], "reusable recovery fixture must be rejected")
    require(DATA["negative"]["long_lived_recovery"]["expires_in_seconds"] > 3600, "long-lived recovery fixture must be rejected")


def test_abuse_and_redaction() -> None:
    abuse = DATA["positive"]["abuse_controls"]
    require(abuse["rate_limit_keyed"] is True, "keyed rate limiting required")
    require(abuse["multi_account_detection"] is True, "multi-account abuse detection required")
    require(abuse["device_signal_minimized"] is True, "device signals must be minimized")
    require(abuse["trial_reissue_default"] == "DENY", "trial reissue must default deny")
    require(DATA["negative"]["trial_reissue_allowed"]["trial_reissue_default"] == "ALLOW", "trial-reissue fixture must be rejected")

    redaction = DATA["positive"]["redaction"]
    require(redaction == {
        "passwords": "NEVER_LOG",
        "recovery_tokens": "HASH_ONLY",
        "session_tokens": "NEVER_LOG",
        "passkey_assertions": "METADATA_ONLY",
        "private_identity_subjects": "PSEUDONYMIZE",
    }, "strict authentication redaction policy required")
    require("PLAINTEXT" in DATA["negative"]["sensitive_logs"].values(), "sensitive-log fixture must be rejected")


def main() -> None:
    tests = [test_credential_boundary, test_session_replay_and_revocation, test_recovery_lifecycle, test_abuse_and_redaction]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"PASS total={len(tests)} fixture={FIXTURE.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
