"""Shared helpers for Onus direct-mode tests.

Direct mode runs the leader path in-process (~30ms), exercising business logic,
validation, access control, and state transitions. Cross-contract effects
(child deployment, value transfers, factory callbacks) are covered by the
integration tests, since direct mode routes those through a no-op hook.
"""

VALID_RUNNER_FEE_BPS = 200  # 2%

# A deadline safely in the future relative to the test VM's default clock.
FUTURE_DEADLINE = "2999-01-01T00:00:00Z"
# A moment strictly after FUTURE_DEADLINE, for warping past it.
AFTER_DEADLINE = "2999-06-01T00:00:00Z"


def hex_of(addr_bytes: bytes) -> str:
    """Direct-mode test addresses are raw bytes; contracts expect 0x-hex strings."""
    return "0x" + addr_bytes.hex()


def deploy_pact(direct_deploy, *, factory, committer, beneficiary,
                commitment="Ship the Onus MVP by the deadline.",
                criteria="A public GitHub repo shows a tagged v1.0 release.",
                deadline=FUTURE_DEADLINE, fee_bps=VALID_RUNNER_FEE_BPS):
    """Deploy a Pact with sensible defaults; override any field per test."""
    return direct_deploy(
        "contracts/pact.py",
        hex_of(factory),
        hex_of(committer),
        hex_of(beneficiary),
        commitment,
        criteria,
        deadline,
        fee_bps,
    )
