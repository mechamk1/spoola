from pathlib import Path
from typing import Optional

from mutagen.id3 import ID3

def extract_artwork(path: Path) -> Optional[tuple[bytes, str]]:
    tags = ID3(path)
    for tag in tags.values():
        if tag.FrameID == "APIC":
            return tag.data, tag.mime
    return None