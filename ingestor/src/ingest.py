from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from src.artwork import extract_artwork
from src.metadata import extract_track
from src.models import Track

@dataclass
class IngestedTrack:
    track: Track
    artwork_data: Optional[bytes]
    artwork_mime_type: Optional[str]
def ingest_directory(music_dir: Path) -> list[IngestedTrack]:
    results = []
    for path in sorted(music_dir.glob("*.mp3")):
        try:
            track = extract_track(path)
            artwork = extract_artwork(path)
            artwork_data = None
            artwork_mime_type = None
            if artwork:
                artwork_data, artwork_mime_type = artwork
            results.append(
                IngestedTrack(
                    track=track,
                    artwork_data=artwork_data,
                    artwork_mime_type=artwork_mime_type,
                )
            )
        except Exception as exc:
            print(f"ERROR processing {path.name}: {exc}")
    return results