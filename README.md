# William Shares FMP Research Skills

Four reusable workflows for researching stocks and funds with Financial Modeling Prep data and an AI assistant.

| Skill | Result |
|---|---|
| [Institutional ownership research](skills/institutional-ownership-research/SKILL.md) | Compare disclosed 13F positions, share changes, reported values and filing evidence |
| [Earnings-call comparison](skills/earnings-call-comparison/SKILL.md) | Locate before/after passages and write a cited comparison of outlook, drivers and risks |
| [Fund exposure analysis](skills/fund-exposure-analysis/SKILL.md) | Calculate identified-holdings overlap, exclusions, concentration and allocation exposure |
| [Company research brief](skills/company-research-brief/SKILL.md) | Combine compatible financials, earnings, ownership, fund exposure and forecast horizons |

## Requirements and tested hosts

- Python 3.11 or later; tested with Python 3.13.14 on Windows.
- Claude Code 2.1.299 or OpenAI Codex CLI 0.164.0 for the observed model-driven workflows.
- Your own entitled FMP connection for live research. Offline synthetic examples need no account or API key.

The tested routes are local CLI hosts. Classic ChatGPT web/mobile, the ChatGPT desktop UI and Claude's browser/desktop Skills-upload UI have not been tested. Account plans, endpoint access, usage limits and charges depend on your accounts. No server or shared API key is supplied. Successful calls do not identify an account's billing tier.

## Install and try an example

Download this repository or a release ZIP. Copy a complete `skills/<name>` folder into your project's `.claude/skills/` for Claude Code or `.agents/skills/` for Codex. Every folder is self-contained: instructions, input contract, Python scripts, licence and invented examples. Start a fresh session in that project and explicitly invoke the chosen skill. The observed Codex route asks the agent to read `.agents/skills/<name>/SKILL.md` and follow it for the research question.

From the installed skill folder:

```sh
python -B scripts/run.py --input examples/input.json --output demo-v1.md
```

For live research, keep input snapshots and reports in a private, Git-ignored project folder outside the installed skill directories, and pass their paths to `--input` and `--output`.

Read the Markdown and companion JSON. The assistant then explains the evidence, counterevidence and gaps. `examples/failure.json` intentionally fails with exit code 2 and writes no report. Existing output filenames are preserved; choose a new name for later runs.

## Connect FMP

In your host's Apps, Plugins or Connectors settings, find Financial Modeling Prep, connect your own account and complete its sign-in/consent flow. Start a fresh session and verify a read-only endpoint before research. Claude Code may use its synced claude.ai connector; Codex uses its available FMP app. Tool names differ by host, so follow the exposed schema.

Ask a concrete question such as: "Use institutional-ownership-research to compare this manager's disclosed holdings for these two quarters, then explain the evidence and limitations." Read the bundled input contract before constructing an input. Retain actual retrieval, reporting and filing dates; unknown coverage stays unknown.

[FMP MCP setup](https://site.financialmodelingprep.com/developer/docs/mcp-server) · [Claude connectors](https://support.claude.com/en/articles/11176164-use-connectors-to-extend-claude-s-capabilities) · [OpenAI skills](https://learn.chatgpt.com/docs/build-skills) · [OpenAI plugins](https://learn.chatgpt.com/docs/plugins)

Keep credentials in your host/provider account. Optional direct API mode reads your own `FMP_API_KEY` environment variable; it has not had a successful-key test here. Never put credentials into input JSON, prompts, command parameters or Git.

## Build and test

```sh
python -B -m unittest discover -s tests
python -B scripts/build_skills.py --output build/release-v1
python -B scripts/install_skills.py --candidate build/release-v1 --project /path/to/research --platform claude
python -B scripts/install_skills.py --candidate build/release-v1 --project /path/to/research --platform codex
```

Use a new build directory and project installation; existing outputs are preserved. `--platform chatgpt` remains a compatibility alias for the local `.agents/skills` destination and does not claim browser support.

The source implementation is in `src/fmp_skills`; checked-in skill folders are generated self-contained copies. When a helper changes, build into a new output directory, then replace the corresponding complete `skills/<name>` folder with the generated folder before committing. Repository aliases, for example `python -B scripts/fmp_research.py company --input input.json --output brief.md`, use the same validated runner.

## Research limits

13F reports are delayed disclosed quarter-end positions, not exact trades, cost basis, motives or current holdings. Amendments, missing coverage and corporate actions require explicit checks. Fund update timestamps are not necessarily holdings-effective dates; excluded derivatives, cash and nested funds are not zero economic exposure. Current estimate snapshots are not historical consensus, and an ended fiscal period can still await results. Ambiguous pending periods remain unresolved.

Separate provider facts, calculations and AI interpretation. Source retrieval success differs from original-filing verification. Selected live source checks and model-driven workflows have been observed, not universal coverage or accuracy. These tools provide educational research, not investment advice or brokerage execution.

## Licence and disclosure

Original code and documentation are [MIT-licensed](LICENSE). All supplied examples are synthetic; third-party data keeps its own terms. No raw provider data or internal evidence is distributed.

Disclosure: I am developing an affiliate relationship with Financial Modeling Prep.
