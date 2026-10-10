from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=10)


class MatchResponse(BaseModel):
    start_ms: int
    end_ms: int
    text: str


class QueryResponse(BaseModel):
    question: str
    summary: str
    primary_start_ms: int
    primary_end_ms: int
    matches: list[MatchResponse]
