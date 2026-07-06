"""Integration tests for Onus against a real GenLayer environment.

Run with, e.g.:
    gltest tests/integration/ -v -s --network testnet_bradbury

These exercise the parts direct mode cannot: real leader plus validator consensus and
value handling. The full resolution test performs real web fetches and LLM calls and is
marked `slow`.
"""

import pytest
from gltest import get_contract_factory, get_default_account
from gltest.assertions import tx_execution_succeeded

FEE_BPS = 200
FUTURE_DEADLINE = "2999-01-01T00:00:00Z"


def _deploy():
    return get_contract_factory("Onus").deploy(args=[FEE_BPS])


def test_create_and_index_pact():
    """A pact is created, indexed, and immediately readable."""
    onus = _deploy()
    me = get_default_account().address

    tx = onus.create_pact(
        args=[me, "Ship the Onus MVP.", "A public repo shows a v1.0 tag.", FUTURE_DEADLINE],
    ).transact()
    assert tx_execution_succeeded(tx)

    assert onus.get_pact_count(args=[]).call() == 1
    assert onus.get_pacts_by(args=[me]).call() == [0]
    assert onus.get_pact(args=[0]).call()["status"] == "awaiting_funding"


def test_fund_and_evidence():
    """A pact can be funded and accept evidence before its deadline."""
    onus = _deploy()
    me = get_default_account().address

    onus.create_pact(
        args=[me, "Post daily for 30 days.", "A public profile shows 30 posts.", FUTURE_DEADLINE],
    ).transact()

    tx = onus.fund(args=[0], value=10**17).transact()  # 0.1 GEN
    assert tx_execution_succeeded(tx)
    assert onus.get_pact(args=[0]).call()["status"] == "active"

    tx = onus.submit_evidence(args=[0, "https://example.com/profile"]).transact()
    assert tx_execution_succeeded(tx)
    assert onus.get_pact(args=[0]).call()["evidence"] == ["https://example.com/profile"]


@pytest.mark.slow
def test_full_resolution_consensus():
    """End-to-end: fund, submit real evidence, wait past the deadline, resolve."""
    import time
    from datetime import datetime, timezone, timedelta

    onus = _deploy()
    me = get_default_account().address
    deadline = (datetime.now(timezone.utc) + timedelta(seconds=20)).isoformat().replace(
        "+00:00", "Z"
    )

    onus.create_pact(
        args=[me, "Publish a public page that mentions GenLayer.",
              "The evidence URL is reachable and clearly mentions GenLayer.", deadline],
    ).transact()
    assert tx_execution_succeeded(onus.fund(args=[0], value=10**17).transact())
    assert tx_execution_succeeded(
        onus.submit_evidence(args=[0, "https://docs.genlayer.com/"]).transact()
    )

    time.sleep(25)
    tx = onus.resolve(args=[0]).transact()
    assert tx_execution_succeeded(tx)
    d = onus.get_pact(args=[0]).call()
    assert d["status"] == "resolved"
    assert d["outcome"] in ("kept", "partial", "broken")
