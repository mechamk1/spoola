import sqlite3
import hashlib
from enum import Enum
from uuid import uuid4
from pathlib import Path
from dataclasses import dataclass

from src.ingest import IngestedTrack

class IngestionStatus(str, Enum):
    ADDED = "added"
    UPDATED = "updated"
    UNCHANGED = "unchanged"
    DUPLICATE = "duplicate"

@dataclass
class SaveTrackResult:
    track_id: str
    status: str

class Database:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.connection = sqlite3.connect(db_path)

    def initialize(self) -> None:
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS artworks (
                id TEXT PRIMARY KEY,
                hash TEXT NOT NULL UNIQUE,
                path TEXT NOT NULL,
                mime_type TEXT NOT NULL,
                width INTEGER,
                height INTEGER
            );

            CREATE TABLE IF NOT EXISTS tracks (
                id TEXT PRIMARY KEY,
                content_hash TEXT NOT NULL UNIQUE,
                path TEXT NOT NULL UNIQUE,
                filename TEXT NOT NULL,
                title TEXT,
                artist TEXT,
                album TEXT,
                album_artist TEXT,
                genre TEXT,
                year INTEGER,
                duration REAL NOT NULL,
                file_size INTEGER NOT NULL,
                modified_at INTEGER NOT NULL,
                artwork_id TEXT,
                FOREIGN KEY (artwork_id) REFERENCES artworks(id)
            );

            CREATE TABLE IF NOT EXISTS ingestions (
                id TEXT PRIMARY KEY,
                started_at TEXT NOT NULL,
                finished_at TEXT,
                status TEXT NOT NULL,
                files_scanned INTEGER NOT NULL DEFAULT 0,
                files_added INTEGER NOT NULL DEFAULT 0,
                files_updated INTEGER NOT NULL DEFAULT 0,
                files_removed INTEGER NOT NULL DEFAULT 0,
                files_failed INTEGER NOT NULL DEFAULT 0,
                error_message TEXT
            );
            """
        )
        self.connection.commit()

    def save_artwork(self, artwork_data: bytes, mime_type: str, artwork_dir: Path) -> str:
        artwork_hash = hashlib.sha256(artwork_data).hexdigest()
    
        existing = self.connection.execute(
            """
            SELECT id
            FROM artworks
            WHERE hash = ?
            """,
            (artwork_hash,),
        ).fetchone()
    
        if existing:
            return existing[0]
    
        extension = mime_type.split("/")[-1].replace("jpeg", "jpg")
    
        artwork_dir.mkdir(parents=True, exist_ok=True)
    
        artwork_path = artwork_dir / f"{artwork_hash}.{extension}"
    
        artwork_path.write_bytes(artwork_data)
    
        artwork_id = str(uuid4())
    
        self.connection.execute(
            """
            INSERT INTO artworks (
                id,
                hash,
                path,
                mime_type
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                artwork_id,
                artwork_hash,
                str(artwork_path),
                mime_type,
            ),
        )
    
        self.connection.commit()
    
        return artwork_id

    def save_track(self, ingested_track: IngestedTrack) -> str:
        track = ingested_track.track
    
        artwork_id = None
    
        if (
            ingested_track.artwork_data is not None
            and ingested_track.artwork_mime_type is not None
        ):
            artwork_id = self.save_artwork(
                artwork_data=ingested_track.artwork_data,
                mime_type=ingested_track.artwork_mime_type,
                artwork_dir=self.db_path.parent / "artwork",
            )
    
        existing_by_path = self.connection.execute(
            """
            SELECT id, content_hash
            FROM tracks
            WHERE path = ?
            """,
            (track.path,),
        ).fetchone()
    
        if existing_by_path:
            track_id, existing_hash = existing_by_path

            if existing_hash == track.content_hash:
                return SaveTrackResult(
                    track_id=track_id,
                    status=IngestionStatus.UNCHANGED,
                )
        
            self.connection.execute(
                """
                UPDATE tracks
                SET
                    content_hash = ?,
                    filename = ?,
                    title = ?,
                    artist = ?,
                    album = ?,
                    album_artist = ?,
                    genre = ?,
                    year = ?,
                    duration = ?,
                    file_size = ?,
                    modified_at = ?,
                    artwork_id = ?
                WHERE id = ?
                """,
                (
                    track.content_hash,
                    track.filename,
                    track.title,
                    track.artist,
                    track.album,
                    track.album_artist,
                    track.genre,
                    track.year,
                    track.duration,
                        track.file_size,
                        track.modified_at,
                        artwork_id,
                        track_id,
                    ),
                )
            self.connection.commit()
        
            return SaveTrackResult(
                track_id=track_id,
                status=IngestionStatus.UPDATED,
            )
    
        existing_by_hash = self.connection.execute(
            """
            SELECT id
            FROM tracks
            WHERE content_hash = ?
            """,
            (track.content_hash,),
        ).fetchone()
    
        if existing_by_hash:
            return SaveTrackResult(
                track_id=existing_by_hash[0],
                status=IngestionStatus.DUPLICATE,
            )
    
        track_id = str(uuid4())
    
        self.connection.execute(
            """
            INSERT INTO tracks (
                id,
                content_hash,
                path,
                filename,
                title,
                artist,
                album,
                album_artist,
                genre,
                year,
                duration,
                file_size,
                modified_at,
                artwork_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                track_id,
                track.content_hash,
                track.path,
                track.filename,
                track.title,
                track.artist,
                track.album,
                track.album_artist,
                track.genre,
                track.year,
                track.duration,
                track.file_size,
                track.modified_at,
                artwork_id,
            ),
        )
    
        self.connection.commit()
        return SaveTrackResult(
            track_id=track_id,
            status=IngestionStatus.ADDED,
        )

    def close(self) -> None:
        self.connection.close()