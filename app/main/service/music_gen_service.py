import time
from typing import Tuple


def create(drums_file: bytes,
           bpm: int,
           tags: str) -> Tuple[bytes, int]:
    time.sleep(3)
    return drums_file, 200
