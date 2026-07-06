# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
"""
Onus — Pact intelligent contract.

A single self-directed commitment. The committer escrows a stake in GEN against a
plain-language promise with a deadline and an evidence rule. After the deadline anyone
may call `resolve()`; a randomly selected validator jury reads the live evidence itself
and reaches consensus on whether the promise was kept. The contract then settles the
stake deterministically — no custodian, no nameable referee.

The contract is both the vault and the referee.
"""

from genlayer import *

from datetime import datetime, timezone
import json


# --- Error classification prefixes (for validator error comparison) ------------------
ERROR_EXPECTED = "[EXPECTED]"   # deterministic business-logic error — exact match
ERROR_EXTERNAL = "[EXTERNAL]"   # external 4xx — deterministic, exact match
ERROR_TRANSIENT = "[TRANSIENT]"  # network / 5xx — agree if both transient
ERROR_LLM = "[LLM_ERROR]"       # LLM misbehavior — always disagree, force rotation


# --- Lifecycle + verdict vocabulary (stored as plain strings) ------------------------
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
# Validator tolerance for the partial-credit split, in basis points.
PARTIAL_BPS_TOLERANCE = 1500


@gl.evm.contract_interface
class _Payee:
    """Minimal external interface used only to move GEN to an EOA / chain address."""

    class View:
        pass

    class Write:
        pass


def _parse_iso_to_unix(iso: str) -> int:
    """Parse an ISO 8601 string to Unix seconds. Raises a classified error if invalid."""
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
    """Transaction time in Unix seconds — deterministic and identical across validators."""
    return int(datetime.now(timezone.utc).timestamp())


def _clean_json_object(text: str) -> dict:
    """Extract the first JSON object from possibly-noisy LLM text."""
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
    """Coerce an LLM verdict into a stable, validated shape: outcome + partial_bps."""
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
        if partial_bps <= 0 or partial_bps >= BPS_DENOMINATOR:
            # A partial verdict at the extremes is really kept/broken; clamp inward.
            partial_bps = max(1, min(BPS_DENOMINATOR - 1, partial_bps))

    rationale = str(raw.get("rationale", raw.get("reasoning", ""))).strip()
    return {"outcome": outcome, "partial_bps": partial_bps, "rationale": rationale[:1000]}


def _build_prompt(commitment: str, criteria: str, gathered: list) -> str:
    """Assemble the neutral referee prompt from stored terms and fetched evidence."""
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


class Pact(gl.Contract):
    # --- Parties & terms (immutable after creation) ---
    factory: Address
    committer: Address
    beneficiary: Address          # receives forfeited stake when the promise is broken
    commitment_text: str
    criteria: str
    deadline_iso: str
    deadline_ts: u256
    created_at: str
    fee_bps: u256                 # protocol fee on the stake, in basis points

    # --- Escrow & lifecycle (mutable) ---
    stake: u256                   # atto-scale GEN escrowed
    status: str
    evidence: DynArray[str]

    # --- Verdict (set once at resolution) ---
    outcome: str
    partial_bps: u256
    rationale: str
    resolved_at: str

    def __init__(
        self,
        factory: str,
        committer: str,
        beneficiary: str,
        commitment_text: str,
        criteria: str,
        deadline_iso: str,
        fee_bps: int,
    ):
        if not commitment_text.strip():
            raise gl.vm.UserError(f"{ERROR_EXPECTED} commitment_text must not be empty")
        if not criteria.strip():
            raise gl.vm.UserError(f"{ERROR_EXPECTED} criteria must not be empty")
        if fee_bps < 0 or fee_bps > BPS_DENOMINATOR:
            raise gl.vm.UserError(f"{ERROR_EXPECTED} fee_bps out of range")

        self.deadline_ts = u256(_parse_iso_to_unix(deadline_iso))

        self.factory = Address(factory)
        self.committer = Address(committer)
        self.beneficiary = Address(beneficiary)
        self.commitment_text = commitment_text
        self.criteria = criteria
        self.deadline_iso = deadline_iso
        self.created_at = gl.message_raw["datetime"]
        self.fee_bps = u256(fee_bps)

        self.stake = u256(0)
        self.status = STATUS_AWAITING_FUNDING
        self.outcome = OUTCOME_UNRESOLVED
        self.partial_bps = u256(0)
        self.rationale = ""
        self.resolved_at = ""

    # --------------------------------------------------------------------------------
    # Escrow
    # --------------------------------------------------------------------------------
    @gl.public.write.payable
    def fund(self) -> None:
        """Committer escrows the stake. Callable once, before the deadline."""
        if gl.message.sender_address != self.committer:
            raise gl.vm.UserError(f"{ERROR_EXPECTED} only the committer can fund this pact")
        if self.status != STATUS_AWAITING_FUNDING:
            raise gl.vm.UserError(f"{ERROR_EXPECTED} pact is not awaiting funding")
        if gl.message.value == u256(0):
            raise gl.vm.UserError(f"{ERROR_EXPECTED} stake must be greater than zero")
        if _now_unix() >= int(self.deadline_ts):
            raise gl.vm.UserError(f"{ERROR_EXPECTED} deadline has already passed")

        self.stake = gl.message.value
        self.status = STATUS_ACTIVE

    @gl.public.write
    def submit_evidence(self, url: str) -> None:
        """Committer appends a public evidence URL. Allowed while active, before deadline."""
        if gl.message.sender_address != self.committer:
            raise gl.vm.UserError(f"{ERROR_EXPECTED} only the committer can submit evidence")
        if self.status != STATUS_ACTIVE:
            raise gl.vm.UserError(f"{ERROR_EXPECTED} pact is not active")
        if _now_unix() >= int(self.deadline_ts):
            raise gl.vm.UserError(f"{ERROR_EXPECTED} deadline has passed; evidence is locked")
        if len(self.evidence) >= MAX_EVIDENCE_ITEMS:
            raise gl.vm.UserError(f"{ERROR_EXPECTED} evidence limit reached")
        cleaned = url.strip()
        if not cleaned:
            raise gl.vm.UserError(f"{ERROR_EXPECTED} evidence url must not be empty")
        self.evidence.append(cleaned)

    # --------------------------------------------------------------------------------
    # Resolution
    # --------------------------------------------------------------------------------
    @gl.public.write
    def resolve(self) -> None:
        """After the deadline, anyone triggers adjudication and deterministic settlement."""
        if self.status != STATUS_ACTIVE:
            raise gl.vm.UserError(f"{ERROR_EXPECTED} pact is not active")
        if _now_unix() < int(self.deadline_ts):
            raise gl.vm.UserError(f"{ERROR_EXPECTED} deadline has not passed yet")

        verdict = self._adjudicate()

        self.outcome = verdict["outcome"]
        self.partial_bps = u256(int(verdict["partial_bps"]))
        self.rationale = verdict["rationale"]
        self.resolved_at = gl.message_raw["datetime"]
        self.status = STATUS_RESOLVED

        self._settle()
        self._report_to_factory()

    def _adjudicate(self) -> dict:
        """Validator jury reads the live evidence and agrees on a structured verdict."""
        commitment = self.commitment_text
        criteria = self.criteria
        urls = [str(u) for u in self.evidence]

        def leader_fn() -> dict:
            gathered = []
            for url in urls:
                try:
                    page = gl.nondet.web.render(url, mode="text")
                    content = str(page)[:MAX_CONTENT_CHARS]
                except Exception:
                    # A source that will not load is simply absent evidence, not a failure.
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
            # Consensus requires agreement on the qualitative outcome.
            if str(leader.get("outcome")) != own["outcome"]:
                return False
            # For partial outcomes, the split must be close (non-comparative tolerance).
            if own["outcome"] == OUTCOME_PARTIAL:
                try:
                    leader_bps = int(leader.get("partial_bps"))
                except (ValueError, TypeError):
                    return False
                if abs(leader_bps - own["partial_bps"]) > PARTIAL_BPS_TOLERANCE:
                    return False
            return True

        return gl.vm.run_nondet(leader_fn, validator_fn)

    def _settle(self) -> None:
        """Deterministically move the escrowed stake according to the agreed verdict."""
        stake = int(self.stake)
        fee = stake * int(self.fee_bps) // BPS_DENOMINATOR
        net = stake - fee

        if self.outcome == OUTCOME_KEPT:
            to_committer = net
            to_beneficiary = 0
        elif self.outcome == OUTCOME_BROKEN:
            to_committer = 0
            to_beneficiary = net
        else:  # partial
            to_committer = net * int(self.partial_bps) // BPS_DENOMINATOR
            to_beneficiary = net - to_committer

        if fee > 0:
            gl.get_contract_at(self.factory).emit_transfer(value=u256(fee), on="finalized")
        if to_committer > 0:
            _Payee(self.committer).emit_transfer(value=u256(to_committer))
        if to_beneficiary > 0:
            _Payee(self.beneficiary).emit_transfer(value=u256(to_beneficiary))

    def _report_to_factory(self) -> None:
        """Record the outcome in the factory's reputation ledger (best-effort, async)."""
        gl.get_contract_at(self.factory).emit(on="finalized").record_outcome(
            self.committer, self.outcome
        )

    # --------------------------------------------------------------------------------
    # Views
    # --------------------------------------------------------------------------------
    @gl.public.view
    def get_details(self) -> dict:
        return {
            "factory": self.factory.as_hex,
            "committer": self.committer.as_hex,
            "beneficiary": self.beneficiary.as_hex,
            "commitment_text": self.commitment_text,
            "criteria": self.criteria,
            "deadline_iso": self.deadline_iso,
            "deadline_ts": str(self.deadline_ts),
            "created_at": self.created_at,
            "fee_bps": str(self.fee_bps),
            "stake": str(self.stake),
            "status": self.status,
            "evidence": [str(u) for u in self.evidence],
            "outcome": self.outcome,
            "partial_bps": str(self.partial_bps),
            "rationale": self.rationale,
            "resolved_at": self.resolved_at,
        }

    @gl.public.view
    def get_status(self) -> str:
        return self.status

    @gl.public.view
    def get_evidence(self) -> list:
        return [str(u) for u in self.evidence]

    @gl.public.view
    def is_resolvable(self) -> bool:
        return self.status == STATUS_ACTIVE and _now_unix() >= int(self.deadline_ts)
