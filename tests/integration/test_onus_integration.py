"""Integration tests for Onus against a real GenLayer environment.

Run with, e.g.:
    gltest tests/integration/ -v -s --network testnet_bradbury

These exercise the parts direct mode cannot: on-chain child deployment via the
factory, real leader+validator consensus, and value handling. The full resolution
test performs real web fetches and LLM calls and is marked `slow`.
"""

from pathlib import Path

import pytest
from gltest import get_contract_factory, get_default_account
from gltest.assertions import tx_execution_succeeded

FUTURE_DEADLINE = "2999-01-01T00:00:00Z"
FEE_BPS = 200


def _pact_code() -> bytes:
    return Path("contracts/pact.py").read_bytes()


def test_factory_deploys_and_indexes_pact():
    """Factory deploys a Pact child on-chain and indexes it under the committer."""
    factory_builder = get_contract_factory("PactFactory")
    factory = factory_builder.deploy(args=[FEE_BPS])

    # Upload the Pact runner source the factory will deploy from.
    tx = factory.set_pact_code(args=[_pact_code()]).transact()
    assert tx_execution_succeeded(tx)
    assert factory.has_pact_code(args=[]).call() is True

    committer = get_default_account().address
    tx = factory.create_pact(
        args=[committer, "Ship the Onus MVP.", "A public repo shows a v1.0 tag.",
              FUTURE_DEADLINE],
    ).transact()
    assert tx_execution_succeeded(tx)

    assert factory.get_pact_count(args=[]).call() == 1
    pacts = factory.get_pacts_by(args=[committer]).call()
    assert len(pacts) == 1


def test_standalone_pact_fund_and_evidence():
    """A Pact can be funded and accept evidence before its deadline."""
    factory_addr = get_default_account().address  # stand-in factory address for a direct pact
    committer = get_default_account().address
    beneficiary = get_default_account().address

    pact_builder = get_contract_factory("Pact")
    pact = pact_builder.deploy(args=[
        factory_addr, committer, beneficiary,
        "Post an update every day for 30 days.",
        "A public profile page shows 30 dated posts.",
        FUTURE_DEADLINE, FEE_BPS,
    ])

    assert pact.get_status(args=[]).call() == "awaiting_funding"

    tx = pact.fund(args=[], value=10**17).transact()  # 0.1 GEN
    assert tx_execution_succeeded(tx)
    assert pact.get_status(args=[]).call() == "active"

    tx = pact.submit_evidence(args=["https://example.com/profile"]).transact()
    assert tx_execution_succeeded(tx)
    assert pact.get_evidence(args=[]).call() == ["https://example.com/profile"]


@pytest.mark.slow
def test_full_resolution_consensus():
    """End-to-end: fund, submit real evidence, wait past the deadline, resolve.

    Uses a deadline a short time in the future so fund() succeeds, then waits for
    it to elapse before resolving. Real web + LLM + finality — marked slow.
    """
    import time
    from datetime import datetime, timezone, timedelta

    deadline = (datetime.now(timezone.utc) + timedelta(seconds=20)).isoformat().replace(
        "+00:00", "Z"
    )
    committer = get_default_account().address

    pact_builder = get_contract_factory("Pact")
    pact = pact_builder.deploy(args=[
        committer, committer, committer,
        "Publish a public page that mentions GenLayer.",
        "The page at the evidence URL is reachable and clearly mentions GenLayer.",
        deadline, FEE_BPS,
    ])

    tx = pact.fund(args=[], value=10**17).transact()  # 0.1 GEN
    assert tx_execution_succeeded(tx)

    tx = pact.submit_evidence(args=["https://docs.genlayer.com/"]).transact()
    assert tx_execution_succeeded(tx)

    # Wait for the deadline to elapse, then resolve.
    time.sleep(25)
    tx = pact.resolve(args=[]).transact()
    assert tx_execution_succeeded(tx)
    assert pact.get_status(args=[]).call() == "resolved"
    assert pact.get_details(args=[]).call()["outcome"] in ("kept", "partial", "broken")
