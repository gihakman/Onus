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
# Tightened consensus: validators must agree on the EXACT (quantized) payout
# --------------------------------------------------------------------------------
def test_partial_quantized_to_grid(direct_vm, direct_deploy, direct_alice, direct_bob):
    """A raw partial_bps is snapped to the 500 bps grid on storage/settlement."""
    onus, pid = _active_with_evidence(direct_vm, direct_deploy, direct_alice, direct_bob)
    direct_vm.mock_web(r".*github\.com.*", {"status": 200, "body": "Beta only."})
    direct_vm.mock_llm(r".*neutral, impartial referee.*",
                       json.dumps({"outcome": "partial", "partial_bps": 4200,
                                   "rationale": "A beta shipped but not a full v1.0."}))
    onus.resolve(pid)
    d = onus.get_pact(pid)
    assert d["outcome"] == "partial"
    # 4200 snaps to the nearest 500 bps step -> 4000
    assert d["partial_bps"] == "4000"


def test_partial_grid_extremes_clamped(direct_vm, direct_deploy, direct_alice, direct_bob):
    """A near-full or near-zero partial stays strictly inside the partial range."""
    onus, pid = _active_with_evidence(direct_vm, direct_deploy, direct_alice, direct_bob)
    direct_vm.mock_web(r".*github\.com.*", {"status": 200, "body": "Almost shipped."})
    # 9980 would snap to 10000 (kept) — must clamp to the partial max 9500
    direct_vm.mock_llm(r".*neutral, impartial referee.*",
                       json.dumps({"outcome": "partial", "partial_bps": 9980, "rationale": "almost"}))
    onus.resolve(pid)
    assert onus.get_pact(pid)["partial_bps"] == "9500"


def test_validator_agrees_same_grid_cell(direct_vm, direct_deploy, direct_alice, direct_bob):
    """Two raw partial estimates that snap to the same grid value reach consensus."""
    onus, pid = _active_with_evidence(direct_vm, direct_deploy, direct_alice, direct_bob)
    direct_vm.mock_web(r".*github\.com.*", {"status": 200, "body": "Beta only."})
    # leader: 4100 -> grid 4000
    direct_vm.mock_llm(r".*neutral, impartial referee.*",
                       json.dumps({"outcome": "partial", "partial_bps": 4100, "rationale": "beta"}))
    onus.resolve(pid)
    assert direct_vm.run_validator() is True  # validator reuses the same 4100 mock


def test_validator_disagrees_adjacent_grid_cell(direct_vm, direct_deploy, direct_alice, direct_bob):
    """Estimates snapping to different grid cells fail consensus (no tolerance band)."""
    onus, pid = _active_with_evidence(direct_vm, direct_deploy, direct_alice, direct_bob)
    direct_vm.mock_web(r".*github\.com.*", {"status": 200, "body": "Beta only."})
    # leader: 4100 -> grid 4000
    direct_vm.mock_llm(r".*neutral, impartial referee.*",
                       json.dumps({"outcome": "partial", "partial_bps": 4100, "rationale": "beta"}))
    onus.resolve(pid)
    # validator sees a slightly different estimate: 4400 -> grid 4500 (different cell)
    direct_vm.clear_mocks()
    direct_vm.mock_web(r".*github\.com.*", {"status": 200, "body": "Beta only."})
    direct_vm.mock_llm(r".*neutral, impartial referee.*",
                       json.dumps({"outcome": "partial", "partial_bps": 4400, "rationale": "beta"}))
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


def test_accumulated_fees_default_zero(direct_vm, direct_deploy):
    onus = deploy_onus(direct_deploy)
    assert onus.get_accumulated_fees() == 0


# --------------------------------------------------------------------------------
# Fee accounting: accrued fees are separated from escrowed pact principal
# --------------------------------------------------------------------------------
def test_resolve_accrues_fee(direct_vm, direct_deploy, direct_alice, direct_bob):
    onus, pid = _active_with_evidence(direct_vm, direct_deploy, direct_alice, direct_bob)
    direct_vm.mock_web(r".*github\.com.*", {"status": 200, "body": "Release v1.0 shipped."})
    direct_vm.mock_llm(r".*neutral, impartial referee.*",
                       json.dumps({"outcome": "kept", "partial_bps": 10000, "rationale": "ok"}))
    onus.resolve(pid)
    # fee = 1 GEN * 200 bps / 10000 = 0.02 GEN = 2 * 10**16 atto
    assert onus.get_accumulated_fees() == ONE_GEN * FEE_BPS // 10000


def test_withdraw_fees_only_takes_accrued_not_principal(direct_vm, direct_deploy, direct_owner,
                                                         direct_alice, direct_bob):
    """A funded-but-unresolved pact's stake must not be withdrawable as fees."""
    onus, pid = _funded(direct_vm, direct_deploy, direct_alice, direct_bob)
    # The whole 1 GEN stake sits in the contract as escrow principal; no fees accrued yet.
    assert onus.get_accumulated_fees() == 0

    direct_vm.sender = direct_owner
    # Owner tries to withdraw: there is balance (the escrowed stake) but no accrued fees,
    # so this must revert rather than drain the committer's principal.
    with direct_vm.expect_revert("no fees to withdraw"):
        onus.withdraw_fees(hex_of(direct_bob))


def test_withdraw_fees_after_resolve_leaves_principal_intact(direct_vm, direct_deploy, direct_owner,
                                                              direct_alice, direct_bob):
    onus, pid = _active_with_evidence(direct_vm, direct_deploy, direct_alice, direct_bob)
    direct_vm.mock_web(r".*github\.com.*", {"status": 200, "body": "Release v1.0 shipped."})
    direct_vm.mock_llm(r".*neutral, impartial referee.*",
                       json.dumps({"outcome": "kept", "partial_bps": 10000, "rationale": "ok"}))
    onus.resolve(pid)

    fee = ONE_GEN * FEE_BPS // 10000
    assert onus.get_accumulated_fees() == fee

    # Direct mode routes value transfers through a no-op hook, so realized balance
    # is zero unless we seed it. Mirror the on-chain state where the accrued fee is
    # actually held by the contract, plus an unrelated escrowed principal that must
    # NOT be swept.
    principal = ONE_GEN  # a second, still-escrowed stake
    direct_vm.deal(direct_vm._contract_address, fee + principal)

    direct_vm.sender = direct_owner
    onus.withdraw_fees(hex_of(direct_bob))
    # Withdrawing exhausts the accrued-fee counter. (Direct mode's value hook is a
    # no-op, so the realized balance is not actually debited here — the real balance
    # accounting is exercised by the integration tests. What matters in direct mode is
    # that the fee counter is bounded and principal can never be withdrawn as fees.)
    assert onus.get_accumulated_fees() == 0

    # A second withdrawal now reverts (no fees left), even though principal remains.
    with direct_vm.expect_revert("no fees to withdraw"):
        onus.withdraw_fees(hex_of(direct_bob))


def test_withdraw_fees_only_owner(direct_vm, direct_deploy, direct_alice, direct_bob):
    onus = deploy_onus(direct_deploy)
    direct_vm.sender = direct_alice
    with direct_vm.expect_revert("only the owner may call"):
        onus.withdraw_fees(hex_of(direct_bob))


# --------------------------------------------------------------------------------
# Time source: deadline checks use the GenVM runtime transaction clock
# --------------------------------------------------------------------------------
def test_fund_rejects_after_deadline_runtime_clock(direct_vm, direct_deploy, direct_alice, direct_bob):
    """Deadline enforcement is driven by gl.message_raw['datetime'], not host wall-clock."""
    onus, pid = _new_pact(direct_vm, direct_deploy, direct_alice, direct_bob)
    # Warp the runtime transaction clock past the deadline; fund must reject.
    direct_vm.warp(AFTER_DEADLINE)
    direct_vm.sender = direct_alice
    direct_vm.value = ONE_GEN
    with direct_vm.expect_revert("deadline has already passed"):
        onus.fund(pid)
