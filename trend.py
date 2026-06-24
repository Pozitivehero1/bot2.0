import requests
import re
import logging
from functools import lru_cache
from typing import List

logger = logging.getLogger(__name__)

BINANCE_API = "https://data-api.binance.vision"
_EXCHANGE_INFO = None

@lru_cache(maxsize=1)
def get_exchange_info():
    """Загружает и кэширует информацию о символах."""
    try:
        url = f"{BINANCE_API}/api/v3/exchangeInfo"
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
        r.raise_for_status()
        data = r.json()
        info = {}
        for s in data.get("symbols", []):
            if s.get("status") == "TRADING" and s.get("quoteAsset") == "USDT":
                # Проверяем, что baseAsset состоит из букв
                base = s["baseAsset"]
                if re.match(r'^[A-Z]+$', base):
                    info[s["symbol"]] = base
        return info
    except Exception as e:
        logger.error(f"Failed to load exchangeInfo: {e}")
        return {}

def get_base_asset(symbol):
    info = get_exchange_info()
    base = info.get(symbol)
    if base:
        return base
    # fallback
    if symbol.endswith("USDT"):
        return symbol[:-4]
    return symbol

def get_trending_symbols(limit=100) -> List[str]:
    """Возвращает список символов, отсортированных по объёму и изменению."""
    try:
        url = f"{BINANCE_API}/api/v3/ticker/24hr"
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        logger.error(f"Failed to get tickers: {e}")
        return []
    
    if not isinstance(data, list):
        logger.error(f"Unexpected response format: {data}")
        return []
    
    pairs = []
    for item in data:
        if not isinstance(item, dict):
            continue
        symbol = item.get("symbol")
        if not symbol or not symbol.endswith("USDT"):
            continue
        if not re.match(r'^[A-Z0-9]+USDT$', symbol):
            continue
        try:
            volume = float(item.get("quoteVolume", 0))
            change = float(item.get("priceChangePercent", 0))
            # Добавляем также объём в базовой валюте для надёжности
            base_volume = float(item.get("volume", 0))
            pairs.append({"symbol": symbol, "volume": volume, "change": change, "base_volume": base_volume})
        except (TypeError, ValueError):
            continue
    
    # Сортировка: сначала по абсолютному изменению, затем по объёму
    pairs.sort(key=lambda x: (abs(x["change"]), x["volume"]), reverse=True)
    return [x["symbol"] for x in pairs[:limit]]