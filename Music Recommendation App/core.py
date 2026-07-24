import logging
from pathlib import Path

from lastfm_client import LastFmClient, LastFmError
from playlist_parser import parse_playlist, get_playlist_name
from recommender import build_recommendations
from report import export_full_report

PLAYLISTS_DIR = Path("playlists")
OUTPUT_DIR = Path("output")


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler("app.log", encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


def load_api_key() -> str:
    key_file = Path("key.txt")
    if not key_file.exists():
        raise FileNotFoundError("Файл key.txt не найден. Создайте файл с API-ключом.")

    api_key = key_file.read_text(encoding="utf-8").strip()
    if not api_key:
        raise ValueError("Файл key.txt пуст. Запишите в него API-ключ.")
    return api_key


def aggregate_tags_with_artists(
        tags_by_track: dict,
        tags_by_artist: dict,
        top_n: int = 50
) -> list[tuple[str, int]]:
    from collections import defaultdict
    counter = defaultdict(int)

    for tags in tags_by_track.values():
        for tag in tags:
            counter[tag.lower()] += 2

    for tags in tags_by_artist.values():
        for tag in tags:
            counter[tag.lower()] += 1

    sorted_tags = sorted(counter.items(), key=lambda x: x[1], reverse=True)
    return sorted_tags[:top_n]


def process_playlist(playlist_path: Path, top_n: int = 25, log_callback=None) -> dict:
    setup_logging()

    def log(message: str):
        if log_callback:
            log_callback(message)
        else:
            print(message)

    playlist_name = get_playlist_name(playlist_path)

    log("Чтение файла плейлиста...")
    raw_text = playlist_path.read_text(encoding="utf-8")
    playlist, skipped_lines = parse_playlist(raw_text, log_callback=log_callback)

    if skipped_lines:
        log(f"Обнаружено строк с ошибками формата: {len(skipped_lines)}")

    if not playlist:
        return {
            "error": "Плейлист пуст или не распознан. Проверьте формат 'Исполнитель - Название'.",
            "playlist_name": playlist_name,
            "playlist": [],
            "skipped_lines": skipped_lines,
            "recommendations": [],
            "tags": [],
            "stats": {}
        }

    log(f"Распознано треков: {len(playlist)}")

    try:
        api_key = load_api_key()
        client = LastFmClient(api_key=api_key)
        log("API ключ загружен")
    except (FileNotFoundError, ValueError) as exc:
        return {
            "error": f"Ошибка загрузки API ключа: {exc}",
            "playlist_name": playlist_name,
            "playlist": playlist,
            "skipped_lines": skipped_lines,
            "recommendations": [],
            "tags": [],
            "stats": {}
        }
    except Exception as exc:
        return {
            "error": f"Неизвестная ошибка при загрузке API ключа: {exc}",
            "playlist_name": playlist_name,
            "playlist": playlist,
            "skipped_lines": skipped_lines,
            "recommendations": [],
            "tags": [],
            "stats": {}
        }

    similar_by_track = {}
    tags_by_track = {}
    tags_by_artist = {}
    skipped = 0
    not_found_tracks = []  # Для сбора треков, которые не найдены

    log("")
    log("Начало обработки треков:")

    for idx, track in enumerate(playlist, 1):
        log(f"  {idx}/{len(playlist)}: {track}")

        try:
            found = client.search_track(track.artist, track.name)
            if not found:
                not_found_tracks.append(str(track))
                log(f"    Трек не найден в Last.fm. Проверьте название: '{track}'")
                skipped += 1
                continue

            similar = client.get_similar_tracks(found["artist"], found["name"])
            similar_by_track[track.key()] = similar

            tags = client.get_top_tags(found["artist"], found["name"])
            tags_by_track[track.key()] = tags

            artist_tags = client.get_artist_top_tags(found["artist"])
            tags_by_artist[found["artist"].lower()] = artist_tags

            log(f"    Похожих: {len(similar)}, тегов у трека: {len(tags)}, тегов у исполнителя: {len(artist_tags)}")

        except LastFmError as exc:
            log(f"    Ошибка API: {exc}")
            skipped += 1
            continue
        except Exception as exc:
            log(f"    Неизвестная ошибка: {exc}")
            skipped += 1
            continue

    # Если есть не найденные треки, выводим отдельное сообщение
    if not_found_tracks:
        log("")
        log(" " * 60)
        log("ВНИМАНИЕ: Следующие треки не найдены в Last.fm")
        log(" " * 60)
        for track_str in not_found_tracks:
            log(f"  {track_str}")
        log("")
        log("Возможные причины:")
        log("  - Опечатка в названии трека или исполнителя")
        log("  - Трек отсутствует в базе Last.fm")
        log("  - Неправильный формат записи (нужно 'Исполнитель - Название')")
        log(" " * 60)
        log("")

    log("")
    log("Построение рекомендаций...")
    recommendations = build_recommendations(playlist, similar_by_track, top_n=top_n)
    log(f"Сформировано рекомендаций: {len(recommendations)}")

    log("Агрегация тегов...")
    top_tags = aggregate_tags_with_artists(tags_by_track, tags_by_artist, top_n=50)

    log("Сохранение результата...")
    output_path = OUTPUT_DIR / f"{playlist_name}_music_recommendations.txt"
    OUTPUT_DIR.mkdir(exist_ok=True)

    export_full_report(
        path=output_path,
        playlist_name=playlist_name,
        playlist_tracks=playlist,
        recommendations=recommendations,
        top_tags=top_tags,
        total_tracks=len(playlist),
        processed_tracks=len(playlist) - skipped,
        skipped_tracks=skipped,
        not_found_tracks=not_found_tracks,
    )

    return {
        "playlist_name": playlist_name,
        "playlist": playlist,
        "skipped_lines": skipped_lines,
        "recommendations": recommendations,
        "tags": top_tags,
        "not_found_tracks": not_found_tracks,
        "stats": {
            "total": len(playlist),
            "processed": len(playlist) - skipped,
            "skipped": skipped,
        },
        "output_file": f"{playlist_name}_music_recommendations.txt"
    }