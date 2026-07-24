import logging
import time
import random
from typing import Optional

import requests

logger = logging.getLogger(__name__)

API_ROOT = "https://ws.audioscrobbler.com/2.0/"
MAX_RETRIES = 2
RETRY_DELAY_SEC = 1
REQUEST_TIMEOUT_SEC = 10


class LastFmError(Exception):
    pass


class LastFmClient:
    def __init__(self, api_key: str, session: Optional[requests.Session] = None):
        if not api_key:
            raise ValueError("API-ключ Last.fm не задан. Проверьте key.txt")
        self.api_key = api_key
        self.session = session or requests.Session()

        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ]
        self.session.headers.update({
            "User-Agent": random.choice(user_agents),
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9,ru;q=0.8,uk;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Referer": "https://www.last.fm/",
            "DNT": "1",
            "Sec-GPC": "1",
        })

    def _request(self, params: dict) -> dict:
        params = {**params, "api_key": self.api_key, "format": "json"}
        time.sleep(0.1)

        last_exc: Optional[Exception] = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = self.session.get(
                    API_ROOT, params=params, timeout=REQUEST_TIMEOUT_SEC
                )

                if response.status_code == 403:
                    logger.error("Ошибка 403 Forbidden. Ваш API ключ вероятно недействителен или заблокирован.")
                    logger.error("Создайте новый ключ на https://www.last.fm/api/account/create")
                    response.raise_for_status()

                response.raise_for_status()
                data = response.json()

                if "error" in data:
                    error_code = data.get("error")
                    error_msg = data.get("message", "Неизвестная ошибка")

                    if error_code == 6:
                        logger.warning("Трек не найден: %s", error_msg)
                    elif error_code == 10:
                        logger.error("Ошибка авторизации: неверный API ключ")
                        raise LastFmError(f"Неверный API ключ: {error_msg}")
                    else:
                        logger.warning("Last.fm API вернул ошибку %s: %s", error_code, error_msg)
                    return data
                return data

            except requests.exceptions.HTTPError as exc:
                last_exc = exc
                if "403" in str(exc):
                    logger.error("403 Forbidden - ключ недействителен.")
                    raise LastFmError("403 Forbidden: недействительный API ключ") from exc

                logger.warning("Попытка %s/%s запроса к Last.fm не удалась: %s", attempt, MAX_RETRIES, exc)
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_DELAY_SEC * attempt)

            except (requests.RequestException, ValueError) as exc:
                last_exc = exc
                logger.warning("Попытка %s/%s запроса к Last.fm не удалась: %s", attempt, MAX_RETRIES, exc)
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_DELAY_SEC * attempt)

        raise LastFmError(f"Не удалось выполнить запрос к Last.fm после {MAX_RETRIES} попыток: {last_exc}")

    def search_track(self, artist: str, track: str) -> Optional[dict]:
        data = self._request({
            "method": "track.search",
            "track": track,
            "artist": artist,
            "limit": 1,
        })
        try:
            matches = data["results"]["trackmatches"]["track"]
        except (KeyError, TypeError):
            return None
        if not matches:
            return None
        first = matches[0] if isinstance(matches, list) else matches
        return {"artist": first["artist"], "name": first["name"]}

    def get_similar_tracks(self, artist: str, track: str, limit: int = 20) -> list[dict]:
        data = self._request({
            "method": "track.getsimilar",
            "artist": artist,
            "track": track,
            "limit": limit,
        })
        try:
            raw = data["similartracks"]["track"]
        except (KeyError, TypeError):
            return []
        if isinstance(raw, dict):
            raw = [raw]
        result = []
        for item in raw:
            try:
                result.append({
                    "artist": item["artist"]["name"],
                    "name": item["name"],
                    "match": float(item.get("match", 0.0)),
                })
            except (KeyError, TypeError, ValueError):
                continue
        return result

    def get_top_tags(self, artist: str, track: str, limit: int = 10) -> list[str]:
        data = self._request({
            "method": "track.gettoptags",
            "artist": artist,
            "track": track,
        })
        try:
            raw = data["toptags"]["tag"]
        except (KeyError, TypeError):
            return []
        if isinstance(raw, dict):
            raw = [raw]
        tags = [t["name"] for t in raw if "name" in t]
        return tags[:limit]

    def get_artist_top_tags(self, artist: str, limit: int = 10) -> list[str]:
        data = self._request({
            "method": "artist.gettoptags",
            "artist": artist,
        })
        try:
            raw = data["toptags"]["tag"]
        except (KeyError, TypeError):
            return []
        if isinstance(raw, dict):
            raw = [raw]
        tags = [t["name"] for t in raw if "name" in t]
        return tags[:limit]