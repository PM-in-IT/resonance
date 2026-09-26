import os
import shutil
import uuid
from pathlib import Path
from typing import BinaryIO


class LocalStorage:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def save(self, source: BinaryIO, key: str) -> str:
        destination = self._resolve(key)
        destination.parent.mkdir(parents=True, exist_ok=True)

        temporary = destination.with_name(
            f".{destination.name}.{uuid.uuid4().hex}.tmp"
        )

        try:
            source.seek(0)

            with temporary.open("wb") as output:
                shutil.copyfileobj(source, output)

            os.replace(temporary, destination)
        finally:
            temporary.unlink(missing_ok=True)

        return key

    def resolve_local_path(self, key: str) -> Path:
        return self._resolve(key)

    def delete(self, key: str) -> None:
        self._resolve(key).unlink(missing_ok=True)

    def _resolve(self, key: str) -> Path:
        relative = Path(key)

        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("Invalid storage key")

        resolved = (self.root / relative).resolve()

        if not resolved.is_relative_to(self.root):
            raise ValueError("Storage key escapes storage root")

        return resolved