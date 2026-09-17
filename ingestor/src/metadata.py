import hashlib
from pathlib import Path
from typing import Optional
from mutagen import File

from src.models import Track

def calculate_file_hash(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as file:
        while chunk := file.read(1024 * 1024):
            hasher.update(chunk)
    return hasher.hexdigest()

def _get_tag(audio, key: str) -> Optional[str]:
    values = audio.get(key)
    if not values:
        return None
    value = values[0].strip()
    if not value:
        return None
    return value

def _parse_year(value: Optional[str]) -> Optional[int]:
    if not value:
        return None
    try:
        return int(value[:4])
    except ValueError:
        return None

def _parse_duration(audio) -> float:
    return round(float(audio.info.length), 2)

def extract_track(path: Path) -> Track:
    audio = File(path, easy=True)
    if audio is None:
        raise ValueError(f"Unable to read audio file: {path}")
    stat = path.stat()
    return Track(
        id=None,
        content_hash=calculate_file_hash(path),
        path=str(path),
        filename=path.name,
        title=_get_tag(audio, "title"),
        artist=_get_tag(audio, "artist"),
        album=_get_tag(audio, "album"),
        album_artist=_get_tag(audio, "albumartist"),
        genre=_get_tag(audio, "genre"),
        year=_parse_year(_get_tag(audio, "date")),
        duration=_parse_duration(audio),
        file_size=stat.st_size,
        modified_at=int(stat.st_mtime),
    )