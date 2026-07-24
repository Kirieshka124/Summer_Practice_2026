"""
Экспорт результатов в текстовый файл и вывод в консоль.
"""

from pathlib import Path

from playlist_parser import Track
from recommender import Recommendation


def export_full_report(
    path: Path,
    playlist_name: str,
    playlist_tracks: list[Track],
    recommendations: list[Recommendation],
    top_tags: list[tuple[str, int]],
    total_tracks: int,
    processed_tracks: int,
    skipped_tracks: int,
    not_found_tracks: list[str] = None,
) -> None:
    lines = []

    lines.append(" " * 70)
    lines.append(f"АНАЛИЗ ПЛЕЙЛИСТА: {playlist_name}")
    lines.append(" " * 70)
    lines.append("")

    lines.append("СТАТИСТИКА:")
    lines.append(f"  Всего треков: {total_tracks}")
    lines.append(f"  Обработано: {processed_tracks}")
    lines.append(f"  Пропущено (не найдено): {skipped_tracks}")
    lines.append("")

    if not_found_tracks:
        lines.append("НЕ НАЙДЕННЫЕ ТРЕКИ (проверьте названия):")
        for track_str in not_found_tracks:
            lines.append(f"  - {track_str}")
        lines.append("")

    lines.append("ИСХОДНЫЙ ПЛЕЙЛИСТ:")
    for i, track in enumerate(playlist_tracks, 1):
        lines.append(f"  {i:2}. {track}")
    lines.append("")

    lines.append("ВСЕ ТЕГИ:")
    if top_tags:
        for tag, count in top_tags:
            lines.append(f"  {tag}: {count}")
    else:
        lines.append("  (теги не найдены)")
    lines.append("")

    lines.append("ВСЕ РЕКОМЕНДАЦИИ:")
    if recommendations:
        for i, rec in enumerate(recommendations, 1):
            lines.append(f"  {i:2}. {rec.artist} - {rec.name}  (score: {rec.score:.3f})")
    else:
        lines.append("  (рекомендаций не найдено)")
    lines.append("")

    lines.append(" " * 70)
    lines.append("Сгенерировано Music Recommendation App")
    lines.append(" " * 70)

    path.write_text("\n".join(lines), encoding="utf-8")


def print_summary(recommendations: list[Recommendation], top_tags: list[tuple[str, int]]) -> None:
    print("")
    print("ТОП РЕКОМЕНДАЦИЙ")
    if recommendations:
        for i, rec in enumerate(recommendations[:10], start=1):
            print(f"  {i:2}. {rec.artist} - {rec.name}  (score: {rec.score:.3f})")
    else:
        print("  (рекомендаций не найдено)")

    print("")
    print("ТОП ТЕГОВ")
    if top_tags:
        for tag, count in top_tags[:10]:
            print(f"  {tag}: {count}")
    else:
        print("  (теги не найдены)")
    print("")