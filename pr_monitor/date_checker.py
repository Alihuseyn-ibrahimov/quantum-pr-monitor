"""
date_checker.py  v2.1
─────────────────────
Dəyişiklik: "RSS pubDate etibarlıdır" strategiyası.

Köhnə davranış:
  Hər link üçün faktiki HTML aç → tarix tap → yoxla.
  Problem: sayt timeout verəndə tarix tapılmır → xəbər atılır.

Yeni davranış (3 mərhələ):
  1. RSS/mənbədən gələn `published` varsa → onu istifadə et (HTML aç)
  2. `published` yoxdursa → HTML-dən tarix çıxarmağa cəhd et
  3. HTML-dən də tapılmırsa → xəbəri QƏBUL ET (atma), "tarix bilinmir" qeyd et
     (Google News `when:24h` parametri artıq filtr edir)

Link yoxlaması:
  - HEAD sorğusu ilə yoxla (4xx → at, timeout → keç)
  - Timeout-da xəbəri at deyil, qəbul et (sayt yavaşdır, amma mövcuddur)
"""

import re
import datetime
import logging
import json
from email.utils import parsedate_to_datetime

log = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════
# 1. TARİX PARSE
# ══════════════════════════════════════════════════════════════
def parse_date(raw: str) -> datetime.datetime | None:
    if not raw:
        return None
    raw = raw.strip()

    # RFC-2822: "Mon, 16 Jun 2025 12:00:00 +0000"
    try:
        dt = parsedate_to_datetime(raw)
        if dt.tzinfo:
            t = dt.utctimetuple()
            return datetime.datetime(*t[:6])
        return dt.replace(tzinfo=None)
    except Exception:
        pass

    # ISO-8601 variantları
    for fmt in (
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M",
        "%Y-%m-%d",
    ):
        try:
            return datetime.datetime.strptime(raw[:len(fmt)], fmt)
        except Exception:
            continue

    # Timezone offset: "2025-06-16T12:00:00+04:00"
    m = re.match(r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})([+-])(\d{2}):(\d{2})", raw)
    if m:
        try:
            naive = datetime.datetime.strptime(m.group(1), "%Y-%m-%dT%H:%M:%S")
            oh, om = int(m.group(3)), int(m.group(4))
            delta = datetime.timedelta(hours=oh, minutes=om)
            return naive - delta if m.group(2) == "+" else naive + delta
        except Exception:
            pass

    return None


def is_within_hours(raw_date: str, hours: int) -> bool:
    dt = parse_date(raw_date)
    if dt is None:
        return False
    cutoff = datetime.datetime.utcnow() - datetime.timedelta(hours=hours)
    return dt >= cutoff


# ══════════════════════════════════════════════════════════════
# 2. HTML-DƏN TARİX ÇIXAR (yalnız ehtiyac olduqda)
# ══════════════════════════════════════════════════════════════
_META_PROPS = [
    "article:published_time", "article:modified_time",
    "og:published_time", "datePublished", "date",
    "pubdate", "DC.date", "DC.Date",
    "publish_date", "published_time", "created", "timestamp",
]
_JSONLD_KEYS = ["datePublished", "dateCreated", "dateModified", "uploadDate", "published"]


def _jsonld_date(html: str) -> str | None:
    for blob in re.findall(
        r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        html, re.DOTALL | re.IGNORECASE
    ):
        try:
            data = json.loads(blob)
            objs = data if isinstance(data, list) else [data]
            for obj in objs:
                if not isinstance(obj, dict):
                    continue
                for k in _JSONLD_KEYS:
                    v = obj.get(k, "")
                    if v and parse_date(v):
                        return v
        except Exception:
            continue
    return None


def _meta_date(soup) -> str | None:
    for prop in _META_PROPS:
        tag = soup.find("meta", property=prop) or soup.find("meta", attrs={"name": prop})
        if tag:
            v = tag.get("content", "").strip()
            if v and parse_date(v):
                return v
    return None


def _time_tag_date(soup) -> str | None:
    for tag in soup.find_all("time", limit=5):
        v = tag.get("datetime", "").strip()
        if v and parse_date(v):
            return v
    return None


def fetch_date_from_page(url: str, safe_get) -> str | None:
    """Faktiki HTML-dən tarix çıxarır. Sürət üçün yalnız head + 20KB oxunur."""
    try:
        resp = safe_get(url)
        if not resp:
            return None
        html = resp.text

        # 1. JSON-LD (bütün sənəddə)
        d = _jsonld_date(html)
        if d:
            return d

        from bs4 import BeautifulSoup
        head_end = html.find("</head>")
        head = html[:head_end + 7] if head_end > 0 else html[:8000]
        soup = BeautifulSoup(head, "html.parser")

        # 2. Meta teqlər
        d = _meta_date(soup)
        if d:
            return d

        # 3. <time datetime>
        body_soup = BeautifulSoup(html[:20000], "html.parser")
        return _time_tag_date(body_soup)

    except Exception as e:
        log.debug(f"fetch_date_from_page xətası: {e}")
        return None


# ══════════════════════════════════════════════════════════════
# 3. ELEMENT VALİDASİYASI
# ══════════════════════════════════════════════════════════════
def validate_and_date_check(item: dict, safe_get, hours_back: int = 24) -> dict | None:
    """
    Qaydalar:
      A. RSS pubDate varsa → onu yoxla (HTML açma)
         - 24 saat içindədirsə → QƏBUL ET
         - Köhnədirsə → AT
      B. pubDate yoxdursa → HTML-dən tarix çıxar
         - Tapıldısa → A kimi yoxla
         - Tapılmadısa → QƏBUL ET (Google News when:24h artıq filtr edir)
      C. Link 4xx verirsə → AT (timeout-da QƏBUL ET)
    """
    url = item.get("link", "")
    if not url or not url.startswith("http"):
        return None

    # ── Link yoxlaması (yalnız açılıb-açılmadığını bil) ─────
    link_ok = _check_link(url)
    if link_ok is False:   # None = bilinmir (timeout), False = 4xx
        log.debug(f"🚫 4xx link atıldı: {url[:70]}")
        return None

    # ── Tarix yoxlaması ─────────────────────────────────────
    pub = item.get("published", "").strip()

    if pub:
        # RSS/mənbədən gələn tarix var → HTML açmadan yoxla
        dt = parse_date(pub)
        if dt is not None:
            cutoff = datetime.datetime.utcnow() - datetime.timedelta(hours=hours_back)
            if dt < cutoff:
                log.debug(f"⏰ Köhnə (RSS tarix): {pub[:16]} | {item.get('title','')[:50]}")
                return None
            # Tarix OK
            return item
        # pub var amma parse edilmir → HTML-ə bax

    # RSS tarixi yox və ya parse uğursuz → HTML-dən cəhd et
    real_date = fetch_date_from_page(url, safe_get)
    if real_date:
        item["published"] = real_date
        dt = parse_date(real_date)
        if dt is not None:
            cutoff = datetime.datetime.utcnow() - datetime.timedelta(hours=hours_back)
            if dt < cutoff:
                log.debug(f"⏰ Köhnə (HTML tarix): {real_date[:16]} | {item.get('title','')[:50]}")
                return None
        return item

    # Heç bir tarix tapılmadı → qəbul et (mənbə artıq filtr edir)
    log.debug(f"📅 Tarix tapılmadı, qəbul edildi: {url[:70]}")
    item["published"] = "bilinmir"
    return item


def _check_link(url: str) -> bool | None:
    """
    True  = link açılır (2xx/3xx)
    False = link 4xx verir → AT
    None  = timeout/bağlantı xətası → QƏBUL ET (sayt mövcuddur)
    """
    import requests as _req
    try:
        r = _req.head(url, timeout=6, allow_redirects=True,
                      headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code >= 400:
            return False
        return True
    except _req.exceptions.Timeout:
        return None   # Timeout → mövcuddur, amma yavaşdır
    except Exception:
        # HEAD dəstəkləmir → GET ilə sına
        try:
            r = _req.get(url, timeout=6,
                         headers={"User-Agent": "Mozilla/5.0"},
                         stream=True)
            r.close()
            return r.status_code < 400
        except _req.exceptions.Timeout:
            return None
        except Exception:
            return None   # Bağlantı xətası → bilinmir, qəbul et


# ══════════════════════════════════════════════════════════════
# 4. TOPLU VALİDASİYA
# ══════════════════════════════════════════════════════════════
def validate_batch(
    items: list[dict],
    safe_get,
    hours_back: int = 24,
    max_workers: int = 6,
) -> list[dict]:
    from concurrent.futures import ThreadPoolExecutor, as_completed

    if not items:
        return []

    valid, dropped = [], 0

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(validate_and_date_check, it, safe_get, hours_back): it
                   for it in items}
        for fut in as_completed(futures):
            try:
                r = fut.result()
                if r:
                    valid.append(r)
                else:
                    dropped += 1
            except Exception:
                dropped += 1

    if dropped:
        log.info(f"🔗 Yoxlama: {len(valid)} keçərli, {dropped} köhnə/4xx atıldı")
    return valid