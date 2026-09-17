from dataclasses import dataclass
from typing import Optional

@dataclass
class Track:
    id: Optional[str]
    content_hash: str
    path: str
    filename: str
    title: Optional[str]
    artist: Optional[str]
    album: Optional[str]
    album_artist: Optional[str]
    genre: Optional[str]
    year: Optional[int]
    duration: float
    file_size: int
    modified_at: int
    artwork_id: Optional[str] = None