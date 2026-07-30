"""Shared helpers for Onus direct-mode tests.

Direct mode runs the leader path in-process (~30ms), exercising business logic,
validation, access control, and state transitions. Cross-contract effects (the
settlement value transfers) are covered by the integration tests, since direct mode
routes external messages through a no-op hook.
"""

import pytest

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


@pytest.fixture(autouse=True)
def _sync_message_datetime_on_warp(direct_vm):
    """Make ``warp()`` update ``gl.message_raw["datetime"]`` as the real runtime does.

    On the GenLayer network each transaction carries its own timestamp in
    ``gl.message_raw["datetime"]``; the contract reads that (not host wall-clock
    ``datetime.now()``) for all deadline checks. The direct test VM freezes
    ``message_raw["datetime"]`` at deploy time and only patches ``datetime.now()``
    to track ``warp()`` — so without this fixture, a contract that reads the runtime
    timestamp would ignore ``warp()`` and see the deploy-time clock.

    This wraps ``warp`` so the runtime timestamp is kept in step with the warped
    clock, mirroring real per-transaction datetime behavior and letting existing
    ``warp(AFTER_DEADLINE)`` tests exercise the deadline logic unchanged.
    """
    original_warp = direct_vm.warp

    def _warp_synced(timestamp: str) -> None:
        original_warp(timestamp)
        import sys as _sys
        gl = _sys.modules.get("genlayer.gl")
        if gl is not None and getattr(gl, "message_raw", None) is not None:
            gl.message_raw["datetime"] = timestamp

    direct_vm.warp = _warp_synced
    yield
    direct_vm.warp = original_warp
