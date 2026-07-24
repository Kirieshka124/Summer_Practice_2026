import argparse
import logging
from pathlib import Path

from lastfm_client import LastFmClient, LastFmError
from playlist_parser import parse_playlist, get_playlist_name
from recommender import build_recommendations
from report import export_full_report, print_summary

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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Music Recommendation App")
    parser.add_argument(
        "--playlist", type=str, default=None,
        help="Имя файла с плейлистом в папке playlists/ (например, Liked.txt)",
    )
    parser.add_argument(
        "--top-n", type=int, default=25,
        help="Количество рекомендаций (по умолчанию 25)",
    )
    return parser.parse_args()


def load_api_key() -> str:
    key_file = Path("key.txt")
    if not key_file.exists():
        print("\nФайл key.txt не найден")
        print("Создай файл key.txt в папке с программой")
        print("Запиши в него свой API-ключ от Last.fm (одной строкой)")
        print("Получить ключ: https://www.last.fm/api/account/create")
        exit(1)

    api_key = key_file.read_text(encoding="utf-8").strip()
    if not api_key:
        print("\nФайл key.txt пуст")
        print("Запиши в него свой API-ключ и запусти программу снова")
        exit(1)
    return api_key


def find_playlist_file(playlist_name: str = None) -> Path:
    if playlist_name:
        file_path = PLAYLISTS_DIR / playlist_name
        if not file_path.exists():
            print(f"Файл {playlist_name} не найден в папке {PLAYLISTS_DIR}")
            print("Доступные файлы:")
            for f in PLAYLISTS_DIR.glob("*.txt"):
                print(f"  - {f.name}")
            exit(1)
        return file_path

    txt_files = list(PLAYLISTS_DIR.glob("*.txt"))
    if not txt_files:
        print(f"В папке {PLAYLISTS_DIR} нет .txt файлов")
        print("Добавь туда свой плейлист и запусти программу снова")
        exit(0)
    return txt_files[0]


def aggregate_tags_with_artists(
        tags_by_track: dict,
        tags_by_artist: dict,
        top_n: int = 15
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


def main() -> None:
    setup_logging()
    logger = logging.getLogger("main")

    args = parse_args()

    print("\nMusic Recommendation App")
    print("")

    api_key = load_api_key()
    print("API ключ загружен")

    playlist_path = find_playlist_file(args.playlist)
    playlist_name = get_playlist_name(playlist_path)
    print(f"Плейлист: {playlist_path.name}")
    print(f"Количество рекомендаций: {args.top_n}")
    print("")

    raw_text = playlist_path.read_text(encoding="utf-8")
    playlist = parse_playlist(raw_text)

    if not playlist:
        print("Плейлист пуст или не распознан")
        print("Проверьте формат: каждая строка должна быть 'Исполнитель - Трек'")
        return

    print(f"Распознано треков: {len(playlist)}")
    print("")

    try:
        client = LastFmClient(api_key=api_key)
    except ValueError as exc:
        print(f"Ошибка: {exc}")
        return

    similar_by_track = {}
    tags_by_track = {}
    tags_by_artist = {}
    skipped = 0

    for idx, track in enumerate(playlist, 1):
        print(f"Обработка {idx}/{len(playlist)}: {track}")

        try:
            found = client.search_track(track.artist, track.name)
            if not found:
                print("  Трек не найден в Last.fm, пропускаем")
                skipped += 1
                continue

            similar = client.get_similar_tracks(found["artist"], found["name"])
            similar_by_track[track.key()] = similar

            tags = client.get_top_tags(found["artist"], found["name"])
            tags_by_track[track.key()] = tags

            artist_tags = client.get_artist_top_tags(found["artist"])
            tags_by_artist[found["artist"].lower()] = artist_tags

            print(f"  Похожих: {len(similar)}, тегов у трека: {len(tags)}, тегов у исполнителя: {len(artist_tags)}")

        except LastFmError as exc:
            print(f"  Ошибка API: {exc}")
            skipped += 1
            continue

    print("")
    print("СТАТИСТИКА ОБРАБОТКИ")
    print(f"  Всего треков в плейлисте: {len(playlist)}")
    print(f"  Успешно обработано: {len(playlist) - skipped}")
    print(f"  Пропущено: {skipped}")
    print("")

    recommendations = build_recommendations(playlist, similar_by_track, top_n=args.top_n)
    top_tags = aggregate_tags_with_artists(tags_by_track, tags_by_artist, top_n=15)

    print_summary(recommendations, top_tags)

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
    )

    print("")
    print("Готово. Результат сохранен в:")
    print(f"{output_path}")
    print("")


if __name__ == "__main__":
    main()