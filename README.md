# KenHallBot

For a Windows-focused setup guide written for a non-technical user, see [WINDOWS_DEPLOYMENT.md](/home/cam/Documents/Github/KenHallBot/WINDOWS_DEPLOYMENT.md).

A lean Python pipeline for:

- identifying major stock moves
- pulling a standard fact pack
- researching likely qualitative reasons
- drafting an article in your style
- checking output against your editorial rules

## What it does

The app helps you:

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

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
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

## Customising your voice and rules

Use the `Settings` tab in the GUI.

There you can:

- add or update your API keys
- choose the underlying models used for research, article generation, and final details
- edit the system prompts used for research, article generation, and final details

If you need to work with the underlying files directly, the app stores its supporting configuration in `config/`.

## Notes

- This tool is designed for human-in-the-loop publishing.
- It does not auto-publish articles.
- It separates factual retrieval from LLM synthesis to reduce hallucination risk.
- UK market scans use a free scrape of public UK mover pages and return the top 3 names by 1-day move.
- Fact packs can fall back to scraped mover metadata when finance API endpoints are unavailable.
- UK market workflows default to the top 3 movers to keep the process focused and API usage efficient.
- OpenRouter is supported through its OpenAI-compatible API base.
