from __future__ import annotations

from .config import Settings
from .finance import FMPClient
from .io_utils import ensure_directory, read_text_if_exists, write_json, write_text
from .llm import OpenAIClient
from .models import ComplianceReport, FactPack, MoverCandidate, ResearchBrief
from .prompts import COMPLIANCE_PROMPT, DRAFT_PROMPT, FINAL_DETAILS_PASS_PROMPT, RESEARCH_PROMPT

DEFAULT_STYLE_NOTES = """
- Write like a punchy private investor-columnist, not an analyst note
- Use first person naturally and explain why the move caught my eye
- Keep the article tight, usually around 450 to 550 words
- Prefer one clear story angle over a list of metrics
- Use company-specific detail when available and say plainly when it is not
- Avoid boilerplate phrasing and padded sector commentary
- Use short paragraphs and a balanced verdict
""".strip()

DEFAULT_MOTLEY_RULES = """
- Use British English
- Avoid overstating certainty
- Separate fact from interpretation
- Keep the tone balanced and investor-focused
- Note uncertainty if the exact catalyst is not confirmed
- Keep the article concise and avoid generic filler
""".strip()


class Pipeline:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.finance = FMPClient(api_key=settings.fmp_api_key, base_url=settings.fmp_base_url)
        self.llm = self._general_llm_client(settings.openrouter_model)
        self.article_llm = self._openrouter_client(settings.article_openrouter_model)
        self.final_details_llm = self._openrouter_client(settings.final_details_openrouter_model)
        ensure_directory(settings.output_dir)

    def _openrouter_client(self, model: str) -> OpenAIClient:
        return OpenAIClient(
            provider="openrouter",
            api_key=self.settings.openrouter_api_key,
            model=model,
            base_url=self.settings.openrouter_base_url,
            site_url=self.settings.openrouter_site_url,
            app_name=self.settings.openrouter_app_name,
        )

    def _general_llm_client(self, openrouter_model: str) -> OpenAIClient:
        if self.settings.llm_provider == "openrouter":
            return self._openrouter_client(openrouter_model)
        return OpenAIClient(
            provider="openai",
            api_key=self.settings.openai_api_key,
            model=self.settings.openai_model,
        )

    def _style_notes(self, override: str | None) -> str:
        if override:
            return override
        return read_text_if_exists(self.settings.style_notes_file, DEFAULT_STYLE_NOTES)

    def _motley_rules(self, override: str | None) -> str:
        if override:
            return override
        return read_text_if_exists(self.settings.motley_rules_file, DEFAULT_MOTLEY_RULES)

    def _research_system_prompt(self) -> str:
        return read_text_if_exists(self.settings.research_prompt_file, RESEARCH_PROMPT)

    def _draft_system_prompt(self) -> str:
        return read_text_if_exists(self.settings.draft_prompt_file, DRAFT_PROMPT)

    def _compliance_system_prompt(self) -> str:
        return read_text_if_exists(self.settings.compliance_prompt_file, COMPLIANCE_PROMPT)

    def _final_details_system_prompt(self) -> str:
        return read_text_if_exists(self.settings.final_details_prompt_file, FINAL_DETAILS_PASS_PROMPT)

    def scan(self, tickers: list[str], min_abs_day_move: float = 4.0) -> list[MoverCandidate]:
        movers = self.finance.scan_movers(tickers, min_abs_day_move=min_abs_day_move)
        write_json(self.settings.output_dir / "movers.json", [item.to_dict() for item in movers])
        return movers

    def scan_uk_market(
        self,
        min_abs_day_move: float = 4.0,
        min_price: float = 0.1,
        min_avg_volume: float = 50_000,
        limit: int = 3,
    ) -> list[MoverCandidate]:
        movers = self.finance.scan_uk_market(
            min_abs_day_move=min_abs_day_move,
            min_price=min_price,
            min_avg_volume=min_avg_volume,
            limit=limit,
        )
        write_json(self.settings.output_dir / "movers.json", [item.to_dict() for item in movers])
        return movers

    def fact_pack(self, ticker: str) -> FactPack:
        fact_pack = self.finance.build_fact_pack(ticker)
        write_json(self.settings.output_dir / f"{ticker}_fact_pack.json", fact_pack.to_dict())
        return fact_pack

    def research(
        self,
        ticker: str,
        fact_pack: FactPack | None = None,
    ) -> ResearchBrief:
        local_fact_pack = fact_pack or self.fact_pack(ticker)
        try:
            news_items = self.finance.get_news(ticker, limit=10)
        except Exception:
            news_items = []
        try:
            press_releases = self.finance.get_press_releases(ticker, limit=10)
        except Exception:
            press_releases = []
        try:
            price_context = self.finance.get_recent_price_context(
                ticker,
                company_name=local_fact_pack.stats.company_name,
                days=3,
            )
        except Exception:
            price_context = []
        try:
            article_summaries = self.finance.search_recent_articles(
                ticker,
                company_name=local_fact_pack.stats.company_name,
                max_results=3,
            )
        except Exception:
            article_summaries = []
        brief = self.llm.research(
            local_fact_pack,
            news_items,
            press_releases,
            price_context,
            article_summaries,
            system_prompt=self._research_system_prompt(),
        )
        write_json(self.settings.output_dir / f"{ticker}_research.json", brief.to_dict())
        return brief

    def draft(
        self,
        ticker: str,
        fact_pack: FactPack | None = None,
        research: ResearchBrief | None = None,
        style_notes: str | None = None,
        motley_rules: str | None = None,
    ) -> str:
        local_fact_pack = fact_pack or self.fact_pack(ticker)
        local_research = research or self.research(ticker, local_fact_pack)
        article = self.article_llm.draft_article(
            local_fact_pack,
            local_research,
            self._style_notes(style_notes),
            self._motley_rules(motley_rules),
            draft_prompt=self._draft_system_prompt(),
        )
        write_text(self.settings.output_dir / f"{ticker}_draft.md", article)
        return article

    def compliance(
        self,
        ticker: str,
        article: str,
        style_notes: str | None = None,
        motley_rules: str | None = None,
    ) -> ComplianceReport:
        report = self.llm.check_compliance(
            article,
            self._style_notes(style_notes),
            self._motley_rules(motley_rules),
            system_prompt=self._compliance_system_prompt(),
        )
        write_json(self.settings.output_dir / f"{ticker}_compliance.json", report.to_dict())
        return report

    def write_and_review(
        self,
        ticker: str,
        fact_pack: FactPack,
        research: ResearchBrief | None,
        research_notes: str,
        extra_notes: str = "",
        style_notes: str | None = None,
        motley_rules: str | None = None,
    ) -> tuple[str, ComplianceReport]:
        article = self.article_llm.draft_article_from_notes(
            fact_pack,
            research,
            research_notes,
            extra_notes,
            self._style_notes(style_notes),
            self._motley_rules(motley_rules),
            draft_prompt=self._draft_system_prompt(),
        )
        write_text(self.settings.output_dir / f"{ticker}_draft.md", article)
        report = self.compliance(
            ticker,
            article,
            style_notes=style_notes,
            motley_rules=motley_rules,
        )
        return article, report

    def build_article_prompt(
        self,
        fact_pack: FactPack,
        research: ResearchBrief | None,
        research_notes: str,
        story_angle: str = "",
        extra_notes: str = "",
        style_notes: str | None = None,
        motley_rules: str | None = None,
    ) -> str:
        return self.llm.build_article_prompt(
            fact_pack,
            research,
            story_angle,
            research_notes,
            extra_notes,
            self._style_notes(style_notes),
            self._motley_rules(motley_rules),
        )

    def draft_from_prompt(
        self,
        ticker: str,
        prompt_text: str,
        style_notes: str | None = None,
    ) -> str:
        full_prompt = self.llm.compose_article_generation_prompt(
            prompt_text,
            self._style_notes(style_notes),
        )
        article = self.article_llm.generate_article_from_prompt(
            full_prompt,
            system_prompt=self._draft_system_prompt(),
        )
        write_text(self.settings.output_dir / f"{ticker}_draft.md", article)
        return article

    def final_details_pass(
        self,
        ticker: str,
        article: str,
        motley_rules: str | None = None,
    ) -> str:
        revised_article = self.final_details_llm.final_details_pass(
            article,
            self._motley_rules(motley_rules),
            system_prompt=self._final_details_system_prompt(),
        )
        write_text(self.settings.output_dir / f"{ticker}_complete.md", revised_article)
        return revised_article

    def save_complete_article(
        self,
        ticker: str,
        article: str,
    ) -> None:
        write_text(self.settings.output_dir / f"{ticker}_complete.md", article)

    def run(
        self,
        tickers: list[str] | None = None,
        min_abs_day_move: float = 4.0,
        style_notes: str | None = None,
        motley_rules: str | None = None,
        uk_market_scan: bool = True,
        limit: int = 3,
    ) -> dict[str, object]:
        tickers = tickers or []
        movers = (
            self.scan_uk_market(min_abs_day_move=min_abs_day_move, limit=limit)
            if uk_market_scan
            else self.scan(tickers, min_abs_day_move=min_abs_day_move)
        )
        selected = movers[:limit] if movers else [
            MoverCandidate(
                ticker=ticker,
                company_name=None,
                price=None,
                day_change_pct=None,
                volume=None,
                avg_volume=None,
                score=0,
            )
            for ticker in tickers
        ]

        results: dict[str, object] = {"movers": [item.to_dict() for item in movers], "articles": {}}
        for candidate in selected:
            fact_pack = self.fact_pack(candidate.ticker)
            research = self.research(candidate.ticker, fact_pack)
            article = self.draft(candidate.ticker, fact_pack, research, style_notes=style_notes, motley_rules=motley_rules)
            compliance = self.compliance(candidate.ticker, article, style_notes=style_notes, motley_rules=motley_rules)
            results["articles"][candidate.ticker] = {
                "fact_pack": fact_pack.to_dict(),
                "research": research.to_dict(),
                "article_path": str(self.settings.output_dir / f"{candidate.ticker}_draft.md"),
                "compliance": compliance.to_dict(),
            }
        write_json(self.settings.output_dir / "run_summary.json", results)
        return results
