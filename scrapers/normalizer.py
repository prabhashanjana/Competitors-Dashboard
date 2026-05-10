import sys
from dotenv import load_dotenv
from loguru import logger

load_dotenv()
logger.add("app.log", rotation="1 week")


def normalize_results(records: list[dict]) -> list[dict]:
    normalized = []

    for record in records:
        try:
            clean = {
                "product_id":     _clean_str(record.get("product_id")),
                "product_name":   _clean_str(record.get("product_name")),
                "price":          _clean_float(record.get("price")),
                "original_price": _clean_float(record.get("original_price")),
                "discount_pct":   _clean_float(record.get("discount_pct")),
                "rating":         _clean_float(record.get("rating")),
                "review_count":   _clean_int(record.get("review_count")),
                "platform":       _clean_str(record.get("platform")),
                "currency":       _clean_str(record.get("currency")),
                "url":            _clean_str(record.get("url")),
                "keyword":        _clean_str(record.get("keyword")),
                "scraped_at":     _clean_str(record.get("scraped_at")),
            }

            if not clean["product_id"] or not clean["product_name"]:
                logger.warning(
                    f"[normalizer] skipping record — missing id or name")
                continue

            normalized.append(clean)

        except Exception as e:
            logger.warning(f"[normalizer] record failed: {e}")
            continue

    logger.info(
        f"[normalizer] {len(normalized)} clean records from {len(records)} raw")
    return normalized


def _clean_str(value) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _clean_float(value) -> float:
    try:
        return round(float(str(value).replace(",", "").strip()), 2)
    except Exception:
        return 0.0


def _clean_int(value) -> int:
    try:
        return int(str(value).replace(",", "").strip())
    except Exception:
        return 0
