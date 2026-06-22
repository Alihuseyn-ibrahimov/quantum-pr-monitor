"""
az_filter.py — Azərbaycan sferası filtri

Hər mənbədən gələn xəbərin həqiqətən Azərbaycana aid olduğunu
üç səviyyədə yoxlayır:

  1. DOMEN yoxlaması  → .az domenimi?
  2. COĞRAFYA yoxlaması → URL/başlıqda AZ göstəricisi varmı?
  3. DİL/MƏZMUN yoxlaması → Azərbaycan/Bakı/AZ sözləri varmı?

Yalnız sosial media linkləri (t.me, youtube, facebook, twitter)
domen yoxlamasından keçirilmir — onlar üçün məzmun yoxlaması edilir.
"""

import re
import logging

log = logging.getLogger(__name__)

# ── .az domenləri (tam siyahı) ────────────────────────────────
AZ_DOMAINS = {
    # Xəbər
    "report.az", "trend.az", "azertag.az", "apa.az",
    "oxu.az", "1news.az", "haqqin.az", "musavat.com",
    "525.az", "olaylar.az", "yeni.az", "xalqqazeti.az",
    "azernews.az", "azerbaijan24.com", "az24.news",
    "azertac.az", "day.az", "modern.az", "milli.az",
    "az-news.az", "azadinform.az", "caliber.az",
    "aztv.az", "ictimai.tv", "cbc.az", "aze.az",
    "news.mia.az", "mincom.gov.az",
    # Hökumət
    "gov.az", "e-gov.az", "cabmin.gov.az",
    "president.az", "meclis.gov.az", "ombudsman.gov.az",
    "maliyye.gov.az", "economy.gov.az", "taxes.gov.az",
    "sosial.gov.az", "mlspp.gov.az", "dsmf.gov.az",
    "dost.gov.az", "labour.gov.az", "sxta.gov.az",
    "dtsx.gov.az", "azerbaijan.az",
    # Forum/sosial
    "forum.az", "baku.ws",
}

# ── Azərbaycan coğrafya siqnalları ───────────────────────────
# NOT: \b word boundary unicode hərflərlə işləmir,
#      ona görə lookahead/lookbehind əvəzinə sadə case-insensitive axtarış
AZ_GEO_PATTERNS = re.compile(
    r"azerbaij|azərbaycan|azərb|azerbaycan"
    r"|bakı|baku"
    r"|naxçıvan|gəncə|sumqayıt|mingəçevir"
    r"|lənkəran|şirvan|şəki|quba|xəzər"
    r"|дербент|баку|азербайджан"
    r"|\.az/|\.az$|\(az\)"
    r"|azertag|azərtac|azertac",
    re.IGNORECASE
)

# ── Sosial media domenləri — domen yoxlaması tətbiq edilmir ──
SOCIAL_DOMAINS = {
    "t.me", "telegram.me",
    "youtube.com", "youtu.be",
    "facebook.com", "fb.com",
    "twitter.com", "x.com",
    "instagram.com", "picuki.com",
    "reddit.com",
    "nitter.net", "nitter.privacydev.net",
    "nitter.poast.org", "nitter.1d4.us",
}

# ── Google News redirect domenləri ───────────────────────────
GNEWS_DOMAINS = {"news.google.com", "news.google.az"}


def _domain(url: str) -> str:
    """URL-dən domenin əsas hissəsini çıxarır."""
    try:
        from urllib.parse import urlparse
        host = urlparse(url).netloc.lower()
        # www. prefiksini sil
        return host.removeprefix("www.")
    except Exception:
        return ""


def is_az_domain(url: str) -> bool:
    """Link birbaşa .az domenlərindəndirsə True."""
    d = _domain(url)
    if d in AZ_DOMAINS:
        return True
    # alt domenli .az saytlar: sosial.gov.az, dost.gov.az və s.
    if d.endswith(".az") or d.endswith(".gov.az"):
        return True
    return False


def is_social(url: str) -> bool:
    """Link sosial media platformasındandırsa True."""
    d = _domain(url)
    return any(d == s or d.endswith("." + s) for s in SOCIAL_DOMAINS)


def is_gnews(url: str) -> bool:
    """Google News redirect linki?"""
    return _domain(url) in GNEWS_DOMAINS


def has_az_signal(title: str, snippet: str = "", url: str = "") -> bool:
    """
    Başlıq, snippet və ya URL-də Azərbaycan coğrafya siqnalı varmı?
    Sosial media postları üçün istifadə olunur.
    """
    text = f"{title} {snippet} {url}"
    return bool(AZ_GEO_PATTERNS.search(text))


def filter_az(items: list[dict]) -> list[dict]:
    """
    Elementlər siyahısını Azərbaycan sfrasına aid olanlarla məhdudlaşdırır.

    Qaydalar:
      • .az domenli link           → qəbul et (həmişə AZ sferası)
      • Google News redirect        → qəbul et (gl=AZ ilə sorğu edildi)
      • Sosial media linki          → başlıq/snippet-də AZ siqnalı varsa qəbul et
      • Digər xarici domain (.com/.ru/.org/...)
            → başlıq+snippet-də AZ siqnalı varsa qəbul et, yoxsa at
    """
    valid   = []
    dropped = 0

    for it in items:
        url     = it.get("link", "")
        title   = it.get("title", "")
        snippet = it.get("snippet", "")

        # .az domenli → birbaşa keçir
        if is_az_domain(url):
            valid.append(it)
            continue

        # Google News → keçir (AZ coğrafyası ilə sorğu edildi)
        if is_gnews(url):
            valid.append(it)
            continue

        # Sosial media → AZ siqnalı lazımdır
        if is_social(url):
            if has_az_signal(title, snippet, url):
                valid.append(it)
            else:
                log.debug(f"🌍 Sosial (AZ siqnalı yox): {title[:50]}")
                dropped += 1
            continue

        # Xarici domen (.com, .ru, .org...) → AZ siqnalı lazımdır
        if has_az_signal(title, snippet, url):
            valid.append(it)
        else:
            log.debug(f"🌍 Xarici domen, AZ siqnalı yox: {_domain(url)} | {title[:50]}")
            dropped += 1

    if dropped:
        log.info(f"🌍 AZ filteri: {len(valid)} qaldı, {dropped} xarici atıldı")

    return valid