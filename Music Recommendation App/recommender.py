"""
Агрегация и ранжирование рекомендаций на основе похожих треков,
полученных для каждого трека исходного плейлиста.
"""

import logging
from dataclasses import dataclass

from playlist_parser import Track

logger = logging.getLogger(__name__)


@dataclass
class Recommendation:
    artist: str
    name: str
    score: float

    def key(self) -> tuple[str, str]:
        return (self.artist.strip().lower(), self.name.strip().lower())


def build_recommendations(
    playlist: list[Track],
    similar_by_track: dict[tuple[str, str], list[dict]],
    top_n: int = 15,
) -> list[Recommendation]:
    """
    Агрегирует похожие треки по всему плейлисту в единый ранжированный список.
    """
    playlist_keys = {t.key() for t in playlist}
    aggregated: dict[tuple[str, str], Recommendation] = {}

    for source_key, similar_tracks in similar_by_track.items():
        for item in similar_tracks:
            candidate_key = (item["artist"].strip().lower(), item["name"].strip().lower())

            if candidate_key in playlist_keys:
                continue

            if candidate_key not in aggregated:
                aggregated[candidate_key] = Recommendation(
                    artist=item["artist"],
                    name=item["name"],
                    score=0.0,
                )
            aggregated[candidate_key].score += item.get("match", 0.0)

    ranked = sorted(aggregated.values(), key=lambda r: r.score, reverse=True)
    return ranked[:top_n]