from app.core.config import settings
from app.storage.base import Storage
from app.storage.local import LocalStorage


def get_storage() -> Storage:
    if settings.storage_backend == "local":
        return LocalStorage(settings.local_storage_path)
    raise NotImplementedError(f"Unsupported storage backend: {settings.storage_backend}")
