from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from html import unescape
import json
import re
from typing import Any
from urllib.parse import parse_qs, quote_plus, unquote, urlparse

import httpx

from .models import FactPack, MoverCandidate, PricePerformance, StandardStats


class FinanceAPIError(RuntimeError):
    pass


@dataclass
class FMPClient:
    api_key: str
    base_url: str
    timeout: float = 20.0
    simplywall_base_url: str = "https://simplywall.st"

    def _get(self, path: str, **params: Any) -> Any:
        if not self.api_key:
            raise FinanceAPIError("Missing FMP_API_KEY.")

        query = {"apikey": self.api_key, **params}
        url = f"{self.base_url.rstrip('/')}/{path.lstrip('/')}"
        response = httpx.get(url, params=query, timeout=self.timeout)
        response.raise_for_status()
        data = response.json()
        if isinstance(data, dict) and data.get("Error Message"):
            raise FinanceAPIError(data["Error Message"])
        return data

    def _get_optional(self, path: str, **params: Any) -> Any:
        try:
            return self._get(path, **params)
        except Exception:
            return None

    def _extract_simplywall_market_payload(self, html: str, url: str) -> dict[str, Any]:
        match = re.search(r'window\["__RQ_R_db_"\]\.push\((\{.*?\})\);</script>', html)
        if not match:
            raise FinanceAPIError(f"Could not parse Simply Wall St page: {url}")
        data = json.loads(match.group(1))
        for query in data.get("queries", []):
            state = query.get("state")
            if not isinstance(state, dict):
                continue
            payload = state.get("data")
            if not isinstance(payload, dict):
                continue
            pages = payload.get("pages")
            if isinstance(pages, list) and pages:
                first_page = pages[0]
                if isinstance(first_page, dict):
                    companies = first_page.get("companies")
                    if isinstance(companies, list):
                        return first_page
            companies = payload.get("companies")
            if isinstance(companies, list):
                return {"companies": companies}
        raise FinanceAPIError(f"Could not locate company list in Simply Wall St page: {url}")

    def _load_simplywall_market_page_payload(self, path: str, page: int = 1) -> dict[str, Any]:
        separator = "&" if "?" in path else "?"
        query = f"{separator}page={page}" if page > 1 else ""
        url = f"{self.simplywall_base_url.rstrip('/')}/stocks/gb/{path.lstrip('/')}{query}"
        return self._extract_simplywall_market_payload(self._fetch_page(url), url)

    def _load_simplywall_market_page(self, path: str) -> list[dict[str, Any]]:
        payload = self._load_simplywall_market_page_payload(path)
        companies = payload.get("companies")
        if isinstance(companies, list):
            return companies
        raise FinanceAPIError(f"Could not locate company list in Simply Wall St page: {path}")

    def _load_all_simplywall_market_companies(self, path: str) -> list[dict[str, Any]]:
        first_page = self._load_simplywall_market_page_payload(path, page=1)
        companies = list(first_page.get("companies", []))
        meta = first_page.get("meta", {})
        total_pages = int(meta.get("totalPages") or 1)
        for page in range(2, total_pages + 1):
            payload = self._load_simplywall_market_page_payload(path, page=page)
            companies.extend(payload.get("companies", []))
        return companies

    def _market_move_for_window(self, company: dict[str, Any], move_window: str) -> float | None:
        mapping = {
            "1D": "return1D",
            "7D": "return7D",
            "1Y": "return1YrAbs",
        }
        field = mapping.get(move_window, "return1D")
        value = company.get(field)
        if value is None:
            return None
        return value * 100

    def _normalise_simplywall_ticker(self, company: dict[str, Any]) -> str:
        unique_symbol = company.get("uniqueSymbol")
        ticker = company.get("tickerSymbol")
        if unique_symbol and ":" in unique_symbol:
            exchange, symbol = unique_symbol.split(":", 1)
            if exchange == "LSE":
                return f"{symbol}.L"
        if ticker:
            return f"{ticker}.L"
        raise FinanceAPIError("Missing ticker symbol in Simply Wall St payload.")

    def _clean_html_text(self, raw_html: str) -> str:
        text = re.sub(r"<script.*?</script>", " ", raw_html, flags=re.I | re.S)
        text = re.sub(r"<style.*?</style>", " ", text, flags=re.I | re.S)
        text = re.sub(r"<[^>]+>", " ", text)
        text = unescape(re.sub(r"\s+", " ", text))
        return text.strip()

    def _fetch_page(self, url: str) -> str:
        response = httpx.get(
            url,
            timeout=self.timeout,
            follow_redirects=True,
            headers={"user-agent": "Mozilla/5.0 (KenHallBot Prototype)"},
        )
        response.raise_for_status()
        return response.text

    def _extract_simplywall_price_history(self, html: str, days: int = 3) -> list[dict[str, Any]]:
        marker = '"queryKey":["price-history"'
        marker_index = html.find(marker)
        if marker_index == -1:
            return []

        window = html[max(0, marker_index - 400000):marker_index]
        e_key = '"entities":'
        e_index = window.rfind(e_key)
        if e_index == -1:
            return []
        x_index = window.rfind("[", 0, e_index)
        if x_index == -1:
            return []

        def extract_json_value(source: str, start_index: int) -> str:
            opening = source[start_index]
            closing = "]" if opening == "[" else "}"
            depth = 0
            in_string = False
            escape = False
            for pos in range(start_index, len(source)):
                char = source[pos]
                if in_string:
                    if escape:
                        escape = False
                    elif char == "\\":
                        escape = True
                    elif char == '"':
                        in_string = False
                    continue
                if char == '"':
                    in_string = True
                elif char == opening:
                    depth += 1
                elif char == closing:
                    depth -= 1
                    if depth == 0:
                        return source[start_index:pos + 1]
            raise FinanceAPIError("Could not extract price history JSON value.")

        x_data = json.loads(extract_json_value(window, x_index))
        entities = json.loads(extract_json_value(window, e_index + len(e_key)))
        rows: list[dict[str, Any]] = []
        for ts in x_data[-days:]:
            price = entities.get(str(ts))
            if price is None:
                continue
            rows.append({"date": date.fromtimestamp(ts / 1000).isoformat(), "close": price})
        return rows

    def _search_duckduckgo(self, query: str, max_results: int = 6) -> list[dict[str, str]]:
        response = httpx.get(
            "https://duckduckgo.com/html/",
            params={"q": query},
            timeout=self.timeout,
            follow_redirects=True,
            headers={"user-agent": "Mozilla/5.0"},
        )
        response.raise_for_status()

        results: list[dict[str, str]] = []
        seen: set[str] = set()
        patterns = [
            r'<a rel="nofollow" class="result__a" href="(.*?)">(.*?)</a>',
            r'<a[^>]*class="[^"]*result__a[^"]*"[^>]*href="(.*?)"[^>]*>(.*?)</a>',
        ]
        matches: list[tuple[str, str]] = []
        for pattern in patterns:
            matches = [(match.group(1), match.group(2)) for match in re.finditer(pattern, response.text, re.S)]
            if matches:
                break

        for href_raw, title_raw in matches:
            href = unescape(href_raw)
            title = self._clean_html_text(title_raw)
            if href.startswith("//duckduckgo.com/l/?"):
                params = parse_qs(urlparse("https:" + href).query)
                href = unquote(params.get("uddg", [""])[0])
            if not href or href in seen:
                continue
            seen.add(href)
            results.append({"title": title, "url": href})
            if len(results) >= max_results:
                break
        return results

    def find_company_page_url(self, ticker: str, company_name: str | None = None) -> str | None:
        try:
            snapshot = self.find_uk_company_snapshot(ticker)
            canonical = snapshot.get("canonicalUrl")
            if canonical:
                return f"{self.simplywall_base_url.rstrip('/')}{canonical}"
        except Exception:
            pass

        query = f'site:simplywall.st "{ticker}" "{company_name or ticker}" simply wall st'
        for result in self._search_duckduckgo(query, max_results=5):
            if "simplywall.st/stocks/gb/" in result["url"]:
                return result["url"]
        return None

    def get_recent_price_context(self, ticker: str, company_name: str | None = None, days: int = 3) -> list[dict[str, Any]]:
        company_page = self.find_company_page_url(ticker, company_name=company_name)
        if not company_page:
            return []
        html = self._fetch_page(company_page)
        return self._extract_simplywall_price_history(html, days=days)

    def _extract_article_summary(self, html: str) -> str:
        meta_match = re.search(r'<meta[^>]+name=["\']description["\'][^>]+content=["\'](.*?)["\']', html, re.I | re.S)
        if meta_match:
            return unescape(meta_match.group(1)).strip()

        paragraphs = re.findall(r"<p[^>]*>(.*?)</p>", html, re.I | re.S)
        cleaned: list[str] = []
        for paragraph in paragraphs:
            text = self._clean_html_text(paragraph)
            if len(text) >= 80:
                cleaned.append(text)
            if len(cleaned) >= 2:
                break
        return " ".join(cleaned)

    def _is_low_signal_article_result(self, title: str, url: str, summary: str = "") -> bool:
        haystack = " ".join([title, url, summary]).lower()
        patterns = [
            "google.com/finance/quote/",
            "finance.yahoo.com/quote/",
            "marketwatch.com/investing/stock/",
            "simplywall.st/stocks/",
            "hl.co.uk/shares/shares-search-results",
            "morningstar.co.uk/uk/stockreport",
            "shareprices.com/lse/",
            "londonstockexchange.com/stock/",
            "stock price & news",
            "real-time quote",
            "historical performance, charts",
            "all the latest stock market news",
            "latest share news for",
            "buy and sell",
        ]
        if any(pattern in haystack for pattern in patterns):
            return True

        parsed = urlparse(url)
        host = parsed.netloc.lower()
        path = parsed.path.lower().rstrip("/")
        title_lower = title.lower().strip()
        summary_lower = summary.lower().strip()

        if summary_lower in {"null", "none"}:
            return True
        if title_lower in {"press releases", "investor relations"}:
            return True
        if path.endswith("/press-releases") or path.endswith("/investor-relations"):
            return True
        if path.endswith("/company-page"):
            return True
        if host.endswith("shareprices.com") and path.endswith("/news"):
            return True
        return False

    def search_recent_articles(
        self,
        ticker: str,
        company_name: str | None = None,
        max_results: int = 3,
    ) -> list[dict[str, str]]:
        query_parts = [
            company_name or ticker,
            ticker.replace(".L", ""),
            "shares recent news",
        ]
        results = self._search_duckduckgo(" ".join(query_parts), max_results=max_results * 4)

        articles: list[dict[str, str]] = []
        for result in results:
            if self._is_low_signal_article_result(result["title"], result["url"]):
                continue
            try:
                html = self._fetch_page(result["url"])
            except Exception:
                continue
            summary = self._extract_article_summary(html)
            if not summary:
                continue
            if self._is_low_signal_article_result(result["title"], result["url"], summary):
                continue
            articles.append(
                {
                    "title": result["title"],
                    "url": result["url"],
                    "summary": summary,
                }
            )
            if len(articles) >= max_results:
                break
        return articles

    def find_uk_company_snapshot(self, ticker: str) -> dict[str, Any]:
        target = ticker.removesuffix(".L").upper()
        for path in ("top-gainers", "biggest-losers"):
            for company in self._load_simplywall_market_page(path):
                if (company.get("tickerSymbol") or "").upper() == target:
                    return company
        raise FinanceAPIError(f"Ticker {ticker} was not found in the current UK mover pages.")

    def get_quote(self, ticker: str) -> dict[str, Any]:
        data = self._get(f"quote", symbol=ticker)
        return data[0] if data else {}

    def get_profile(self, ticker: str) -> dict[str, Any]:
        data = self._get("profile", symbol=ticker)
        return data[0] if data else {}

    def get_ratios_ttm(self, ticker: str) -> dict[str, Any]:
        data = self._get("ratios-ttm", symbol=ticker)
        return data[0] if data else {}

    def get_key_metrics_ttm(self, ticker: str) -> dict[str, Any]:
        data = self._get("key-metrics-ttm", symbol=ticker)
        return data[0] if data else {}

    def get_price_change(self, ticker: str) -> dict[str, Any]:
        data = self._get("stock-price-change", symbol=ticker)
        return data[0] if data else {}

    def get_historical_prices(self, ticker: str, interval: str = "day") -> list[dict[str, Any]]:
        from_date = date(date.today().year - 1, 1, 1).isoformat()
        data = self._get("historical-price-eod/full", symbol=ticker, from_=from_date, to=date.today().isoformat())
        if isinstance(data, dict):
            return data.get("historical", [])
        return data or []

    def get_news(self, ticker: str, limit: int = 10) -> list[dict[str, Any]]:
        data = self._get("news/stock", symbols=ticker, limit=limit)
        return data or []

    def get_press_releases(self, ticker: str, limit: int = 10) -> list[dict[str, Any]]:
        data = self._get("news/press-releases", symbols=ticker, limit=limit)
        return data or []

    def get_exchange_quotes(self, exchange: str = "LSE") -> list[dict[str, Any]]:
        data = self._get("batch-exchange-quote", exchange=exchange)
        return data or []

    def build_fact_pack(self, ticker: str) -> FactPack:
        quote = self._get_optional("quote", symbol=ticker)
        quote = quote[0] if isinstance(quote, list) and quote else {}
        profile = self._get_optional("profile", symbol=ticker)
        profile = profile[0] if isinstance(profile, list) and profile else {}
        ratios = self._get_optional("ratios-ttm", symbol=ticker)
        ratios = ratios[0] if isinstance(ratios, list) and ratios else {}
        metrics = self._get_optional("key-metrics-ttm", symbol=ticker)
        metrics = metrics[0] if isinstance(metrics, list) and metrics else {}
        price_change = self._get_optional("stock-price-change", symbol=ticker)
        price_change = price_change[0] if isinstance(price_change, list) and price_change else {}
        prices = self._get_optional("historical-price-eod/full", symbol=ticker, from_=date(date.today().year - 1, 1, 1).isoformat(), to=date.today().isoformat())
        if isinstance(prices, dict):
            prices = prices.get("historical", [])
        prices = prices or []

        if not profile:
            profile = self.find_uk_company_snapshot(ticker)

        closes = [item.get("close") for item in prices if item.get("close") is not None]
        volumes = [item.get("volume") for item in prices if item.get("volume") is not None]

        def pct_change(current: float | None, previous: float | None) -> float | None:
            if current in (None, 0) or previous in (None, 0):
                return None
            return round(((current - previous) / previous) * 100, 2)

        current_price = (
            quote.get("price")
            or profile.get("price")
            or profile.get("sharePrice")
            or (closes[-1] if closes else None)
        )
        five_day_ref = closes[-6] if len(closes) >= 6 else None
        one_month_ref = closes[-22] if len(closes) >= 22 else None
        year_start_ref = None
        one_year_ref = closes[0] if closes else None
        if prices:
            current_year = date.today().year
            for item in prices:
                item_date = item.get("date", "")
                if item_date.startswith(f"{current_year}-"):
                    year_start_ref = item.get("close")
                    break

        avg_volume = round(sum(volumes[-30:]) / min(len(volumes), 30), 2) if volumes else None
        relative_volume = None
        if quote.get("volume") and avg_volume:
            relative_volume = round(quote["volume"] / avg_volume, 2)

        performance = PricePerformance(
            day_change_pct=quote.get("changesPercentage") or ((profile.get("return1D") or 0) * 100 if profile.get("return1D") is not None else None),
            five_day_change_pct=price_change.get("5D") or ((profile.get("return7D") or 0) * 100 if profile.get("return7D") is not None else pct_change(current_price, five_day_ref)),
            one_month_change_pct=price_change.get("1M") or pct_change(current_price, one_month_ref),
            ytd_change_pct=price_change.get("ytd") or pct_change(current_price, year_start_ref),
            one_year_change_pct=price_change.get("1Y") or ((profile.get("return1YrAbs") or 0) * 100 if profile.get("return1YrAbs") is not None else pct_change(current_price, one_year_ref)),
            relative_volume=relative_volume,
            fifty_two_week_low=quote.get("yearLow"),
            fifty_two_week_high=quote.get("yearHigh"),
        )

        stats = StandardStats(
            company_name=profile.get("companyName") or profile.get("legalName") or profile.get("shortName") or quote.get("name"),
            exchange=profile.get("exchangeShortName") or profile.get("exchangeSymbol") or quote.get("exchange"),
            sector=profile.get("sector"),
            industry=profile.get("industry") or profile.get("industryLabel"),
            market_cap=quote.get("marketCap") or profile.get("marketCap"),
            price=current_price,
            dividend_yield=(
                round((profile.get("lastDiv") or 0) / current_price * 100, 2)
                if current_price and profile.get("lastDiv")
                else ratios.get("dividendYielTTM") or ((profile.get("dividendYield") or 0) * 100 if profile.get("dividendYield") is not None else None)
            ),
            pe_ratio=quote.get("pe") or ratios.get("peRatioTTM") or profile.get("bestValuationRatio", {}).get("valuation"),
            forward_pe=metrics.get("forwardPE"),
        )

        return FactPack(
            ticker=ticker,
            performance=performance,
            stats=stats,
            source_notes=[
                "UK mover snapshots and basic valuation fields sourced from Simply Wall St public market pages.",
                "Additional company stats sourced from Financial Modeling Prep when available.",
            ],
        )

    def scan_movers(self, tickers: list[str], min_abs_day_move: float = 4.0) -> list[MoverCandidate]:
        candidates: list[MoverCandidate] = []
        for ticker in tickers:
            quote = self.get_quote(ticker)
            day_change = quote.get("changesPercentage")
            if day_change is None or abs(day_change) < min_abs_day_move:
                continue
            volume = quote.get("volume")
            avg_volume = quote.get("avgVolume")
            rel_volume = (volume / avg_volume) if volume and avg_volume else 1.0
            score = round(abs(day_change) * 0.7 + rel_volume * 0.3, 2)
            candidates.append(
                MoverCandidate(
                    ticker=ticker,
                    company_name=quote.get("name"),
                    price=quote.get("price"),
                    day_change_pct=day_change,
                    volume=volume,
                    avg_volume=avg_volume,
                    score=score,
                )
            )
        return sorted(candidates, key=lambda item: item.score, reverse=True)

    def scan_uk_market(
        self,
        min_abs_day_move: float = 0.0,
        min_price: float = 0.1,
        min_avg_volume: float = 50_000,
        limit: int = 3,
        move_window: str = "1D",
    ) -> list[MoverCandidate]:
        candidates: list[MoverCandidate] = []
        seen: set[str] = set()
        for company in self._load_all_simplywall_market_companies("top-gainers"):
            symbol = self._normalise_simplywall_ticker(company)
            if symbol in seen:
                continue
            seen.add(symbol)

            move_pct = self._market_move_for_window(company, move_window)
            price = company.get("sharePrice")

            if move_pct is None:
                continue
            if min_abs_day_move and abs(move_pct) < min_abs_day_move:
                continue
            if price is not None and price < min_price:
                continue

            score = round(abs(move_pct), 2)
            candidates.append(
                MoverCandidate(
                    ticker=symbol,
                    company_name=company.get("legalName") or company.get("shortName"),
                    price=price,
                    day_change_pct=round(move_pct, 2),
                    volume=None,
                    avg_volume=None,
                    score=score,
                    raw_context=company,
                )
            )

        return sorted(candidates, key=lambda item: item.score, reverse=True)[:limit]
