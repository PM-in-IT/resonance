from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.repositories.audio import AudioRepository
from app.schemas.audio import AudioAssetResponse
from app.services.audio import AudioService

router = APIRouter()


@router.post("", response_model=AudioAssetResponse, status_code=status.HTTP_202_ACCEPTED)
def upload_audio(
    file: Annotated[UploadFile, File(...)],
    db: Annotated[Session, Depends(get_db)],
) -> AudioAssetResponse:
    try:
        asset = AudioService(db).create(file)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return AudioAssetResponse.model_validate(asset)


@router.get("/{audio_id}", response_model=AudioAssetResponse)
def get_audio(
    audio_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> AudioAssetResponse:
    asset = AudioRepository(db).get(audio_id)
    if asset is None:
        raise HTTPException(status_code=404, detail="Audio not found")
    return AudioAssetResponse.model_validate(asset)
