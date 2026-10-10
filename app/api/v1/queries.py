from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.query import QueryRequest, QueryResponse
from app.services.query import AudioNotReadyError, QueryService

router = APIRouter()


@router.post("/{audio_id}/queries", response_model=QueryResponse)
def query_audio(
    audio_id: UUID,
    payload: QueryRequest,
    db: Annotated[Session, Depends(get_db)],
) -> QueryResponse:
    try:
        return QueryService(db).answer(audio_id, payload.question, payload.top_k)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except AudioNotReadyError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
