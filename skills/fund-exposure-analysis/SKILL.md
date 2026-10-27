---
name: fund-exposure-analysis
description: Compare current ETF or mutual-fund holdings and concentration using FMP data, with explicit unmatched, cash and derivative coverage.
---

# fund exposure analysis

Use FMP etfAndMutualFunds holdings for both symbols and optional sector/country weights. Preserve updatedAt and any actual effective date separately. Pass fund_a/fund_b arrays to the helper. Report unnormalised identified-positive-holdings overlap, comparable coverage and excluded gross weights. Inspect excluded rows; do not treat cash, options, futures, negative holdings or nested funds as simple stock economic exposure. Do not claim historical exposure from a current snapshot.

Use the user's existing entitled FMP connector; connector names vary by platform. Alternatively use the read-only stable API fetch helper with the user's own FMP_API_KEY stored outside files. A manually exported snapshot is supported but must be labelled snapshot-based, not an automatic live integration.

Save an input JSON with source provenance. Run the bundled helper from this skill folder:

    python -B scripts/run.py --input input.json --output report-v1.md

Read the Markdown AND companion JSON, then write the requested research report with dated citations and interpretation limits. Do not fabricate missing values, imply a tested platform that was not run, or treat an API success as independent source verification. Do not place API keys, restricted raw data or private audit material in Git. Existing outputs are preserved; choose a new version for changes.

The installed bundle is self-contained, with a no-key synthetic examples/input.json. Inputs fund_a/fund_b contain original FMP holdings; optional effective_date_a/effective_date_b must be actual holding dates, not updatedAt. Claude group etfAndMutualFunds and OpenAI Codex CLI group etfandmutualfunds expose holdings. Keep provenance and original weights. Cross-match US/Canadian ISINs and CUSIPs consistently; conflicting identifiers stop. Symbol fallback requires exchange and currency. Keep share classes distinct unless the user explicitly requests and supplies reliable issuer aggregation. Expose unmatched records, missing weights, gross and net exclusions and coverage. Cash, negative positions, derivatives and nested funds do not receive invented equity look-through. Optional allocation_pct has fund_a/fund_b percentage points summing to at most100; combined exposure covers identified direct securities only. Show largest overlap contributions and concentration without renormalising dropped exposure. Unknown/mismatched effective dates limit interpretation. Check selected issuer holdings with their actual dates; do not equate different-date weights. Direct REST is etf/holdings. Python3.11+; own entitled connector/account. Educational research only, no investment advice or trading actions.


## Install and inputs
Unzip the complete skill folder into a chosen project's `.claude/skills/` for Claude Code or `.agents/skills/` for the local OpenAI agent runtime. Keep scripts/examples/references together. Start a fresh session in that project and explicitly invoke this skill. Requires Python3.11+ available to the host's local shell and your own entitled FMP connection for live research; the offline example needs no account. In the host's Apps/Connectors settings find Financial Modeling Prep/FMP, connect your own account, complete its sign-in/consent flow, and confirm an endpoint read before starting research. Claude Code may use the synced claude.ai FMP connector. Tool names differ by host. Do not paste keys into prompts/files. This bundle does not install a server, provide account entitlements or certify browser/mobile execution. AI/FMP subscription charges and limits remain with your accounts.
Read [the input contract](references/input-contract.md) before building input JSON. Run the main example and `examples/failure.json` (expected exit2, no report). Then use the user's research question and connected tools to assemble the input yourself, keeping retrieval and source checks explicit. Unknown coverage stays unknown; a prewritten coverage flag is not a source check.
