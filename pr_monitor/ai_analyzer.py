"""
AI Analiz Modulu
Gemini vasitəsilə toplu analiz, rate-limit idarəetməsi
"""

import json
import time
import logging
import google.generativeai as genai
from config import GEMINI_MODEL, AI_BATCH_SIZE, AI_RETRY_WAIT, GEMINI_API_KEY

log = logging.getLogger(__name__)
genai.configure(api_key=GEMINI_API_KEY)
_model = genai.GenerativeModel(GEMINI_MODEL)

SYSTEM_PROMPT = """Sən Azərbaycan hökuməti sosial siyasəti üzrə PR analitik ekspertisən.
Sənə xəbər/post siyahısı veriləcək. Hər biri üçün:
1. Mövzunu müəyyən et
2. Hissiyyatı qiymətləndir: MƏNFİ / MÜSBƏT / NEYTRAL / RİSK
3. 2-3 cümlə ilə xülasə yaz (Azərbaycanca)
4. PR riski 1-10 qiymətləndir (10=ən yüksək risk)

YALNIZ JSON massivi qaytır, başqa heç nə yazma:
[
  {
    "title": "...",
    "link": "...",
    "keyword": "...",
    "source_type": "...",
    "sentiment": "MƏNFİ|MÜSBƏT|NEYTRAL|RİSK",
    "summary": "...",
    "pr_risk": 1-10,
    "action_needed": true/false
  }
]"""


def _call_ai(batch: list[dict]) -> list[dict]:
    """Tək bir batch üçün AI sorğusu."""
    # Lazımsız sahələri çıxar, kontekst boyutunu azalt
    slim = [
        {
            "title":       it.get("title", ""),
            "snippet":     it.get("snippet", "")[:300],
            "link":        it.get("link", ""),
            "keyword":     it.get("keyword", ""),
            "source_type": it.get("source_type", ""),
        }
        for it in batch
    ]

    prompt = f"{SYSTEM_PROMPT}\n\nANALİZ ET:\n{json.dumps(slim, ensure_ascii=False)}"

    try:
        resp = _model.generate_content(prompt)
        raw = resp.text.strip()
        # Markdown code block-ları təmizlə
        raw = raw.replace("```json", "").replace("```", "").strip()
        return json.loads(raw)
    except json.JSONDecodeError as e:
        log.warning(f"AI JSON parse xətası: {e}")
        return _fallback(batch)
    except Exception as e:
        err = str(e)
        if "429" in err or "quota" in err.lower() or "rate" in err.lower():
            log.warning(f"⏳ API limiti! {AI_RETRY_WAIT}s gözlənilir...")
            time.sleep(AI_RETRY_WAIT)
            try:
                resp = _model.generate_content(prompt)
                raw = resp.text.strip().replace("```json", "").replace("```", "").strip()
                return json.loads(raw)
            except Exception as e2:
                log.error(f"Təkrar cəhd uğursuz: {e2}")
                return _fallback(batch)
        else:
            log.error(f"AI xətası: {e}")
            return _fallback(batch)


def _fallback(batch: list[dict]) -> list[dict]:
    """AI uğursuz olduqda standart format qaytarır."""
    return [
        {
            "title":         it.get("title", "Başlıqsız"),
            "link":          it.get("link", "#"),
            "keyword":       it.get("keyword", ""),
            "source_type":   it.get("source_type", ""),
            "sentiment":     "NEYTRAL",
            "summary":       "AI analizi tamamlana bilmədi. Manual yoxlama tövsiyə edilir.",
            "pr_risk":       5,
            "action_needed": True,
        }
        for it in batch
    ]


def analyze_with_ai(items: list[dict]) -> list[dict]:
    """
    Bütün elementləri batch-lərə bölərek analiz edir.
    Rate-limit aşılmaması üçün batch-lər arası fasilə saxlayır.
    """
    if not items:
        return []

    results = []
    total_batches = (len(items) + AI_BATCH_SIZE - 1) // AI_BATCH_SIZE

    for i in range(0, len(items), AI_BATCH_SIZE):
        batch = items[i: i + AI_BATCH_SIZE]
        batch_num = i // AI_BATCH_SIZE + 1
        log.info(f"  🤖 AI batch {batch_num}/{total_batches} ({len(batch)} element)...")

        analyzed = _call_ai(batch)
        results.extend(analyzed)

        # Batches arası qısa fasilə (rate limit üçün)
        if batch_num < total_batches:
            time.sleep(4)

    # Yüksək riskliləri əvvələ gətir
    results.sort(key=lambda x: x.get("pr_risk", 0), reverse=True)
    return results