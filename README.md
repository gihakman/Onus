<div align="center">

# Onus

**A trustless referee for commitments, built on GenLayer.**

Stake money on a promise you make about yourself. A randomly selected validator jury
reads your evidence from live public sources and reaches consensus on whether the
promise was kept. The same contract holds the stake and renders the verdict, so there
is no custodian to trust and no single referee to bribe.

[Live on Testnet Bradbury](https://explorer-bradbury.genlayer.com) ·
[GenLayer](https://genlayer.com) ·
[Repository](https://github.com/gihakman/Onus)

</div>

---

## Why Onus

Commitment contracts have always been bottlenecked on the referee. A friend can be
talked out of enforcing your pledge, a platform that holds your money can freeze it or
rule in private, and a plain smart contract cannot read a repository or a profile and
judge whether a real-world promise was honored.

Onus removes the trusted party entirely. The referee is a randomly selected set of
GenLayer validators, and the vault is the same contract that renders the verdict.

## How it works

1. **Define the commitment.** A plain-language promise, a deadline, the success
   criteria, and a beneficiary who receives the stake if it is broken.
2. **Escrow the stake.** Funds are held by the contract, not by any operator.
3. **Submit evidence.** Public URLs the jury can fetch, such as a repository, a profile
   page, or a published dashboard.
4. **Resolve by consensus.** After the deadline, anyone can trigger resolution. Each
   validator independently reads the evidence, judges it against the criteria, and
   agrees on the outcome.
5. **Settle and appeal.** The contract pays out deterministically: kept returns the
   stake, broken forfeits it, partial splits it. Either side can appeal within the
   finality window.

## Live deployment

| | |
|---|---|
| Network | Testnet Bradbury |
| Chain ID | 4221 |
| Onus contract | [`0xFB5fD0ee9a7F7A93cdC2e4FE3626d2d1fc880b4B`](https://explorer-bradbury.genlayer.com/contracts/0xFB5fD0ee9a7F7A93cdC2e4FE3626d2d1fc880b4B) |
| Protocol fee | 2% (200 bps) |
| Explorer | [explorer-bradbury.genlayer.com](https://explorer-bradbury.genlayer.com) |
| Faucet | [testnet-faucet.genlayer.foundation](https://testnet-faucet.genlayer.foundation) |

This is testnet software. Stake only test GEN.

## Tech stack

- **Intelligent contract:** Python on the GenLayer GenVM. Subjective adjudication runs
  through `gl.vm.run_nondet` with a custom validator; settlement is deterministic
  atto-scale arithmetic. The runner version is pinned.
- **Consensus and evidence:** validators fetch evidence with `gl.nondet.web.render` and
  judge it with `gl.nondet.exec_prompt`, then agree on the outcome.
- **Deployment:** [genlayer-js](https://www.npmjs.com/package/genlayer-js) targeting
  Testnet Bradbury.
- **Frontend:** Next.js 14 (App Router) with TypeScript and Tailwind CSS, talking to the
  contract through genlayer-js.
- **Quality:** GenVM linter and type checker, fast in-memory direct-mode tests, and
  integration tests against a live network.

## Architecture

Onus is a single intelligent contract. It stores every commitment as a record addressed
by a numeric id, escrows each stake, holds the protocol fee configuration, and keeps a
reputation ledger of kept, partial, and broken counts per address. Subjective judgment
runs only at the point where a pact is resolved. Keeping everything in one contract makes
each pact immediately readable and keeps every action to a single transaction.

```
contracts/
  onus.py             The Onus contract: records, escrow, adjudication, settlement
tests/
  direct/             Fast in-memory tests (pytest, genlayer-test)
  integration/        Full consensus tests against a live network (gltest)
deploy/
  deployScript.ts     genlayer-js deployment to Testnet Bradbury
web/                  Next.js frontend and dApp
gltest.config.yaml    Test network configuration
```

## Develop

Contract, linting, and tests (Python):

```bash
python -m venv .venv && . .venv/bin/activate
pip install genvm-linter "genlayer-test[sim]"
genvm-lint check contracts/onus.py
pytest tests/direct/ -q
```

Deploy to Bradbury (Node):

```bash
npm install
cp .env.example .env      # set ACCOUNT_PRIVATE_KEY to a funded Bradbury key
npm run deploy:bradbury
```

The deploy script publishes the contract and writes its address to
`deploy/deployments.bradbury.json`.

Frontend:

```bash
cd web
npm install
cp .env.local.example .env.local   # set NEXT_PUBLIC_ONUS_ADDRESS to the deployed contract
npm run dev
```

## Deploy the frontend to Vercel

The web app lives in `web/`. Import the repository in Vercel and set:

- **Root Directory:** `web`
- **Environment variables:**
  - `NEXT_PUBLIC_ONUS_ADDRESS` = `0xFB5fD0ee9a7F7A93cdC2e4FE3626d2d1fc880b4B`
  - `NEXT_PUBLIC_ONUS_FEE_BPS` = `200`

## Security

The stake is held by the contract, never by an operator. Payouts happen only through the
resolve path, in proportion to the verdict. Consensus requires validators to agree on the
qualitative outcome, and contested results can be escalated through the protocol finality
window. Wallet keys stay in a local `.env` that is never committed.

## License

MIT
