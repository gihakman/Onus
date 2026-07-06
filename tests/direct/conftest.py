"""Shared helpers for Onus direct-mode tests.

Direct mode runs the leader path in-process (~30ms), exercising business logic,
validation, access control, and state transitions. Cross-contract effects (the
settlement value transfers) are covered by the integration tests, since direct mode
routes external messages through a no-op hook.
"""

FEE_BPS = 200

# A deadline safely in the future relative to the test VM's default clock.
FUTURE_DEADLINE = "2999-01-01T00:00:00Z"
# A moment strictly after FUTURE_DEADLINE, for warping past it.
AFTER_DEADLINE = "2999-06-01T00:00:00Z"

ONE_GEN = 10**18


def hex_of(addr_bytes: bytes) -> str:
    """Direct-mode test addresses are raw bytes; contracts expect 0x-hex strings."""
    return "0x" + addr_bytes.hex()


def deploy_onus(direct_deploy, fee_bps=FEE_BPS):
    return direct_deploy("contracts/onus.py", fee_bps)


def create_pact(
    onus,
    *,
    beneficiary,
    commitment="Ship the Onus MVP by the deadline.",
    criteria="A public GitHub repo shows a tagged v1.0 release.",
    deadline=FUTURE_DEADLINE,
):
    """Create a pact and return its id."""
    return onus.create_pact(hex_of(beneficiary), commitment, criteria, deadline)
