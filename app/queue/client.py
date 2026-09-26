from functools import lru_cache
from uuid import UUID

from redis import Redis
from rq import Queue
from rq.job import Job

from app.core.config import settings


@lru_cache
def get_redis() -> Redis:
    return Redis.from_url(settings.redis_url)


@lru_cache
def get_queue() -> Queue:
    return Queue(
        settings.rq_queue_name,
        connection=get_redis(),
    )


def audio_processing_job_id(audio_id: UUID) -> str:
    return f"audio-process-{audio_id}"


def enqueue_audio_processing(audio_id: UUID) -> Job:
    return get_queue().enqueue(
        "app.workers.jobs.process_audio",
        str(audio_id),
        job_id=audio_processing_job_id(audio_id),
        job_timeout=settings.processing_job_timeout_seconds,
        result_ttl=settings.processing_job_result_ttl_seconds,
    )