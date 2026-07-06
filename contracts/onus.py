# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
"""
Onus — a trustless commitment escrow and AI-referee protocol on GenLayer.

A single contract holds every commitment ("pact") as a record and escrows its stake.
A committer stakes GEN against a self-directed promise with a deadline and an evidence
rule. After the deadline anyone may resolve it; a randomly selected validator jury reads
the live evidence and reaches consensus on whether the promise was kept, and the contract
settles the stake deterministically. The contract is both the vault and the referee.
"""

from genlayer import *

from dataclasses import dataclass
from datetime import datetime, timezone
import json


# --- Error classification prefixes (for validator error comparison) ------------------
ERROR_EXPECTED = "[EXPECTED]"
ERROR_EXTERNAL = "[EXTERNAL]"
ERROR_TRANSIENT = "[TRANSIENT]"
ERROR_LLM = "[LLM_ERROR]"

# --- Lifecycle + verdict vocabulary --------------------------------------------------
STATUS_AWAITING_FUNDING = "awaiting_funding"
STATUS_ACTIVE = "active"
STATUS_RESOLVED = "resolved"

OUTCOME_UNRESOLVED = "unresolved"
OUTCOME_KEPT = "kept"
OUTCOME_PARTIAL = "partial"
OUTCOME_BROKEN = "broken"

BPS_DENOMINATOR = 10000
MAX_EVIDENCE_ITEMS = 20
MAX_CONTENT_CHARS = 4000
PARTIAL_BPS_TOLERANCE = 1500


@gl.evm.contract_interface
class _Payee:
    """Minimal external interface used only to move GEN to an EOA / chain address."""

    class View:
        pass

    class Write:
        pass


@allow_storage
@dataclass
class Pact:
    committer: Address
    beneficiary: Address
    commitment_text: str
    criteria: str
    deadline_iso: str
    deadline_ts: u256
    created_at: str
    fee_bps: u256
    stake: u256
    status: str
    outcome: str
    partial_bps: u256
    rationale: str
    resolved_at: str


def _parse_iso_to_unix(iso: str) -> int:
    text = iso.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(text)
    except (ValueError, TypeError):
        raise gl.vm.UserError(f"{ERROR_EXPECTED} deadline is not a valid ISO 8601 datetime")
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp())


def _now_unix() -> int:
    return int(datetime.now(timezone.utc).timestamp())


def _clean_json_object(text: str) -> dict:
    first = text.find("{")
    last = text.rfind("}")
    if first == -1 or last == -1 or last < first:
        raise gl.vm.UserError(f"{ERROR_LLM} model response contained no JSON object")
    try:
        parsed = json.loads(text[first : last + 1])
    except (ValueError, TypeError):
        raise gl.vm.UserError(f"{ERROR_LLM} model response was not valid JSON")
    if not isinstance(parsed, dict):
        raise gl.vm.UserError(f"{ERROR_LLM} model response was not a JSON object")
    return parsed


def _normalize_verdict(raw: dict) -> dict:
    outcome = str(raw.get("outcome", "")).strip().lower()
    if outcome not in (OUTCOME_KEPT, OUTCOME_PARTIAL, OUTCOME_BROKEN):
        raise gl.vm.UserError(
            f"{ERROR_LLM} outcome must be kept|partial|broken, got: {outcome!r}"
        )
    partial_bps = 0
    if outcome == OUTCOME_KEPT:
        partial_bps = BPS_DENOMINATOR
    elif outcome == OUTCOME_BROKEN:
        partial_bps = 0
    else:
        raw_bps = raw.get("partial_bps", raw.get("percent_kept_bps"))
        try:
            partial_bps = int(round(float(str(raw_bps).strip())))
        except (ValueError, TypeError):
            raise gl.vm.UserError(f"{ERROR_LLM} partial verdict missing numeric partial_bps")
        partial_bps = max(1, min(BPS_DENOMINATOR - 1, partial_bps))
    rationale = str(raw.get("rationale", raw.get("reasoning", ""))).strip()
    return {"outcome": outcome, "partial_bps": partial_bps, "rationale": rationale[:1000]}


def _build_prompt(commitment: str, criteria: str, gathered: list) -> str:
    evidence_block = "\n\n".join(
        f"SOURCE {i + 1}: {item['url']}\n{item['content']}" for i, item in enumerate(gathered)
    ) or "NO EVIDENCE WAS RETRIEVABLE FROM THE PROVIDED SOURCES."
    return (
        "You are a neutral, impartial referee deciding whether a person kept a "
        "commitment they staked money on. Judge ONLY against the stated success "
        "criteria, using ONLY the evidence retrieved below from the committer's own "
        "declared sources. Do not assume facts that are not supported by the evidence. "
        "User-submitted claims that are not corroborated by the retrieved sources are "
        "weak evidence and must not, on their own, prove the commitment was kept.\n\n"
        f"COMMITMENT:\n{commitment}\n\n"
        f"SUCCESS CRITERIA:\n{criteria}\n\n"
        f"RETRIEVED EVIDENCE:\n{evidence_block}\n\n"
        "Decide the outcome:\n"
        '- "kept": the criteria are clearly and fully satisfied by the evidence.\n'
        '- "broken": the criteria are clearly not satisfied.\n'
        '- "partial": the criteria are only partly satisfied; set partial_bps to the '
        "fraction honored, in basis points (1..9999, where 10000 = fully kept).\n\n"
        "Respond with a single JSON object and nothing else:\n"
        '{"outcome": "kept|partial|broken", "partial_bps": <int 0-10000>, '
        '"rationale": "<one concise paragraph citing the evidence>"}'
    )


class Onus(gl.Contract):
    owner: Address
    fee_bps: u256
    pacts: DynArray[Pact]
    evidence: TreeMap[u256, DynArray[str]]
    pacts_by_committer: TreeMap[Address, DynArray[u256]]
    kept_count: TreeMap[Address, u256]
    partial_count: TreeMap[Address, u256]
    broken_count: TreeMap[Address, u256]

    def __init__(self, fee_bps: int):
        if fee_bps < 0 or fee_bps > BPS_DENOMINATOR:
            raise gl.vm.UserError(f"{ERROR_EXPECTED} fee_bps out of range")
        self.owner = gl.message.sender_address
        self.fee_bps = u256(fee_bps)

    # --------------------------------------------------------------------------------
    # Create & fund
    # --------------------------------------------------------------------------------
    @gl.public.write
    def create_pact(
        self,
        beneficiary: str,
        commitment_text: str,
        criteria: str,
        deadline_iso: str,
    ) -> int:
        """Register a new commitment for the caller. Returns its pact id."""
        if not commitment_text.strip():
            raise gl.vm.UserError(f"{ERROR_EXPECTED} commitment_text must not be empty")
        if not criteria.strip():
            raise gl.vm.UserError(f"{ERROR_EXPECTED} criteria must not be empty")
        deadline_ts = _parse_iso_to_unix(deadline_iso)

        committer = gl.message.sender_address
        self.pacts.append(
            Pact(
                committer=committer,
                beneficiary=Address(beneficiary),
                commitment_text=commitment_text,
                criteria=criteria,
                deadline_iso=deadline_iso,
                deadline_ts=u256(deadline_ts),
                created_at=gl.message_raw["datetime"],
                fee_bps=self.fee_bps,
                stake=u256(0),
                status=STATUS_AWAITING_FUNDING,
                outcome=OUTCOME_UNRESOLVED,
                partial_bps=u256(0),
                rationale="",
                resolved_at="",
            )
        )
        pact_id = len(self.pacts) - 1
        self.pacts_by_committer.get_or_insert_default(committer).append(u256(pact_id))
        return pact_id

    @gl.public.write.payable
    def fund(self, pact_id: int) -> None:
        """Committer escrows the stake for a pact. Callable once, before the deadline."""
        p = self._pact(pact_id)
        if gl.message.sender_address != p.committer:
            raise gl.vm.UserError(f"{ERROR_EXPECTED} only the committer can fund this pact")
        if p.status != STATUS_AWAITING_FUNDING:
            raise gl.vm.UserError(f"{ERROR_EXPECTED} pact is not awaiting funding")
        if gl.message.value == u256(0):
            raise gl.vm.UserError(f"{ERROR_EXPECTED} stake must be greater than zero")
        if _now_unix() >= int(p.deadline_ts):
            raise gl.vm.UserError(f"{ERROR_EXPECTED} deadline has already passed")
        p.stake = gl.message.value
        p.status = STATUS_ACTIVE

    @gl.public.write
    def submit_evidence(self, pact_id: int, url: str) -> None:
        """Committer appends a public evidence URL while the pact is active."""
        p = self._pact(pact_id)
        if gl.message.sender_address != p.committer:
            raise gl.vm.UserError(f"{ERROR_EXPECTED} only the committer can submit evidence")
        if p.status != STATUS_ACTIVE:
            raise gl.vm.UserError(f"{ERROR_EXPECTED} pact is not active")
        if _now_unix() >= int(p.deadline_ts):
            raise gl.vm.UserError(f"{ERROR_EXPECTED} deadline has passed; evidence is locked")
        bucket = self.evidence.get_or_insert_default(u256(pact_id))
        if len(bucket) >= MAX_EVIDENCE_ITEMS:
            raise gl.vm.UserError(f"{ERROR_EXPECTED} evidence limit reached")
        cleaned = url.strip()
        if not cleaned:
            raise gl.vm.UserError(f"{ERROR_EXPECTED} evidence url must not be empty")
        bucket.append(cleaned)

    # --------------------------------------------------------------------------------
    # Resolve & settle
    # --------------------------------------------------------------------------------
    @gl.public.write
    def resolve(self, pact_id: int) -> None:
        """After the deadline, anyone triggers adjudication and deterministic settlement."""
        p = self._pact(pact_id)
        if p.status != STATUS_ACTIVE:
            raise gl.vm.UserError(f"{ERROR_EXPECTED} pact is not active")
        if _now_unix() < int(p.deadline_ts):
            raise gl.vm.UserError(f"{ERROR_EXPECTED} deadline has not passed yet")

        verdict = self._adjudicate(pact_id)
        p.outcome = verdict["outcome"]
        p.partial_bps = u256(int(verdict["partial_bps"]))
        p.rationale = verdict["rationale"]
        p.resolved_at = gl.message_raw["datetime"]
        p.status = STATUS_RESOLVED

        self._settle(pact_id)
        self._record_outcome(p.committer, p.outcome)

    def _adjudicate(self, pact_id: int) -> dict:
        p = self.pacts[pact_id]
        commitment = p.commitment_text
        criteria = p.criteria
        urls = [str(u) for u in self.evidence[u256(pact_id)]] if u256(pact_id) in self.evidence else []

        def leader_fn() -> dict:
            gathered = []
            for url in urls:
                try:
                    page = gl.nondet.web.render(url, mode="text")
                    content = str(page)[:MAX_CONTENT_CHARS]
                except Exception:
                    content = ""
                gathered.append({"url": url, "content": content})
            raw = gl.nondet.exec_prompt(_build_prompt(commitment, criteria, gathered),
                                        response_format="json")
            if isinstance(raw, dict):
                return _normalize_verdict(raw)
            return _normalize_verdict(_clean_json_object(str(raw)))

        def validator_fn(leader_res: gl.vm.Result) -> bool:
            if not isinstance(leader_res, gl.vm.Return):
                return False
            own = leader_fn()
            leader = leader_res.calldata
            if not isinstance(leader, dict):
                return False
            if str(leader.get("outcome")) != own["outcome"]:
                return False
            if own["outcome"] == OUTCOME_PARTIAL:
                try:
                    leader_bps = int(leader.get("partial_bps"))
                except (ValueError, TypeError):
                    return False
                if abs(leader_bps - own["partial_bps"]) > PARTIAL_BPS_TOLERANCE:
                    return False
            return True

        return gl.vm.run_nondet(leader_fn, validator_fn)

    def _settle(self, pact_id: int) -> None:
        p = self.pacts[pact_id]
        stake = int(p.stake)
        fee = stake * int(p.fee_bps) // BPS_DENOMINATOR
        net = stake - fee
        if p.outcome == OUTCOME_KEPT:
            to_committer, to_beneficiary = net, 0
        elif p.outcome == OUTCOME_BROKEN:
            to_committer, to_beneficiary = 0, net
        else:
            to_committer = net * int(p.partial_bps) // BPS_DENOMINATOR
            to_beneficiary = net - to_committer
        # The protocol fee simply remains in this contract for the owner to withdraw.
        if to_committer > 0:
            _Payee(p.committer).emit_transfer(value=u256(to_committer))
        if to_beneficiary > 0:
            _Payee(p.beneficiary).emit_transfer(value=u256(to_beneficiary))

    def _record_outcome(self, committer: Address, outcome: str) -> None:
        if outcome == OUTCOME_KEPT:
            self.kept_count[committer] = self.kept_count.get(committer, u256(0)) + u256(1)
        elif outcome == OUTCOME_PARTIAL:
            self.partial_count[committer] = self.partial_count.get(committer, u256(0)) + u256(1)
        elif outcome == OUTCOME_BROKEN:
            self.broken_count[committer] = self.broken_count.get(committer, u256(0)) + u256(1)

    # --------------------------------------------------------------------------------
    # Administration
    # --------------------------------------------------------------------------------
    @gl.public.write
    def set_fee_bps(self, fee_bps: int) -> None:
        self._only_owner()
        if fee_bps < 0 or fee_bps > BPS_DENOMINATOR:
            raise gl.vm.UserError(f"{ERROR_EXPECTED} fee_bps out of range")
        self.fee_bps = u256(fee_bps)

    @gl.public.write
    def withdraw_fees(self, to: str) -> None:
        self._only_owner()
        amount = self.balance
        if amount == u256(0):
            raise gl.vm.UserError(f"{ERROR_EXPECTED} no fees to withdraw")
        _Payee(Address(to)).emit_transfer(value=amount)

    # --------------------------------------------------------------------------------
    # Views
    # --------------------------------------------------------------------------------
    @gl.public.view
    def get_pact(self, pact_id: int) -> dict:
        p = self._pact(pact_id)
        ev = [str(u) for u in self.evidence[u256(pact_id)]] if u256(pact_id) in self.evidence else []
        return {
            "id": str(pact_id),
            "committer": p.committer.as_hex,
            "beneficiary": p.beneficiary.as_hex,
            "commitment_text": p.commitment_text,
            "criteria": p.criteria,
            "deadline_iso": p.deadline_iso,
            "deadline_ts": str(p.deadline_ts),
            "created_at": p.created_at,
            "fee_bps": str(p.fee_bps),
            "stake": str(p.stake),
            "status": p.status,
            "evidence": ev,
            "outcome": p.outcome,
            "partial_bps": str(p.partial_bps),
            "rationale": p.rationale,
            "resolved_at": p.resolved_at,
        }

    @gl.public.view
    def get_pact_count(self) -> int:
        return len(self.pacts)

    @gl.public.view
    def get_all_pact_ids(self) -> list:
        return [i for i in range(len(self.pacts))]

    @gl.public.view
    def get_pacts_by(self, committer: str) -> list:
        addr = Address(committer)
        if addr not in self.pacts_by_committer:
            return []
        return [int(i) for i in self.pacts_by_committer[addr]]

    @gl.public.view
    def get_reputation(self, committer: str) -> dict:
        addr = Address(committer)
        return {
            "kept": str(self.kept_count.get(addr, u256(0))),
            "partial": str(self.partial_count.get(addr, u256(0))),
            "broken": str(self.broken_count.get(addr, u256(0))),
        }

    @gl.public.view
    def get_fee_bps(self) -> int:
        return int(self.fee_bps)

    @gl.public.view
    def get_owner(self) -> str:
        return self.owner.as_hex

    # --------------------------------------------------------------------------------
    # Internal
    # --------------------------------------------------------------------------------
    def _pact(self, pact_id: int) -> Pact:
        if pact_id < 0 or pact_id >= len(self.pacts):
            raise gl.vm.UserError(f"{ERROR_EXPECTED} unknown pact id")
        return self.pacts[pact_id]

    def _only_owner(self) -> None:
        if gl.message.sender_address != self.owner:
            raise gl.vm.UserError(f"{ERROR_EXPECTED} only the owner may call this method")
