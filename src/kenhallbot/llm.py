from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from openai import OpenAI

from .models import ComplianceReport, FactPack, ResearchBrief
from .prompts import (
    COMPLIANCE_PROMPT,
    DRAFT_PROMPT,
    FINAL_DETAILS_PASS_PROMPT,
    MOTLEY_RULES_PROMPT,
    RESEARCH_PROMPT,
    WRITER_STYLE_PROMPT,
)


class LLMError(RuntimeError):
    pass


@dataclass
class OpenAIClient:
    provider: str
    api_key: str
    model: str
    base_url: str | None = None
    site_url: str = ""
    app_name: str = ""

    def _client(self) -> OpenAI:
        if not self.api_key:
            raise LLMError(f"Missing API key for provider '{self.provider}'.")

        kwargs: dict[str, Any] = {"api_key": self.api_key}
        if self.base_url:
            kwargs["base_url"] = self.base_url
        if self.provider == "openrouter":
            headers: dict[str, str] = {}
            if self.site_url:
                headers["HTTP-Referer"] = self.site_url
            if self.app_name:
                headers["X-Title"] = self.app_name
            if headers:
                kwargs["default_headers"] = headers
        return OpenAI(**kwargs)

    def _message_response(self, prompt: str, user_content: str) -> str:
        client = self._client()
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": user_content},
        ]
        if self.provider == "openrouter":
            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
            )
            message = response.choices[0].message.content
            if isinstance(message, list):
                return "".join(
                    part.get("text", "") for part in message if isinstance(part, dict)
                )
            return message or ""

        response = client.responses.create(
            model=self.model,
            input=messages,
        )
        return response.output_text

    def _text_response(self, prompt: str, payload: dict[str, Any]) -> str:
        return self._message_response(prompt, json.dumps(payload, ensure_ascii=True))

    def _json_response(self, prompt: str, payload: dict[str, Any]) -> dict[str, Any]:
        text = self._text_response(prompt, payload)
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise LLMError(f"Model did not return valid JSON: {text}") from exc

    def _normalise_list(self, value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        text = str(value).strip()
        return [text] if text else []

    def _compose_system_prompt(self, *sections: str) -> str:
        return "\n\n".join(section.strip() for section in sections if section and section.strip())

    def _writer_research_payload(self, research: ResearchBrief) -> dict[str, Any]:
        raw_context = research.raw_context or {}
        article_summaries = raw_context.get("article_summaries", [])
        news_items = raw_context.get("news_items", [])
        press_releases = raw_context.get("press_releases", [])
        return {
            "ticker": research.ticker,
            "likely_reason": self._normalise_list(research.likely_reason),
            "confidence": research.confidence,
            "evidence": self._normalise_list(research.evidence),
            "recent_history": self._normalise_list(research.recent_history),
            "caveats": self._normalise_list(research.caveats),
            "article_angles": self._normalise_list(research.article_angles),
            "sector_backdrop": self._normalise_list(research.sector_backdrop),
            "company_developments": self._normalise_list(research.company_developments),
            "watch_items": self._normalise_list(research.watch_items),
            "price_context": raw_context.get("price_context", []),
            "article_summaries": [
                {
                    "title": item.get("title"),
                    "summary": item.get("summary"),
                    "url": item.get("url"),
                }
                for item in article_summaries[:3]
            ],
            "news_items": [
                {
                    "title": item.get("title"),
                    "publishedDate": item.get("publishedDate"),
                    "site": item.get("site"),
                    "text": item.get("text"),
                    "url": item.get("url"),
                }
                for item in news_items[:5]
            ],
            "press_releases": [
                {
                    "title": item.get("title"),
                    "publishedDate": item.get("publishedDate"),
                    "site": item.get("site"),
                    "text": item.get("text"),
                    "url": item.get("url"),
                }
                for item in press_releases[:5]
            ],
        }

    def research(
        self,
        fact_pack: FactPack,
        news_items: list[dict[str, Any]],
        press_releases: list[dict[str, Any]],
        price_context: list[dict[str, Any]],
        article_summaries: list[dict[str, Any]],
    ) -> ResearchBrief:
        payload = {
            "fact_pack": fact_pack.to_dict(),
            "price_context": price_context,
            "news_items": [
                {
                    "title": item.get("title"),
                    "publishedDate": item.get("publishedDate"),
                    "site": item.get("site"),
                    "text": item.get("text"),
                    "url": item.get("url"),
                }
                for item in news_items
            ],
            "press_releases": [
                {
                    "title": item.get("title"),
                    "publishedDate": item.get("publishedDate"),
                    "site": item.get("site"),
                    "text": item.get("text"),
                    "url": item.get("url"),
                }
                for item in press_releases
            ],
            "article_summaries": article_summaries,
        }
        data = self._json_response(RESEARCH_PROMPT, payload)
        return ResearchBrief(
            ticker=fact_pack.ticker,
            likely_reason=data.get("likely_reason", ""),
            confidence=data.get("confidence", "low"),
            evidence=data.get("evidence", []),
            recent_history=data.get("recent_history", []),
            caveats=data.get("caveats", []),
            article_angles=data.get("article_angles", []),
            raw_context=payload,
            sector_backdrop=data.get("sector_backdrop", []),
            company_developments=data.get("company_developments", []),
            watch_items=data.get("watch_items", []),
        )

    def draft_article(self, fact_pack: FactPack, research: ResearchBrief, style_notes: str, motley_rules: str) -> str:
        prompt = self._compose_system_prompt(
            DRAFT_PROMPT,
            WRITER_STYLE_PROMPT,
            MOTLEY_RULES_PROMPT,
            f"Writer house style:\n{style_notes}",
            f"Publisher rules:\n{motley_rules}",
        )
        payload = {
            "fact_pack": fact_pack.to_dict(),
            "research_brief": self._writer_research_payload(research),
        }
        return self._text_response(prompt, payload)

    def draft_article_from_notes(
        self,
        fact_pack: FactPack,
        research: ResearchBrief | None,
        research_notes: str,
        extra_notes: str,
        style_notes: str,
        motley_rules: str,
    ) -> str:
        prompt = self._compose_system_prompt(
            DRAFT_PROMPT,
            WRITER_STYLE_PROMPT,
            MOTLEY_RULES_PROMPT,
            f"Writer house style:\n{style_notes}",
            f"Publisher rules:\n{motley_rules}",
        )
        payload = {
            "fact_pack": fact_pack.to_dict(),
            "research_brief": self._writer_research_payload(research) if research else None,
            "edited_research_notes": research_notes,
            "extra_notes": extra_notes,
        }
        return self._text_response(prompt, payload)

    def build_article_prompt(
        self,
        fact_pack: FactPack,
        research: ResearchBrief | None,
        story_angle: str,
        research_notes: str,
        extra_notes: str,
        style_notes: str,
        motley_rules: str,
    ) -> str:
        stats = fact_pack.stats

        lines = [
            "Assignment",
            f"- Company: {stats.company_name or fact_pack.ticker}",
            f"- Ticker: {fact_pack.ticker}",
        ]
        if story_angle.strip():
            lines.append(f"- Lean into this angle if the evidence supports it: {story_angle.strip()}")

        if extra_notes.strip():
            lines.extend(["", "Additional writing priorities", extra_notes.strip()])

        if research_notes.strip():
            lines.extend(["", research_notes.strip()])

        return "\n".join(lines).strip()

    def compose_article_generation_prompt(self, dynamic_prompt_text: str, style_notes: str) -> str:
        lines = [
            "Write a Motley Fool UK-style article in Ken Hall's voice.",
            "",
            "Output",
            "- Return the finished article only in markdown.",
            "- Use British English.",
            "- Keep it concise, story-led, and investor-focused.",
            "",
            "Writing requirements",
            "- Use first person naturally and answer the main headline question directly.",
            "- Lead with the key angle or the uncertainty, not a generic company profile.",
            "- Explain what the shares did, what may be driving the move, and what I think now.",
            "- Use only the numbers that sharpen the argument.",
            "- Prefer concrete company detail, recent developments, and what investors should watch next.",
            "- End with a clear, balanced verdict.",
        ]
        if dynamic_prompt_text.strip():
            lines.extend(["", dynamic_prompt_text.strip()])
        lines.extend(
            [
                "",
                "House style",
                style_notes.strip(),
            ]
        )
        return "\n".join(lines).strip()

    def generate_article_from_prompt(self, prompt_text: str) -> str:
        return self._message_response(
            "Write the requested article and return only the finished markdown article.",
            prompt_text,
        )

    def final_details_pass(self, article: str, motley_rules: str) -> str:
        prompt = self._compose_system_prompt(
            FINAL_DETAILS_PASS_PROMPT,
            f"Technical and compliance specification:\n{motley_rules}",
        )
        return self._message_response(prompt, article)

    def check_compliance(self, article: str, style_notes: str, motley_rules: str) -> ComplianceReport:
        prompt = self._compose_system_prompt(
            COMPLIANCE_PROMPT,
            f"Writer house style:\n{style_notes}",
            f"Publisher rules:\n{motley_rules}",
        )
        payload = {
            "article": article,
        }
        data = self._json_response(prompt, payload)
        return ComplianceReport(
            verdict=data.get("verdict", "needs_review"),
            issues=data.get("issues", []),
            revision_advice=data.get("revision_advice", []),
        )
