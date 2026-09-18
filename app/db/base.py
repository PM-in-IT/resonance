from app.db.base_class import Base

from app.db.models.audio import AudioAsset  # noqa: E402,F401
from app.db.models.query import QueryRecord  # noqa: E402,F401
from app.db.models.segment import TranscriptSegment  # noqa: E402,F401

__all__ = ["Base"]
