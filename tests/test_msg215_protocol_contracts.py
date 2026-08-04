#!/usr/bin/env python3
from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "msg215_protocol_cases.json"
DATA = json.loads(FIXTURE.read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


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
        require(model["status"] != "VERIFIED_RUNNING" or any(ref.startswith("receipt:") for ref in model["evidence"]), "running model requires runtime receipt")

    for agent in registry["agents"]:
        require(agent["evidence"], "agent record requires evidence")
        if agent["status"] == "PERSONA_ONLY":
            require(agent.get("productive_receipt_ref") is None, "persona cannot claim productive runtime")
        if agent["status"] == "VERIFIED_ACTIVE":
            require(bool(agent.get("productive_receipt_ref")), "active/productive agent requires receipt")

    require(len(set(DATA["negative"]["duplicate_model_ids"])) < len(DATA["negative"]["duplicate_model_ids"]), "duplicate model fixture must be rejected")
    require(len(set(DATA["negative"]["duplicate_agent_ids"])) < len(DATA["negative"]["duplicate_agent_ids"]), "duplicate agent fixture must be rejected")
    fake = DATA["negative"]["persona_claimed_active_without_receipt"]
    require(fake["status"] == "VERIFIED_ACTIVE" and fake["productive_receipt_ref"] is None, "false liveness fixture must be rejected")


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


def main() -> None:
    tests = [
        test_pricing,
        test_identity_and_auth,
        test_discord_authority,
        test_model_and_agent_truth,
        test_private_projection_and_receive_only_design,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"PASS total={len(tests)} fixture={FIXTURE.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
