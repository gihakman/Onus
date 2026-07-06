"""Direct-mode tests for the Pact intelligent contract."""

import json

from conftest import (
    deploy_pact,
    hex_of,
    FUTURE_DEADLINE,
    AFTER_DEADLINE,
    VALID_RUNNER_FEE_BPS,
)

ONE_GEN = 10**18


# --------------------------------------------------------------------------------
# Construction & terms
# --------------------------------------------------------------------------------
def test_construct_sets_terms(direct_vm, direct_deploy, direct_owner, direct_alice, direct_bob):
    pact = deploy_pact(direct_deploy, factory=direct_owner, committer=direct_alice,
                       beneficiary=direct_bob)
    d = pact.get_details()
    assert d["committer"].lower() == hex_of(direct_alice)
    assert d["beneficiary"].lower() == hex_of(direct_bob)
    assert d["status"] == "awaiting_funding"
    assert d["outcome"] == "unresolved"
    assert d["stake"] == "0"
    assert d["fee_bps"] == str(VALID_RUNNER_FEE_BPS)
    assert pact.get_status() == "awaiting_funding"
    assert pact.is_resolvable() is False


def test_construct_rejects_empty_commitment(direct_vm, direct_deploy, direct_owner,
                                            direct_alice, direct_bob):
    with direct_vm.expect_revert("commitment_text must not be empty"):
        deploy_pact(direct_deploy, factory=direct_owner, committer=direct_alice,
                    beneficiary=direct_bob, commitment="   ")


def test_construct_rejects_bad_deadline(direct_vm, direct_deploy, direct_owner,
                                        direct_alice, direct_bob):
    with direct_vm.expect_revert("valid ISO 8601"):
        deploy_pact(direct_deploy, factory=direct_owner, committer=direct_alice,
                    beneficiary=direct_bob, deadline="not-a-date")


def test_construct_rejects_bad_fee(direct_vm, direct_deploy, direct_owner,
                                   direct_alice, direct_bob):
    with direct_vm.expect_revert("fee_bps out of range"):
        deploy_pact(direct_deploy, factory=direct_owner, committer=direct_alice,
                    beneficiary=direct_bob, fee_bps=20001)


# --------------------------------------------------------------------------------
# Funding
# --------------------------------------------------------------------------------
def test_fund_success(direct_vm, direct_deploy, direct_owner, direct_alice, direct_bob):
    pact = deploy_pact(direct_deploy, factory=direct_owner, committer=direct_alice,
                       beneficiary=direct_bob)
    direct_vm.sender = direct_alice
    direct_vm.value = ONE_GEN
    pact.fund()
    assert pact.get_status() == "active"
    assert pact.get_details()["stake"] == str(ONE_GEN)


def test_fund_only_committer(direct_vm, direct_deploy, direct_owner, direct_alice, direct_bob):
    pact = deploy_pact(direct_deploy, factory=direct_owner, committer=direct_alice,
                       beneficiary=direct_bob)
    direct_vm.sender = direct_bob
    direct_vm.value = ONE_GEN
    with direct_vm.expect_revert("only the committer can fund"):
        pact.fund()


def test_fund_rejects_zero_value(direct_vm, direct_deploy, direct_owner, direct_alice, direct_bob):
    pact = deploy_pact(direct_deploy, factory=direct_owner, committer=direct_alice,
                       beneficiary=direct_bob)
    direct_vm.sender = direct_alice
    direct_vm.value = 0
    with direct_vm.expect_revert("stake must be greater than zero"):
        pact.fund()


def test_fund_rejects_after_deadline(direct_vm, direct_deploy, direct_owner,
                                     direct_alice, direct_bob):
    pact = deploy_pact(direct_deploy, factory=direct_owner, committer=direct_alice,
                       beneficiary=direct_bob)
    direct_vm.warp(AFTER_DEADLINE)
    direct_vm.sender = direct_alice
    direct_vm.value = ONE_GEN
    with direct_vm.expect_revert("deadline has already passed"):
        pact.fund()


def test_cannot_fund_twice(direct_vm, direct_deploy, direct_owner, direct_alice, direct_bob):
    pact = deploy_pact(direct_deploy, factory=direct_owner, committer=direct_alice,
                       beneficiary=direct_bob)
    direct_vm.sender = direct_alice
    direct_vm.value = ONE_GEN
    pact.fund()
    with direct_vm.expect_revert("not awaiting funding"):
        pact.fund()


# --------------------------------------------------------------------------------
# Evidence
# --------------------------------------------------------------------------------
def _fund(direct_vm, pact, committer):
    direct_vm.sender = committer
    direct_vm.value = ONE_GEN
    pact.fund()


def test_submit_evidence_success(direct_vm, direct_deploy, direct_owner, direct_alice, direct_bob):
    pact = deploy_pact(direct_deploy, factory=direct_owner, committer=direct_alice,
                       beneficiary=direct_bob)
    _fund(direct_vm, pact, direct_alice)
    pact.submit_evidence("https://github.com/example/onus/releases/tag/v1.0")
    assert pact.get_evidence() == ["https://github.com/example/onus/releases/tag/v1.0"]


def test_submit_evidence_only_committer(direct_vm, direct_deploy, direct_owner,
                                        direct_alice, direct_bob):
    pact = deploy_pact(direct_deploy, factory=direct_owner, committer=direct_alice,
                       beneficiary=direct_bob)
    _fund(direct_vm, pact, direct_alice)
    direct_vm.sender = direct_bob
    with direct_vm.expect_revert("only the committer can submit evidence"):
        pact.submit_evidence("https://example.com")


def test_submit_evidence_requires_active(direct_vm, direct_deploy, direct_owner,
                                         direct_alice, direct_bob):
    pact = deploy_pact(direct_deploy, factory=direct_owner, committer=direct_alice,
                       beneficiary=direct_bob)
    direct_vm.sender = direct_alice
    with direct_vm.expect_revert("pact is not active"):
        pact.submit_evidence("https://example.com")


def test_submit_evidence_locked_after_deadline(direct_vm, direct_deploy, direct_owner,
                                               direct_alice, direct_bob):
    pact = deploy_pact(direct_deploy, factory=direct_owner, committer=direct_alice,
                       beneficiary=direct_bob)
    _fund(direct_vm, pact, direct_alice)
    direct_vm.warp(AFTER_DEADLINE)
    with direct_vm.expect_revert("deadline has passed"):
        pact.submit_evidence("https://example.com")


# --------------------------------------------------------------------------------
# Resolution guards
# --------------------------------------------------------------------------------
def test_resolve_requires_active(direct_vm, direct_deploy, direct_owner, direct_alice, direct_bob):
    pact = deploy_pact(direct_deploy, factory=direct_owner, committer=direct_alice,
                       beneficiary=direct_bob)
    with direct_vm.expect_revert("pact is not active"):
        pact.resolve()


def test_resolve_before_deadline_reverts(direct_vm, direct_deploy, direct_owner,
                                         direct_alice, direct_bob):
    pact = deploy_pact(direct_deploy, factory=direct_owner, committer=direct_alice,
                       beneficiary=direct_bob)
    _fund(direct_vm, pact, direct_alice)
    with direct_vm.expect_revert("deadline has not passed yet"):
        pact.resolve()


# --------------------------------------------------------------------------------
# Resolution adjudication (leader path + validator agreement)
# --------------------------------------------------------------------------------
def _setup_active_pact_with_evidence(direct_vm, direct_deploy, factory, committer, beneficiary):
    pact = deploy_pact(direct_deploy, factory=factory, committer=committer, beneficiary=beneficiary)
    _fund(direct_vm, pact, committer)
    pact.submit_evidence("https://github.com/example/onus/releases/tag/v1.0")
    direct_vm.warp(AFTER_DEADLINE)
    return pact


def test_resolve_kept(direct_vm, direct_deploy, direct_owner, direct_alice, direct_bob):
    pact = _setup_active_pact_with_evidence(direct_vm, direct_deploy,
                                            direct_owner, direct_alice, direct_bob)
    direct_vm.mock_web(r".*github\.com.*", {"status": 200, "body": "Release v1.0 — shipped."})
    direct_vm.mock_llm(r".*neutral, impartial referee.*",
                       json.dumps({"outcome": "kept", "partial_bps": 10000,
                                   "rationale": "The repo shows a tagged v1.0 release."}))
    direct_vm.sender = direct_bob  # anyone may resolve
    pact.resolve()
    d = pact.get_details()
    assert d["status"] == "resolved"
    assert d["outcome"] == "kept"
    assert d["partial_bps"] == "10000"


def test_resolve_broken(direct_vm, direct_deploy, direct_owner, direct_alice, direct_bob):
    pact = _setup_active_pact_with_evidence(direct_vm, direct_deploy,
                                            direct_owner, direct_alice, direct_bob)
    direct_vm.mock_web(r".*github\.com.*", {"status": 200, "body": "No releases yet."})
    direct_vm.mock_llm(r".*neutral, impartial referee.*",
                       json.dumps({"outcome": "broken", "partial_bps": 0,
                                   "rationale": "No v1.0 release exists."}))
    pact.resolve()
    d = pact.get_details()
    assert d["outcome"] == "broken"
    assert d["status"] == "resolved"


def test_resolve_partial_clamps(direct_vm, direct_deploy, direct_owner, direct_alice, direct_bob):
    pact = _setup_active_pact_with_evidence(direct_vm, direct_deploy,
                                            direct_owner, direct_alice, direct_bob)
    direct_vm.mock_web(r".*github\.com.*", {"status": 200, "body": "Beta only."})
    direct_vm.mock_llm(r".*neutral, impartial referee.*",
                       json.dumps({"outcome": "partial", "partial_bps": 4000,
                                   "rationale": "A beta shipped but not a full v1.0."}))
    pact.resolve()
    assert pact.get_details()["outcome"] == "partial"
    assert pact.get_details()["partial_bps"] == "4000"


def test_validator_agrees_on_matching_outcome(direct_vm, direct_deploy, direct_owner,
                                              direct_alice, direct_bob):
    pact = _setup_active_pact_with_evidence(direct_vm, direct_deploy,
                                            direct_owner, direct_alice, direct_bob)
    direct_vm.mock_web(r".*github\.com.*", {"status": 200, "body": "Release v1.0 — shipped."})
    direct_vm.mock_llm(r".*neutral, impartial referee.*",
                       json.dumps({"outcome": "kept", "partial_bps": 10000, "rationale": "ok"}))
    pact.resolve()
    # A validator re-running against the same evidence must agree.
    assert direct_vm.run_validator() is True


def test_validator_disagrees_on_conflicting_outcome(direct_vm, direct_deploy, direct_owner,
                                                    direct_alice, direct_bob):
    pact = _setup_active_pact_with_evidence(direct_vm, direct_deploy,
                                            direct_owner, direct_alice, direct_bob)
    direct_vm.mock_web(r".*github\.com.*", {"status": 200, "body": "Release v1.0 — shipped."})
    direct_vm.mock_llm(r".*neutral, impartial referee.*",
                       json.dumps({"outcome": "kept", "partial_bps": 10000, "rationale": "ok"}))
    pact.resolve()
    # Now the validator's own view of the world says "broken" — it must reject a "kept" leader.
    direct_vm.clear_mocks()
    direct_vm.mock_web(r".*github\.com.*", {"status": 200, "body": "No releases yet."})
    direct_vm.mock_llm(r".*neutral, impartial referee.*",
                       json.dumps({"outcome": "broken", "partial_bps": 0, "rationale": "none"}))
    assert direct_vm.run_validator() is False
