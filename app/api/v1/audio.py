from typing import Annotated
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.repositories.audio import AudioRepository
from app.schemas.audio import AudioAssetResponse
from app.services.audio import (
    AudioService,
    MediaTooLargeError,
    MediaTooLongError,
    ProcessingQueueUnavailableError,
    UnsupportedMediaError,
)

router = APIRouter()


@router.post(
    "",
    response_model=AudioAssetResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def upload_audio(
    file: Annotated[UploadFile, File(...)],
    db: Annotated[Session, Depends(get_db)],
) -> AudioAssetResponse:
    try:
        asset = AudioService(db).create(file)

    except MediaTooLargeError as exc:
        raise HTTPException(
            status_code=413,
            detail={
                "code": "MEDIA_TOO_LARGE",
                "message": str(exc),
            },
        ) from exc

    except MediaTooLongError as exc:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "MEDIA_TOO_LONG",
                "message": str(exc),
            },
        ) from exc

    except UnsupportedMediaError as exc:
        raise HTTPException(
            status_code=415,
            detail={
                "code": "MEDIA_UNSUPPORTED",
                "message": str(exc),
            },
        ) from exc

    except ProcessingQueueUnavailableError as exc:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "PROCESSING_QUEUE_UNAVAILABLE",
                "message": str(exc),
                "audio_id": str(exc.audio_id),
            },
        ) from exc

    return AudioAssetResponse.model_validate(asset)


@router.get(
    "/{audio_id}",
    response_model=AudioAssetResponse,
)
def get_audio(
    audio_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> AudioAssetResponse:
    asset = AudioRepository(db).get(audio_id)

    if asset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "AUDIO_NOT_FOUND",
                "message": "Audio not found",
            },
        )

    return AudioAssetResponse.model_validate(asset)