from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class PricePerformance:
    day_change_pct: float | None = None
    five_day_change_pct: float | None = None
    one_month_change_pct: float | None = None
    ytd_change_pct: float | None = None
    one_year_change_pct: float | None = None
    relative_volume: float | None = None
    fifty_two_week_low: float | None = None
    fifty_two_week_high: float | None = None


@dataclass
class StandardStats:
    company_name: str | None = None
    exchange: str | None = None
    sector: str | None = None
    industry: str | None = None
    market_cap: float | None = None
    price: float | None = None
    dividend_yield: float | None = None
    pe_ratio: float | None = None
    forward_pe: float | None = None


@dataclass
class FactPack:
    ticker: str
    performance: PricePerformance
    stats: StandardStats
    source_notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class MoverCandidate:
    ticker: str
    company_name: str | None
    price: float | None
    day_change_pct: float | None
    volume: float | None
    avg_volume: float | None
    score: float
    raw_context: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ResearchBrief:
    ticker: str
    likely_reason: str
    confidence: str
    evidence: list[str]
    recent_history: list[str]
    caveats: list[str]
    article_angles: list[str]
    raw_context: dict[str, Any]
    sector_backdrop: list[str] = field(default_factory=list)
    company_developments: list[str] = field(default_factory=list)
    watch_items: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ComplianceReport:
    verdict: str
    issues: list[str]
    revision_advice: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
