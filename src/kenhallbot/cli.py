from __future__ import annotations

import argparse
import json
import sys

from .config import load_settings
from .pipeline import Pipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="kenhallbot", description="Lean stock-move article assistant.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan_parser = subparsers.add_parser("scan", help="Scan a list of tickers or the UK market for notable movers.")
    scan_parser.add_argument("--tickers", nargs="+")
    scan_parser.add_argument("--min-abs-day-move", type=float, default=4.0)
    scan_parser.add_argument("--uk-market", action="store_true", help="Scan the London market directly instead of using explicit tickers.")
    scan_parser.add_argument("--limit", type=int, default=3)

    fact_pack_parser = subparsers.add_parser("fact-pack", help="Build a fact pack for one ticker.")
    fact_pack_parser.add_argument("--ticker", required=True)

    research_parser = subparsers.add_parser("research", help="Research likely reasons for a move.")
    research_parser.add_argument("--ticker", required=True)

    draft_parser = subparsers.add_parser("draft", help="Draft an article for one ticker.")
    draft_parser.add_argument("--ticker", required=True)

    compliance_parser = subparsers.add_parser("check", help="Run compliance checks for a drafted article.")
    compliance_parser.add_argument("--ticker", required=True)
    compliance_parser.add_argument("--article-file", required=True)

    run_parser = subparsers.add_parser("run", help="Run the full pipeline.")
    run_parser.add_argument("--tickers", nargs="+")
    run_parser.add_argument("--min-abs-day-move", type=float, default=4.0)
    run_parser.add_argument("--uk-market", action="store_true", help="Source movers from the London market.")
    run_parser.add_argument("--limit", type=int, default=3)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    settings = load_settings()
    pipeline = Pipeline(settings)

    if args.command == "scan":
        if args.uk_market:
            result = pipeline.scan_uk_market(min_abs_day_move=args.min_abs_day_move, limit=args.limit)
        else:
            if not args.tickers:
                parser.error("scan requires --tickers unless --uk-market is used.")
            result = pipeline.scan(args.tickers, min_abs_day_move=args.min_abs_day_move)
        print(json.dumps([item.to_dict() for item in result], indent=2))
        return 0

    if args.command == "fact-pack":
        result = pipeline.fact_pack(args.ticker)
        print(json.dumps(result.to_dict(), indent=2))
        return 0

    if args.command == "research":
        result = pipeline.research(args.ticker)
        print(json.dumps(result.to_dict(), indent=2))
        return 0

    if args.command == "draft":
        result = pipeline.draft(args.ticker)
        print(result)
        return 0

    if args.command == "check":
        article = open(args.article_file, "r", encoding="utf-8").read()
        result = pipeline.compliance(args.ticker, article)
        print(json.dumps(result.to_dict(), indent=2))
        return 0

    if args.command == "run":
        if not args.uk_market and not args.tickers:
            parser.error("run requires --tickers unless --uk-market is used.")
        result = pipeline.run(
            args.tickers,
            min_abs_day_move=args.min_abs_day_move,
            uk_market_scan=args.uk_market,
            limit=args.limit,
        )
        print(json.dumps(result, indent=2))
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
