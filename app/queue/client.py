from uuid import UUID

from redis import Redis
from rq import Queue
from rq.job import Job

from app.core.config import settings


def get_queue() -> Queue:
    return Queue(settings.rq_queue_name, connection=Redis.from_url(settings.redis_url))


def enqueue_audio_processing(audio_id: UUID) -> Job:
    return get_queue().enqueue(
        "app.workers.jobs.process_audio",
        str(audio_id),
        job_timeout="30m",
        result_ttl=3600,
    )
