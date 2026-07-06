"""Direct-mode tests for the Onus contract."""

import json

from conftest import (
    deploy_onus,
    create_pact,
    hex_of,
    FEE_BPS,
    FUTURE_DEADLINE,
    AFTER_DEADLINE,
    ONE_GEN,
)


# --------------------------------------------------------------------------------
# Construction & creation
# --------------------------------------------------------------------------------
def test_construct_sets_owner_and_fee(direct_vm, direct_deploy, direct_owner):
    direct_vm.sender = direct_owner
    onus = deploy_onus(direct_deploy)
    assert onus.get_owner().lower() == hex_of(direct_owner)
    assert onus.get_fee_bps() == FEE_BPS
    assert onus.get_pact_count() == 0


def test_construct_rejects_bad_fee(direct_vm, direct_deploy):
    with direct_vm.expect_revert("fee_bps out of range"):
        deploy_onus(direct_deploy, fee_bps=20001)


def test_create_pact_sets_terms(direct_vm, direct_deploy, direct_alice, direct_bob):
    onus = deploy_onus(direct_deploy)
    direct_vm.sender = direct_alice
    pid = create_pact(onus, beneficiary=direct_bob)
    assert pid == 0
    d = onus.get_pact(0)
    assert d["committer"].lower() == hex_of(direct_alice)
    assert d["beneficiary"].lower() == hex_of(direct_bob)
    assert d["status"] == "awaiting_funding"
    assert d["outcome"] == "unresolved"
    assert d["stake"] == "0"
    assert d["fee_bps"] == str(FEE_BPS)
    assert onus.get_pact_count() == 1
    assert onus.get_all_pact_ids() == [0]
    assert onus.get_pacts_by(hex_of(direct_alice)) == [0]


def test_create_rejects_empty_commitment(direct_vm, direct_deploy, direct_alice, direct_bob):
    onus = deploy_onus(direct_deploy)
    direct_vm.sender = direct_alice
    with direct_vm.expect_revert("commitment_text must not be empty"):
        create_pact(onus, beneficiary=direct_bob, commitment="   ")


def test_create_rejects_bad_deadline(direct_vm, direct_deploy, direct_alice, direct_bob):
    onus = deploy_onus(direct_deploy)
    direct_vm.sender = direct_alice
    with direct_vm.expect_revert("valid ISO 8601"):
        create_pact(onus, beneficiary=direct_bob, deadline="not-a-date")


# --------------------------------------------------------------------------------
# Funding
# --------------------------------------------------------------------------------
def _new_pact(direct_vm, direct_deploy, committer, beneficiary):
    onus = deploy_onus(direct_deploy)
    direct_vm.sender = committer
    pid = create_pact(onus, beneficiary=beneficiary)
    return onus, pid


def test_fund_success(direct_vm, direct_deploy, direct_alice, direct_bob):
    onus, pid = _new_pact(direct_vm, direct_deploy, direct_alice, direct_bob)
    direct_vm.sender = direct_alice
    direct_vm.value = ONE_GEN
    onus.fund(pid)
    d = onus.get_pact(pid)
    assert d["status"] == "active"
    assert d["stake"] == str(ONE_GEN)


def test_fund_only_committer(direct_vm, direct_deploy, direct_alice, direct_bob):
    onus, pid = _new_pact(direct_vm, direct_deploy, direct_alice, direct_bob)
    direct_vm.sender = direct_bob
    direct_vm.value = ONE_GEN
    with direct_vm.expect_revert("only the committer can fund"):
        onus.fund(pid)


def test_fund_rejects_zero(direct_vm, direct_deploy, direct_alice, direct_bob):
    onus, pid = _new_pact(direct_vm, direct_deploy, direct_alice, direct_bob)
    direct_vm.sender = direct_alice
    direct_vm.value = 0
    with direct_vm.expect_revert("stake must be greater than zero"):
        onus.fund(pid)


def test_fund_rejects_after_deadline(direct_vm, direct_deploy, direct_alice, direct_bob):
    onus, pid = _new_pact(direct_vm, direct_deploy, direct_alice, direct_bob)
    direct_vm.warp(AFTER_DEADLINE)
    direct_vm.sender = direct_alice
    direct_vm.value = ONE_GEN
    with direct_vm.expect_revert("deadline has already passed"):
        onus.fund(pid)


def test_cannot_fund_twice(direct_vm, direct_deploy, direct_alice, direct_bob):
    onus, pid = _new_pact(direct_vm, direct_deploy, direct_alice, direct_bob)
    direct_vm.sender = direct_alice
    direct_vm.value = ONE_GEN
    onus.fund(pid)
    with direct_vm.expect_revert("not awaiting funding"):
        onus.fund(pid)


def test_unknown_pact_id_reverts(direct_vm, direct_deploy, direct_alice):
    onus = deploy_onus(direct_deploy)
    direct_vm.sender = direct_alice
    with direct_vm.expect_revert("unknown pact id"):
        onus.get_pact(99)


# --------------------------------------------------------------------------------
# Evidence
# --------------------------------------------------------------------------------
def _funded(direct_vm, direct_deploy, committer, beneficiary):
    onus, pid = _new_pact(direct_vm, direct_deploy, committer, beneficiary)
    direct_vm.sender = committer
    direct_vm.value = ONE_GEN
    onus.fund(pid)
    return onus, pid


def test_submit_evidence_success(direct_vm, direct_deploy, direct_alice, direct_bob):
    onus, pid = _funded(direct_vm, direct_deploy, direct_alice, direct_bob)
    onus.submit_evidence(pid, "https://github.com/example/onus/releases/tag/v1.0")
    assert onus.get_pact(pid)["evidence"] == [
        "https://github.com/example/onus/releases/tag/v1.0"
    ]


def test_submit_evidence_only_committer(direct_vm, direct_deploy, direct_alice, direct_bob):
    onus, pid = _funded(direct_vm, direct_deploy, direct_alice, direct_bob)
    direct_vm.sender = direct_bob
    with direct_vm.expect_revert("only the committer can submit evidence"):
        onus.submit_evidence(pid, "https://example.com")


def test_submit_evidence_requires_active(direct_vm, direct_deploy, direct_alice, direct_bob):
    onus, pid = _new_pact(direct_vm, direct_deploy, direct_alice, direct_bob)
    direct_vm.sender = direct_alice
    with direct_vm.expect_revert("pact is not active"):
        onus.submit_evidence(pid, "https://example.com")


def test_submit_evidence_locked_after_deadline(direct_vm, direct_deploy, direct_alice, direct_bob):
    onus, pid = _funded(direct_vm, direct_deploy, direct_alice, direct_bob)
    direct_vm.warp(AFTER_DEADLINE)
    with direct_vm.expect_revert("deadline has passed"):
        onus.submit_evidence(pid, "https://example.com")


# --------------------------------------------------------------------------------
# Resolution guards
# --------------------------------------------------------------------------------
def test_resolve_requires_active(direct_vm, direct_deploy, direct_alice, direct_bob):
    onus, pid = _new_pact(direct_vm, direct_deploy, direct_alice, direct_bob)
    with direct_vm.expect_revert("pact is not active"):
        onus.resolve(pid)


def test_resolve_before_deadline_reverts(direct_vm, direct_deploy, direct_alice, direct_bob):
    onus, pid = _funded(direct_vm, direct_deploy, direct_alice, direct_bob)
    with direct_vm.expect_revert("deadline has not passed yet"):
        onus.resolve(pid)


# --------------------------------------------------------------------------------
# Resolution adjudication (leader path + validator agreement)
# --------------------------------------------------------------------------------
def _active_with_evidence(direct_vm, direct_deploy, committer, beneficiary):
    onus, pid = _funded(direct_vm, direct_deploy, committer, beneficiary)
    onus.submit_evidence(pid, "https://github.com/example/onus/releases/tag/v1.0")
    direct_vm.warp(AFTER_DEADLINE)
    return onus, pid


def test_resolve_kept_updates_reputation(direct_vm, direct_deploy, direct_alice, direct_bob):
    onus, pid = _active_with_evidence(direct_vm, direct_deploy, direct_alice, direct_bob)
    direct_vm.mock_web(r".*github\.com.*", {"status": 200, "body": "Release v1.0 shipped."})
    direct_vm.mock_llm(r".*neutral, impartial referee.*",
                       json.dumps({"outcome": "kept", "partial_bps": 10000,
                                   "rationale": "A tagged v1.0 release is present."}))
    direct_vm.sender = direct_bob  # anyone may resolve
    onus.resolve(pid)
    d = onus.get_pact(pid)
    assert d["status"] == "resolved"
    assert d["outcome"] == "kept"
    assert onus.get_reputation(hex_of(direct_alice))["kept"] == "1"


def test_resolve_broken(direct_vm, direct_deploy, direct_alice, direct_bob):
    onus, pid = _active_with_evidence(direct_vm, direct_deploy, direct_alice, direct_bob)
    direct_vm.mock_web(r".*github\.com.*", {"status": 200, "body": "No releases yet."})
    direct_vm.mock_llm(r".*neutral, impartial referee.*",
                       json.dumps({"outcome": "broken", "partial_bps": 0,
                                   "rationale": "No v1.0 release exists."}))
    onus.resolve(pid)
    assert onus.get_pact(pid)["outcome"] == "broken"
    assert onus.get_reputation(hex_of(direct_alice))["broken"] == "1"


def test_resolve_partial(direct_vm, direct_deploy, direct_alice, direct_bob):
    onus, pid = _active_with_evidence(direct_vm, direct_deploy, direct_alice, direct_bob)
    direct_vm.mock_web(r".*github\.com.*", {"status": 200, "body": "Beta only."})
    direct_vm.mock_llm(r".*neutral, impartial referee.*",
                       json.dumps({"outcome": "partial", "partial_bps": 4000,
                                   "rationale": "A beta shipped but not a full v1.0."}))
    onus.resolve(pid)
    d = onus.get_pact(pid)
    assert d["outcome"] == "partial"
    assert d["partial_bps"] == "4000"


def test_validator_agrees(direct_vm, direct_deploy, direct_alice, direct_bob):
    onus, pid = _active_with_evidence(direct_vm, direct_deploy, direct_alice, direct_bob)
    direct_vm.mock_web(r".*github\.com.*", {"status": 200, "body": "Release v1.0 shipped."})
    direct_vm.mock_llm(r".*neutral, impartial referee.*",
                       json.dumps({"outcome": "kept", "partial_bps": 10000, "rationale": "ok"}))
    onus.resolve(pid)
    assert direct_vm.run_validator() is True


def test_validator_disagrees(direct_vm, direct_deploy, direct_alice, direct_bob):
    onus, pid = _active_with_evidence(direct_vm, direct_deploy, direct_alice, direct_bob)
    direct_vm.mock_web(r".*github\.com.*", {"status": 200, "body": "Release v1.0 shipped."})
    direct_vm.mock_llm(r".*neutral, impartial referee.*",
                       json.dumps({"outcome": "kept", "partial_bps": 10000, "rationale": "ok"}))
    onus.resolve(pid)
    direct_vm.clear_mocks()
    direct_vm.mock_web(r".*github\.com.*", {"status": 200, "body": "No releases yet."})
    direct_vm.mock_llm(r".*neutral, impartial referee.*",
                       json.dumps({"outcome": "broken", "partial_bps": 0, "rationale": "none"}))
    assert direct_vm.run_validator() is False


# --------------------------------------------------------------------------------
# Views defaults
# --------------------------------------------------------------------------------
def test_reputation_defaults_zero(direct_vm, direct_deploy, direct_alice):
    onus = deploy_onus(direct_deploy)
    assert onus.get_reputation(hex_of(direct_alice)) == {"kept": "0", "partial": "0", "broken": "0"}


def test_pacts_by_empty(direct_vm, direct_deploy, direct_alice):
    onus = deploy_onus(direct_deploy)
    assert onus.get_pacts_by(hex_of(direct_alice)) == []
