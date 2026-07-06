# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
"""
Onus — PactFactory intelligent contract.

The factory is the deterministic backbone of the protocol. It:
  * deploys and indexes individual `Pact` commitments on-chain,
  * holds the protocol fee configuration,
  * collects protocol fees paid by resolved pacts, and
  * maintains the reputation ledger (kept / partial / broken counts per address).

It contains no non-deterministic logic — all subjective judgment lives in the `Pact`
children. The factory only coordinates and records.
"""

from genlayer import *


ERROR_EXPECTED = "[EXPECTED]"

BPS_DENOMINATOR = 10000

OUTCOME_KEPT = "kept"
OUTCOME_PARTIAL = "partial"
OUTCOME_BROKEN = "broken"


class PactFactory(gl.Contract):
    owner: Address
    fee_bps: u256                       # protocol fee applied to newly created pacts
    pact_code: bytes                    # the Pact runner source used to deploy children

    all_pacts: DynArray[str]            # every pact address (hex), in creation order
    pacts_by_committer: TreeMap[Address, DynArray[str]]
    is_pact: TreeMap[Address, bool]     # authorization set for outcome callbacks

    kept_count: TreeMap[Address, u256]
    partial_count: TreeMap[Address, u256]
    broken_count: TreeMap[Address, u256]

    def __init__(self, fee_bps: int):
        if fee_bps < 0 or fee_bps > BPS_DENOMINATOR:
            raise gl.vm.UserError(f"{ERROR_EXPECTED} fee_bps out of range")
        self.owner = gl.message.sender_address
        self.fee_bps = u256(fee_bps)
        self.pact_code = b""

    # --------------------------------------------------------------------------------
    # Administration
    # --------------------------------------------------------------------------------
    @gl.public.write
    def set_pact_code(self, code: bytes) -> None:
        """Owner uploads the Pact runner source used to deploy future commitments."""
        self._only_owner()
        if len(code) == 0:
            raise gl.vm.UserError(f"{ERROR_EXPECTED} pact code must not be empty")
        self.pact_code = code

    @gl.public.write
    def set_fee_bps(self, fee_bps: int) -> None:
        """Owner updates the protocol fee for future pacts. Existing pacts are unaffected."""
        self._only_owner()
        if fee_bps < 0 or fee_bps > BPS_DENOMINATOR:
            raise gl.vm.UserError(f"{ERROR_EXPECTED} fee_bps out of range")
        self.fee_bps = u256(fee_bps)

    @gl.public.write
    def withdraw_fees(self, to: str) -> None:
        """Owner withdraws accumulated protocol fees held by the factory."""
        self._only_owner()
        amount = self.balance
        if amount == u256(0):
            raise gl.vm.UserError(f"{ERROR_EXPECTED} no fees to withdraw")
        _Payee(Address(to)).emit_transfer(value=amount)

    # --------------------------------------------------------------------------------
    # Pact lifecycle
    # --------------------------------------------------------------------------------
    @gl.public.write
    def create_pact(
        self,
        beneficiary: str,
        commitment_text: str,
        criteria: str,
        deadline_iso: str,
    ) -> str:
        """Deploy a new Pact for the caller and index it. Returns the pact address."""
        if len(self.pact_code) == 0:
            raise gl.vm.UserError(f"{ERROR_EXPECTED} pact code not configured yet")

        committer = gl.message.sender_address
        salt = u256(len(self.all_pacts) + 1)

        pact_address = gl.deploy_contract(
            code=self.pact_code,
            args=[
                gl.message.contract_address.as_hex,
                committer.as_hex,
                beneficiary,
                commitment_text,
                criteria,
                deadline_iso,
                int(self.fee_bps),
            ],
            salt_nonce=salt,
            on="accepted",
        )

        # gl.deploy_contract returns an Address when salt_nonce != 0; use it directly.
        addr = pact_address
        self.all_pacts.append(addr.as_hex)
        self.pacts_by_committer.get_or_insert_default(committer).append(addr.as_hex)
        self.is_pact[addr] = True
        return addr.as_hex

    @gl.public.write
    def record_outcome(self, committer: Address, outcome: str) -> None:
        """Callback used by a deployed Pact to record its verdict in the reputation ledger."""
        if not self.is_pact.get(gl.message.sender_address, False):
            raise gl.vm.UserError(f"{ERROR_EXPECTED} caller is not a registered pact")
        if outcome == OUTCOME_KEPT:
            self.kept_count[committer] = self.kept_count.get(committer, u256(0)) + u256(1)
        elif outcome == OUTCOME_PARTIAL:
            self.partial_count[committer] = self.partial_count.get(committer, u256(0)) + u256(1)
        elif outcome == OUTCOME_BROKEN:
            self.broken_count[committer] = self.broken_count.get(committer, u256(0)) + u256(1)
        else:
            raise gl.vm.UserError(f"{ERROR_EXPECTED} unknown outcome: {outcome}")

    # --------------------------------------------------------------------------------
    # Views
    # --------------------------------------------------------------------------------
    @gl.public.view
    def get_fee_bps(self) -> int:
        return int(self.fee_bps)

    @gl.public.view
    def has_pact_code(self) -> bool:
        return len(self.pact_code) > 0

    @gl.public.view
    def get_owner(self) -> str:
        return self.owner.as_hex

    @gl.public.view
    def get_pact_count(self) -> int:
        return len(self.all_pacts)

    @gl.public.view
    def get_all_pacts(self) -> list:
        return [str(a) for a in self.all_pacts]

    @gl.public.view
    def get_pacts_by(self, committer: str) -> list:
        addr = Address(committer)
        if addr not in self.pacts_by_committer:
            return []
        return [str(a) for a in self.pacts_by_committer[addr]]

    @gl.public.view
    def get_reputation(self, committer: str) -> dict:
        addr = Address(committer)
        return {
            "kept": str(self.kept_count.get(addr, u256(0))),
            "partial": str(self.partial_count.get(addr, u256(0))),
            "broken": str(self.broken_count.get(addr, u256(0))),
        }

    # --------------------------------------------------------------------------------
    # Internal
    # --------------------------------------------------------------------------------
    def _only_owner(self) -> None:
        if gl.message.sender_address != self.owner:
            raise gl.vm.UserError(f"{ERROR_EXPECTED} only the owner may call this method")


@gl.evm.contract_interface
class _Payee:
    """Minimal external interface used only to move GEN to an EOA / chain address."""

    class View:
        pass

    class Write:
        pass
