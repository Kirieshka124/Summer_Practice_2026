import logging
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Track:
    artist: str
    name: str

    def key(self) -> tuple[str, str]:
        return (self.artist.strip().lower(), self.name.strip().lower())

    def __str__(self) -> str:
        return f"{self.artist} - {self.name}"


def split_artists(artist_str: str) -> list[str]:
    """
    Разбивает строку с несколькими исполнителями на список.
    Поддерживает разделители: ", ", " & ", " feat. ", " featuring "
    """
    import re

    # Убираем лишние пробелы
    artist_str = artist_str.strip()

    # Заменяем все разделители на запятую для единообразия
    for sep in [" feat. ", " featuring ", " & ", " + "]:
        artist_str = artist_str.replace(sep, ", ")

    # Разбиваем по запятой
    artists = [a.strip() for a in artist_str.split(",") if a.strip()]

    # Если после разбиения ничего не осталось, возвращаем исходную строку
    if not artists:
        return [artist_str]

    return artists


def parse_playlist(raw_text: str, log_callback=None) -> tuple[list[Track], list[tuple[int, str, str]]]:
    """
    Разбирает многострочный текст плейлиста в список Track.
    Поддерживаемые разделители: " - ", " – ", " — ".
    Возвращает кортеж (список треков, список пропущенных строк с причиной).
    """
    tracks: list[Track] = []
    separators = (" - ", " – ", " — ")
    skipped_lines: list[tuple[int, str, str]] = []  # (номер, строка, причина)

    def log(message: str):
        if log_callback:
            log_callback(message)
        else:
            print(message)

    for line_number, line in enumerate(raw_text.splitlines(), start=1):
        line = line.strip()
        if not line:
            continue

        parts = None
        for sep in separators:
            if sep in line:
                parts = line.split(sep, maxsplit=1)
                break

        if parts is None or len(parts) != 2:
            skipped_lines.append((line_number, line, "Не найден разделитель ' - '"))
            continue

        artist_str, name = parts[0].strip(), parts[1].strip()
        if not artist_str or not name:
            skipped_lines.append((line_number, line, "Пустой исполнитель или название трека"))
            continue

        # Разбиваем исполнителей
        artists = split_artists(artist_str)

        # Для каждого исполнителя создаем отдельный трек
        for artist in artists:
            tracks.append(Track(artist=artist, name=name))

    if skipped_lines:
        log("")
        log("ВНИМАНИЕ: Обнаружены строки с ошибками")
        log("-" * 50)
        for num, line, reason in skipped_lines:
            log(f"  Строка {num}: {line}")
            log(f"    Причина: {reason}")
        log(" " * 50)
        log(f"Всего распознано треков: {len(tracks)}")
        log(f"Пропущено строк: {len(skipped_lines)}")
        log("")

    return tracks, skipped_lines


def get_playlist_name(file_path: Path) -> str:
    return file_path.stem