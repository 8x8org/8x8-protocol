#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "msg215_protocol_cases.json"
DATA = json.loads(FIXTURE.read_text(encoding="utf-8"))
SHA256_RE = re.compile(r"^sha256:[a-f0-9]{64}$")
COMMIT_RE = re.compile(r"^[a-f0-9]{40}$")
COMMIT_EVIDENCE_RE = re.compile(r"^commit:[a-f0-9]{40}$")
GENERIC_EVIDENCE_RE = re.compile(r"^(receipt|source|artifact|registry):[A-Za-z0-9][A-Za-z0-9._:/@+-]{2,509}$")
RECEIPT_RE = re.compile(r"^receipt:[A-Za-z0-9][A-Za-z0-9._:/@+-]{2,503}$")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def valid_evidence_ref(ref: str) -> bool:
    return bool(
        SHA256_RE.fullmatch(ref)
        or COMMIT_EVIDENCE_RE.fullmatch(ref)
        or GENERIC_EVIDENCE_RE.fullmatch(ref)
    )


def test_pricing() -> None:
    unit = Decimal(DATA["pricing"]["monthly_unit_usd"])
    expected = DATA["pricing"]["expected_totals"]
    for months_text, total_text in expected.items():
        months = int(months_text)
        require(unit * months == Decimal(total_text), f"incorrect prepaid total for {months} months")

    for plan in DATA["positive"]["subscriptions"]:
        if plan["plan_id"] == "TRIAL_88_MIN":
            require(plan["trial_seconds"] == 5280, "trial must be exactly 5,280 seconds")
            require(plan["price_usd"] == "0.00", "trial must be free")
        else:
            expected_total = expected[str(plan["billing_months"])]
            require(plan["price_usd"] == expected_total, "paid plan total must equal 8.88 times term months")
            require(plan["trial_seconds"] == 0, "paid plans must not mint a second trial")

    bad = DATA["negative"]["discount_invented_total"]
    require(Decimal(bad["price_usd"]) != unit * bad["billing_months"], "negative pricing fixture must be rejected")
    require(DATA["negative"]["trial_wrong_seconds"] != 5280, "negative trial fixture must be rejected")


def test_identity_and_auth() -> None:
    profile = DATA["positive"]["user_profile"]
    require(profile["profile_id"].startswith("8X8-"), "profile ID namespace required")
    require(profile["email_state"] == "VERIFIED", "active trial fixture requires verified email")
    require(profile["privacy"]["legal_name_public"] is False, "legal name must remain private")
    require(len({(link["provider"], link["state"]) for link in profile["identity_links"]}) == len(profile["identity_links"]), "identity links must be unique")

    auth = DATA["positive"]["auth_security"]
    require(auth["plaintext_password_forbidden"] is True, "plaintext password storage forbidden")
    require(auth["passkey_secret_material_server_stored"] is False, "server must not retain passkey secret material")
    require(auth["recovery_token_single_use"] is True, "recovery tokens must be single use")
    require(auth["session_revocation_supported"] is True, "session revocation required")
    require(auth["anti_replay_nonce_required"] is True, "anti-replay nonce required")
    require(auth["multi_account_abuse_detection"] is True, "multi-account abuse controls required")
    require(auth["sensitive_log_redaction"] is True, "sensitive log redaction required")

    unsafe = DATA["negative"]["auth_unsafe"]
    require(unsafe["password_storage"] == "PLAINTEXT", "unsafe password fixture must remain unsafe")
    require(not unsafe["recovery_token_single_use"], "unsafe recovery fixture must be rejected")
    require(not unsafe["anti_replay_nonce_required"], "unsafe replay fixture must be rejected")


def test_discord_authority() -> None:
    discord = DATA["positive"]["discord"]
    require(discord["default_mode"] in {"READ_ONLY", "DRAFT_ONLY", "OWNER_GATED_WRITE"}, "invalid Discord mode")
    require(discord["public_post_requires_gate"] is True, "public Discord posts require exact gate")
    require(discord["dm_requires_gate"] is True, "Discord DMs require exact gate")
    require(discord["admin_actions_forbidden"] is True, "Discord administration forbidden")
    require(discord["financial_actions_forbidden"] is True, "financial Discord actions forbidden")
    require(discord["credential_export_forbidden"] is True, "credential export forbidden")
    require(discord["store_private_dm_body"] is False, "private DM bodies must not be retained")
    require(discord["redaction_required"] is True, "redaction required")
    require(len(discord["channel_allowlist"]) == len(set(discord["channel_allowlist"])), "Discord allowlist must be unique")

    unsafe = DATA["negative"]["discord_unsafe"]
    require(not unsafe["public_post_requires_gate"], "unsafe public-post fixture must be rejected")
    require(unsafe["store_private_dm_body"], "unsafe DM-retention fixture must be rejected")


def test_model_and_agent_truth() -> None:
    registry = DATA["positive"]["registry"]
    model_ids = [item["model_id"] for item in registry["models"]]
    agent_ids = [item["agent_id"] for item in registry["agents"]]
    require(len(model_ids) == len(set(model_ids)), "model counts require unique records")
    require(len(agent_ids) == len(set(agent_ids)), "agent counts require unique records")

    for model in registry["models"]:
        require(model["evidence"], "model record requires evidence")
        require(all(valid_evidence_ref(ref) for ref in model["evidence"]), "model evidence must use a typed canonical reference")
        require(model["status"] != "VERIFIED_RUNNING" or any(RECEIPT_RE.fullmatch(ref) for ref in model["evidence"]), "running model requires runtime receipt")

    for agent in registry["agents"]:
        require(agent["evidence"], "agent record requires evidence")
        require(all(valid_evidence_ref(ref) for ref in agent["evidence"]), "agent evidence must use a typed canonical reference")
        if agent["status"] == "PERSONA_ONLY":
            require(agent.get("productive_receipt_ref") is None, "persona cannot claim productive runtime")
        if agent["status"] == "VERIFIED_ACTIVE":
            require(bool(agent.get("productive_receipt_ref")), "active/productive agent requires receipt")
            require(RECEIPT_RE.fullmatch(agent["productive_receipt_ref"]) is not None, "productive receipt must use receipt namespace")
            require(any(RECEIPT_RE.fullmatch(ref) for ref in agent["evidence"]), "active agent evidence must include a runtime receipt")

    require(len(set(DATA["negative"]["duplicate_model_ids"])) < len(DATA["negative"]["duplicate_model_ids"]), "duplicate model fixture must be rejected")
    require(len(set(DATA["negative"]["duplicate_agent_ids"])) < len(DATA["negative"]["duplicate_agent_ids"]), "duplicate agent fixture must be rejected")
    require(all(not valid_evidence_ref(ref) for ref in DATA["negative"]["malformed_evidence_refs"]), "malformed evidence fixtures must be rejected")
    fake_model = DATA["negative"]["running_model_without_receipt"]
    require(fake_model["status"] == "VERIFIED_RUNNING" and not any(RECEIPT_RE.fullmatch(ref) for ref in fake_model["evidence"]), "false model liveness fixture must be rejected")
    fake = DATA["negative"]["persona_claimed_active_without_receipt"]
    require(fake["status"] == "VERIFIED_ACTIVE" and fake["productive_receipt_ref"] is None, "false agent liveness fixture must be rejected")


def test_private_projection_and_receive_only_design() -> None:
    projection = DATA["positive"]["private_projection"]
    require(set(projection["public_fields"]).isdisjoint(projection["restricted_fields"]), "public projection must exclude private fields")
    leak = DATA["negative"]["private_projection_leak"]
    require(any(item in projection["restricted_fields"] for item in leak), "private projection leak fixture must be rejected")

    design = DATA["positive"]["payment_design"]
    require(design["BTC"] == "WATCH_ONLY_OR_RECEIVE_ONLY", "BTC adapter must remain receive/watch only")
    require(design["XMR"] == "VIEW_ONLY_AND_UNIQUE_SUBADDRESS", "XMR adapter must remain view/receive only")
    require(design["spend_authority_in_public_service"] is False, "public service cannot contain spend authority")
    require(design["live_actions"] is False, "fixtures must not perform live actions")

    unsafe = DATA["negative"]["wallet_unsafe"]
    require(unsafe["spend_authority_in_public_service"] is True, "unsafe wallet fixture must be rejected")
    require(unsafe["live_actions"] is True, "unsafe live-action fixture must be rejected")


def test_cryptographic_receipt_and_provenance() -> None:
    receipt = DATA["positive"]["cryptographic_receipt"]
    require(SHA256_RE.fullmatch(receipt["subject_digest"]) is not None, "receipt digest must be a canonical SHA-256 reference")
    require(receipt["signature_state"] == "SIGNED_VERIFIED", "positive fixture requires a verified signature state")
    require(receipt["signature"] is not None, "verified signature state requires signature evidence")
    require(receipt["signature"]["scheme"] in {"ED25519", "ECDSA_P256", "RSA_PSS", "SIGSTORE_KEYLESS"}, "unsupported signature scheme")
    require(receipt["signature"]["signature_ref"].startswith(("sigstore:", "signature:")), "signature must reference verification material")
    require(COMMIT_RE.fullmatch(receipt["provenance"]["source_commit"]) is not None, "provenance requires a full commit digest")
    require(receipt["provenance"]["slsa_level"] >= 1, "positive provenance fixture requires at least SLSA level 1 metadata")
    require(bool(receipt["provenance"]["in_toto_statement_ref"]), "in-toto statement reference required")
    require(receipt["supply_chain"]["tuf_metadata_state"] == "VERIFIED", "TUF metadata must be verified")
    require(receipt["supply_chain"]["sbom_state"] == "CYCLONEDX_VERIFIED", "CycloneDX SBOM must be verified")
    require(receipt["supply_chain"]["sigstore_state"] == "VERIFIED", "Sigstore bundle must be verified")
    require(receipt["privacy"]["contains_secrets"] is False, "receipt must not contain secrets")
    require(receipt["privacy"]["contains_private_payload"] is False, "receipt must not contain private payloads")

    mislabeled = DATA["negative"]["hash_mislabeled_signature"]
    require(SHA256_RE.fullmatch(mislabeled["subject_digest"]) is not None, "negative fixture still needs a valid hash")
    require(mislabeled["signature_state"] == "SIGNED_VERIFIED" and mislabeled["signature"] is None, "hash-only evidence must not be called a verified signature")

    unsafe = DATA["negative"]["provenance_unsafe"]
    require(COMMIT_RE.fullmatch(unsafe["source_commit"]) is None, "unsafe provenance must have an invalid commit reference")
    require(unsafe["contains_secrets"] is True, "unsafe provenance fixture must expose secret risk")
    require(unsafe["contains_private_payload"] is True, "unsafe provenance fixture must expose private-payload risk")
    require(unsafe["sigstore_state"] == "INVALID", "invalid Sigstore state must be rejected")
    require(unsafe["tuf_metadata_state"] == "INVALID", "invalid TUF state must be rejected")


def main() -> None:
    tests = [
        test_pricing,
        test_identity_and_auth,
        test_discord_authority,
        test_model_and_agent_truth,
        test_private_projection_and_receive_only_design,
        test_cryptographic_receipt_and_provenance,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"PASS total={len(tests)} fixture={FIXTURE.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
