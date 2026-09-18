import shutil
from pathlib import Path
from typing import BinaryIO


class LocalStorage:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def save(self, source: BinaryIO, key: str) -> str:
        destination = self.root / key
        destination.parent.mkdir(parents=True, exist_ok=True)
        source.seek(0)
        with destination.open("wb") as output:
            shutil.copyfileobj(source, output)
        return key

    def resolve_local_path(self, key: str) -> Path:
        return self.root / key

    def delete(self, key: str) -> None:
        self.resolve_local_path(key).unlink(missing_ok=True)
