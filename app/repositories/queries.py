from sqlalchemy.orm import Session

from app.db.models.query import QueryRecord


class QueryRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add(self, record: QueryRecord) -> QueryRecord:
        self.db.add(record)
        self.db.flush()
        return record
