# KenHallBot

For a Windows-focused setup guide written for a non-technical user, see [WINDOWS_DEPLOYMENT.md](/home/cam/Documents/Github/KenHallBot/WINDOWS_DEPLOYMENT.md).

A lean Python pipeline for:

- identifying major stock moves
- pulling a standard fact pack
- researching likely qualitative reasons
- drafting an article in your style
- checking output against Motley Fool UK-style rules

## What it does

The app exposes a small CLI that can:

- scan a watchlist for notable movers
- scan the London market directly for UK movers
- build a reusable metrics pack for a ticker
- research recent qualitative catalysts and history with LLM synthesis
- draft an article from facts + research
- run a final compliance/style review
- run the full flow end-to-end
- launch a simple local GUI

## Requirements

- Python 3.11+
- `OPENAI_API_KEY`

Optional:

- `FMP_API_KEY`

Optional environment variables:

- `LLM_PROVIDER` (`openai` or `openrouter`)
- `OPENAI_MODEL`
- `OPENROUTER_API_KEY`
- `OPENROUTER_MODEL`
- `OPENROUTER_BASE_URL`
- `OPENROUTER_SITE_URL`
- `OPENROUTER_APP_NAME`
- `FMP_BASE_URL`
- `OUTPUT_DIR`
- `STYLE_NOTES_FILE`
- `MOTLEY_RULES_FILE`

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Configure

Create a `.env` file or export variables in your shell:

```bash
export OPENAI_API_KEY="..."
export OPENAI_MODEL="gpt-4.1-mini"
```

If you have an FMP key that supports the endpoints you need, you can also set:

```bash
export FMP_API_KEY="..."
```

Use OpenRouter instead:

```bash
export LLM_PROVIDER="openrouter"
export OPENROUTER_API_KEY="..."
export OPENROUTER_MODEL="openai/gpt-4.1-mini"
export OPENROUTER_SITE_URL="https://your-site.example"
export OPENROUTER_APP_NAME="KenHallBot"
```

## GUI

Launch the local interface:

```bash
kenhallbot-gui
```

Then open:

```text
http://127.0.0.1:5000
```

The GUI is designed around two clean tabs:

- `Research setup`: scan movers, select a company, edit research guidance before the run, and maintain the working brief item by item under each category
- `Write and review`: edit the single article-generation prompt, generate the draft with Claude Sonnet 4.6 via OpenRouter, edit the final output, run a final technical details pass, and run review notes against the current version

## Usage

Run the full pipeline for one or more tickers:

```bash
kenhallbot run --tickers BATS.L SHEL.L
```

Run the full pipeline from UK market movers:

```bash
kenhallbot run --uk-market --min-abs-day-move 5
```

Scan a watchlist for notable movers:

```bash
kenhallbot scan --tickers BATS.L SHEL.L GSK.L
```

Scan the London market directly for notable movers:

```bash
kenhallbot scan --uk-market --min-abs-day-move 5
```

Build a fact pack only:

```bash
kenhallbot fact-pack --ticker SHEL.L
```

## Output

Generated files are written to `output/` by default:

- `movers.json`
- `{ticker}_fact_pack.json`
- `{ticker}_research.json`
- `{ticker}_draft.md`
- `{ticker}_compliance.json`

## Customising your voice and rules

Edit these files:

- `config/style_notes.md`
- `config/motley_rules_uk.md`

The pipeline loads them automatically for draft and compliance stages.

## Notes

- This tool is designed for human-in-the-loop publishing.
- It does not auto-publish articles.
- It separates factual retrieval from LLM synthesis to reduce hallucination risk.
- UK market scans use a free scrape of public UK mover pages and return the top 3 names by 1-day move.
- Fact packs can fall back to scraped mover metadata when finance API endpoints are unavailable.
- UK market workflows default to the top 3 movers to keep the process focused and API usage efficient.
- OpenRouter is supported through its OpenAI-compatible API base.
