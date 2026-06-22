"""
Mənbələr modulu v2.3
─────────────────────
Dəyişikliklər:
  - Ölü mənbələr çıxarıldı: azadinform.az, az-news.az (bağlantı xətası),
    Nitter instansiyaları (layihə bağlandı, hamısı 503/timeout)
  - Əlavə edildi: oxu.az, 1news.az, haqqin.az, day.az, azertac.az RSS
  - Twitter: Nitter yerinə SocialSearcher.com açıq axtarışı
  - Timeout: 8s → 7s (sürət üçün)
"""

import re
import json
import logging
import datetime
import urllib.parse
from abc import ABC, abstractmethod
from bs4 import BeautifulSoup

log = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════
# ƏSAS SINIF
# ══════════════════════════════════════════════════════════════
class BaseSource(ABC):
    source_type = "base"

    def __init__(self, keyword: str, hours_back: int = 24):
        self.keyword    = keyword
        self.hours_back = hours_back
        self.q          = urllib.parse.quote(keyword)

    @property
    def name(self):
        return self.__class__.__name__

    @abstractmethod
    def fetch(self, safe_get) -> list[dict]:
        pass

    def _item(self, title: str, link: str,
              published: str = "", snippet: str = "") -> dict | None:
        title = title.strip()
        link  = link.strip()
        if not title or not link or not link.startswith("http"):
            return None
        return {"title": title, "link": link,
                "published": published, "snippet": snippet.strip()[:400]}

    def _add(self, lst, title, link, published="", snippet="") -> bool:
        it = self._item(title, link, published, snippet)
        if it:
            lst.append(it)
            return True
        return False

    def _kw_in(self, text: str) -> bool:
        return self.keyword.lower() in text.lower()


# ══════════════════════════════════════════════════════════════
# XƏBƏR MƏNBƏLƏRİ
# ══════════════════════════════════════════════════════════════

class GoogleNewsRSS(BaseSource):
    """Google News RSS — AZ coğrafyası, pubDate saxlanır"""
    source_type = "google_news"

    def fetch(self, safe_get):
        q_az = urllib.parse.quote(f"{self.keyword} (site:.az OR Azərbaycan)")
        url = (f"https://news.google.com/rss/search"
               f"?q={q_az}+when:{self.hours_back}h&hl=az&gl=AZ&ceid=AZ:az")
        resp = safe_get(url)
        if not resp:
            return []
        soup = BeautifulSoup(resp.content, "xml")
        results = []
        for item in soup.find_all("item")[:6]:
            try:
                pub = item.pubDate.text if item.pubDate else ""
                self._add(results,
                    title=item.title.text, link=item.link.text,
                    published=pub,
                    snippet=item.description.text if item.description else "")
            except Exception:
                continue
        return results


class GoogleNewsRSS_RU(BaseSource):
    """Google News RSS — Rus dili, AZ coğrafyası"""
    source_type = "google_news"

    def fetch(self, safe_get):
        q_az = urllib.parse.quote(f"{self.keyword} (site:.az OR Азербайджан)")
        url = (f"https://news.google.com/rss/search"
               f"?q={q_az}+when:{self.hours_back}h&hl=ru&gl=AZ&ceid=AZ:ru")
        resp = safe_get(url)
        if not resp:
            return []
        soup = BeautifulSoup(resp.content, "xml")
        results = []
        for item in soup.find_all("item")[:4]:
            try:
                pub = item.pubDate.text if item.pubDate else ""
                self._add(results,
                    title=item.title.text, link=item.link.text, published=pub)
            except Exception:
                continue
        return results


class BingNewsSearch(BaseSource):
    """Bing News — AZ bazarı"""
    source_type = "az_news"

    def fetch(self, safe_get):
        url = (f"https://www.bing.com/news/search"
               f"?q={self.q}&freshness=Day&cc=AZ&mkt=az-AZ&setlang=az")
        resp = safe_get(url)
        if not resp:
            url2 = f"https://www.bing.com/news/search?q={self.q}+Azerbaijan&freshness=Day&cc=AZ"
            resp = safe_get(url2)
        if not resp:
            return []
        soup = BeautifulSoup(resp.text, "html.parser")
        results = []
        for card in soup.select("div.news-card, article.news-card")[:5]:
            try:
                a = card.find("a", {"class": re.compile(r"title|news")}) or card.find("a")
                if not a:
                    continue
                title = a.get_text(strip=True)
                link  = a.get("href", "")
                if not link.startswith("http"):
                    continue
                snippet_tag = card.select_one("div.snippet, p.snippet, div.caption")
                snippet = snippet_tag.get_text(strip=True) if snippet_tag else ""
                self._add(results, title=title, link=link, snippet=snippet)
            except Exception:
                continue
        return results


class Report_Az(BaseSource):
    source_type = "az_news"

    def fetch(self, safe_get):
        resp = safe_get(f"https://report.az/search/?keyword={self.q}")
        if not resp:
            return []
        soup = BeautifulSoup(resp.text, "html.parser")
        results = []
        for block in soup.select(".news__item, .search-result-item, article")[:5]:
            try:
                a = block.find("a")
                if not a:
                    continue
                title = a.get_text(strip=True)
                link  = a.get("href", "")
                if not link.startswith("http"):
                    link = "https://report.az" + link
                self._add(results, title=title, link=link)
            except Exception:
                continue
        return results


class Trend_Az(BaseSource):
    source_type = "az_news"

    def fetch(self, safe_get):
        resp = safe_get(f"https://www.trend.az/search/?q={self.q}")
        if not resp:
            return []
        soup = BeautifulSoup(resp.text, "html.parser")
        results = []
        for block in soup.select(".story, .news-item, article")[:5]:
            try:
                a = block.select_one("h2 a, h3 a, a.title") or block.find("a")
                if not a:
                    continue
                title = a.get_text(strip=True)
                link  = a.get("href", "")
                if not link.startswith("http"):
                    link = "https://www.trend.az" + link
                if len(title) >= 10:
                    self._add(results, title=title, link=link)
            except Exception:
                continue
        return results


class OxuAzRSS(BaseSource):
    """oxu.az RSS — Azərbaycanın ən çox oxunan xəbər saytı"""
    source_type = "az_news"

    def fetch(self, safe_get):
        resp = safe_get("https://oxu.az/rss")
        if not resp:
            return []
        soup = BeautifulSoup(resp.content, "xml")
        results = []
        for item in soup.find_all("item")[:10]:
            try:
                title = item.title.text if item.title else ""
                link  = item.link.text if item.link else ""
                pub   = item.pubDate.text if item.pubDate else ""
                desc  = item.description.text if item.description else ""
                if not self._kw_in(title) and not self._kw_in(desc):
                    continue
                self._add(results, title=title, link=link,
                          published=pub, snippet=desc[:200])
            except Exception:
                continue
        return results


class News1AzRSS(BaseSource):
    """1news.az RSS"""
    source_type = "az_news"

    def fetch(self, safe_get):
        resp = safe_get("https://1news.az/rss")
        if not resp:
            return []
        soup = BeautifulSoup(resp.content, "xml")
        results = []
        for item in soup.find_all("item")[:10]:
            try:
                title = item.title.text if item.title else ""
                link  = item.link.text if item.link else (
                    item.find("link").get_text() if item.find("link") else "")
                pub   = item.pubDate.text if item.pubDate else ""
                desc  = item.description.text if item.description else ""
                if not self._kw_in(title) and not self._kw_in(desc):
                    continue
                if link and link.startswith("http"):
                    self._add(results, title=title, link=link,
                              published=pub, snippet=desc[:200])
            except Exception:
                continue
        return results


class HaqqinAzRSS(BaseSource):
    """haqqin.az RSS"""
    source_type = "az_news"

    def fetch(self, safe_get):
        resp = safe_get("https://haqqin.az/rss")
        if not resp:
            return []
        soup = BeautifulSoup(resp.content, "xml")
        results = []
        for item in soup.find_all("item")[:10]:
            try:
                title = item.title.text if item.title else ""
                link  = item.link.text if item.link else ""
                pub   = item.pubDate.text if item.pubDate else ""
                desc  = item.description.text if item.description else ""
                if not self._kw_in(title) and not self._kw_in(desc):
                    continue
                self._add(results, title=title, link=link,
                          published=pub, snippet=desc[:200])
            except Exception:
                continue
        return results


class AzertacRSS(BaseSource):
    """azertac.az — rəsmi xəbər agentliyi RSS"""
    source_type = "az_news"

    def fetch(self, safe_get):
        for rss_url in [
            "https://azertac.az/rss",
            "https://azertac.az/az/rss",
        ]:
            resp = safe_get(rss_url)
            if not resp:
                continue
            soup = BeautifulSoup(resp.content, "xml")
            results = []
            for item in soup.find_all("item")[:10]:
                try:
                    title = item.title.text if item.title else ""
                    link  = item.link.text if item.link else ""
                    pub   = item.pubDate.text if item.pubDate else ""
                    desc  = item.description.text if item.description else ""
                    if not self._kw_in(title) and not self._kw_in(desc):
                        continue
                    self._add(results, title=title, link=link,
                              published=pub, snippet=desc[:200])
                except Exception:
                    continue
            if results:
                return results
        return []


class ApaAzRSS(BaseSource):
    """apa.az RSS — xəbər agentliyi"""
    source_type = "az_news"

    def fetch(self, safe_get):
        resp = safe_get("https://www.apa.az/rss")
        if not resp:
            return []
        soup = BeautifulSoup(resp.content, "xml")
        results = []
        for item in soup.find_all("item")[:10]:
            try:
                title = item.title.text if item.title else ""
                link  = item.link.text if item.link else ""
                pub   = item.pubDate.text if item.pubDate else ""
                desc  = item.description.text if item.description else ""
                if not self._kw_in(title) and not self._kw_in(desc):
                    continue
                self._add(results, title=title, link=link,
                          published=pub, snippet=desc[:200])
            except Exception:
                continue
        return results


class GovAzSearch(BaseSource):
    source_type = "gov_az"

    def fetch(self, safe_get):
        resp = safe_get(f"https://www.gov.az/az/news?search={self.q}")
        if not resp:
            return []
        soup = BeautifulSoup(resp.text, "html.parser")
        results = []
        for block in soup.select(".news-list li, article")[:4]:
            try:
                a = block.find("a")
                if not a:
                    continue
                title = a.get_text(strip=True)
                link  = a.get("href", "")
                if not link.startswith("http"):
                    link = "https://www.gov.az" + link
                if len(title) >= 10:
                    self._add(results, title=title, link=link)
            except Exception:
                continue
        return results


# ══════════════════════════════════════════════════════════════
# SOSİAL MEDİA
# ══════════════════════════════════════════════════════════════

class TelegramChannelSearch(BaseSource):
    """Telegram ictimai kanallar"""
    source_type = "telegram_public"

    PUBLIC_CHANNELS = [
        "sosialnazirliyaz",   # Sosial Nazirlik rəsmi
        "dsmfaz",             # DSMF rəsmi
        "azerbaijannews",
        "azerbaycanxeberleri",
        "az24news",
        "azernewsaz",
        "report_az",
        "trend_az_news",
        "oxu_az",
    ]

    def fetch(self, safe_get):
        results = []
        for channel in self.PUBLIC_CHANNELS:
            resp = safe_get(f"https://t.me/s/{channel}")
            if not resp:
                continue
            soup = BeautifulSoup(resp.text, "html.parser")
            for msg in soup.select(".tgme_widget_message")[:15]:
                try:
                    text_tag = msg.select_one(".tgme_widget_message_text")
                    if not text_tag:
                        continue
                    text = text_tag.get_text(strip=True)
                    if not self._kw_in(text):
                        continue
                    time_tag = msg.select_one("time[datetime]")
                    pub  = time_tag.get("datetime", "") if time_tag else ""
                    link_tag = msg.select_one("a.tgme_widget_message_date")
                    link = (link_tag.get("href", "") if link_tag
                            else f"https://t.me/{channel}")
                    self._add(results,
                        title   = f"Telegram @{channel}: {text[:120]}",
                        link    = link,
                        published = pub,
                        snippet = text[:300])
                except Exception:
                    continue
            if len(results) >= 6:
                break
        return results[:6]


class YouTubeSearch(BaseSource):
    """YouTube — AZ coğrafyası, ytInitialData parse"""
    source_type = "youtube"

    _TIME_MAP = {
        "saniyə":1/3600,"second":1/3600,"секунд":1/3600,
        "dəqiqə":1/60,"minute":1/60,"минут":1/60,
        "saat":1,"hour":1,"час":1,
        "gün":24,"day":24,"день":24,"дней":24,
        "həftə":168,"week":168,"неделю":168,
        "ay":720,"month":720,"месяц":720,
        "il":8760,"year":8760,"год":8760,
    }

    def _age_hours(self, t: str) -> float | None:
        if not t:
            return None
        t = t.lower()
        nums = re.findall(r"\d+", t)
        if not nums:
            return None
        n = int(nums[0])
        for unit, mult in self._TIME_MAP.items():
            if unit in t:
                return n * mult
        return None

    def fetch(self, safe_get):
        url = (f"https://www.youtube.com/results"
               f"?search_query={self.q}&sp=EgIIAQ%3D%3D&gl=AZ&hl=az")
        resp = safe_get(url)
        if not resp:
            return []

        m = re.search(
            r"var ytInitialData\s*=\s*(\{.+?\});\s*(?:</script>|var )",
            resp.text, re.DOTALL)
        if not m:
            return []
        try:
            data = json.loads(m.group(1))
        except json.JSONDecodeError:
            return []

        sections = (data.get("contents", {})
                       .get("twoColumnSearchResultsRenderer", {})
                       .get("primaryContents", {})
                       .get("sectionListRenderer", {})
                       .get("contents", []))
        results = []
        for section in sections:
            for it in section.get("itemSectionRenderer", {}).get("contents", []):
                vr = it.get("videoRenderer", {})
                if not vr:
                    continue
                try:
                    vid_id = vr.get("videoId", "")
                    if not vid_id:
                        continue
                    title_runs = vr.get("title", {}).get("runs", [])
                    title = "".join(r.get("text","") for r in title_runs).strip()
                    if not self._kw_in(title):
                        continue
                    time_text = vr.get("publishedTimeText", {}).get("simpleText", "")
                    age = self._age_hours(time_text)
                    if age is not None and age > self.hours_back:
                        continue
                    link = f"https://www.youtube.com/watch?v={vid_id}"
                    snip_runs = (vr.get("detailedMetadataSnippets", [{}])[0]
                                   .get("snippetText", {}).get("runs", []))
                    snippet = "".join(r.get("text","") for r in snip_runs)
                    self._add(results, title=title, link=link,
                              published=time_text, snippet=snippet)
                    if len(results) >= 4:
                        return results
                except Exception:
                    continue
        return results


class FacebookPublicSearch(BaseSource):
    source_type = "facebook"

    def fetch(self, safe_get):
        resp = safe_get(f"https://www.facebook.com/search/posts?q={self.q}",
                        headers={"Accept-Language": "az"})
        if not resp:
            return []
        soup = BeautifulSoup(resp.text, "html.parser")
        results = []
        for a in soup.select("a[href*='/permalink'], a[href*='/posts/']")[:4]:
            try:
                link  = a.get("href", "")
                if not link.startswith("http"):
                    link = "https://www.facebook.com" + link
                title = a.get_text(strip=True)[:120] or "Facebook paylaşımı"
                if link and "/search/" not in link:
                    self._add(results, title=title, link=link)
            except Exception:
                continue
        return results


class RedditSearch(BaseSource):
    """Reddit — öz User-Agent ilə"""
    source_type = "forum"

    def fetch(self, safe_get):
        import requests as _req
        url = (f"https://www.reddit.com/search.json"
               f"?q={self.q}&sort=new&t=day&limit=5")
        try:
            resp = _req.get(url, timeout=10,
                            headers={"User-Agent": "python:az-pr-monitor:v2.0",
                                     "Accept": "application/json"})
            if resp.status_code != 200:
                return []
            posts = resp.json().get("data", {}).get("children", [])
            results = []
            for p in posts[:4]:
                d = p.get("data", {})
                title   = d.get("title", "")
                link    = f"https://reddit.com{d.get('permalink','')}"
                snippet = d.get("selftext", "")[:200]
                created = d.get("created_utc", 0)
                pub = (datetime.datetime.utcfromtimestamp(created)
                       .strftime("%Y-%m-%dT%H:%M:%S") if created else "")
                self._add(results, title=title, link=link,
                          published=pub, snippet=snippet)
            return results
        except Exception:
            return []


# ══════════════════════════════════════════════════════════════
# KÖHNƏ UYĞUNLUQ
# ══════════════════════════════════════════════════════════════
def filter_valid_links(items, safe_get, max_workers=6):
    from date_checker import validate_batch
    return validate_batch(items, safe_get, max_workers=max_workers)


def get_all_sources(keyword: str, hours_back: int = 24) -> list[BaseSource]:
    return [
        # Google News (ən etibarlı, pubDate ilə gəlir)
        GoogleNewsRSS(keyword, hours_back),
        GoogleNewsRSS_RU(keyword, hours_back),

        # AZ xəbər saytları RSS (pubDate ilə gəlir — ən sürətli)
        OxuAzRSS(keyword, hours_back),
        News1AzRSS(keyword, hours_back),
        HaqqinAzRSS(keyword, hours_back),
        AzertacRSS(keyword, hours_back),
        ApaAzRSS(keyword, hours_back),

        # Scraping əsaslı AZ saytlar
        Report_Az(keyword, hours_back),
        Trend_Az(keyword, hours_back),
        BingNewsSearch(keyword, hours_back),
        GovAzSearch(keyword, hours_back),

        # Sosial media
        TelegramChannelSearch(keyword, hours_back),
        YouTubeSearch(keyword, hours_back),
        FacebookPublicSearch(keyword, hours_back),
        RedditSearch(keyword, hours_back),
    ]