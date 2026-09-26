import math
from pathlib import Path

import av


class InvalidMediaError(ValueError):
    pass


def probe_duration_ms(path: Path) -> int:
    try:
        with av.open(str(path)) as container:
            duration = container.duration

            if duration is None:
                raise InvalidMediaError(
                    "Could not determine media duration"
                )

            seconds = duration / av.time_base

    except InvalidMediaError:
        raise
    except Exception as exc:
        raise InvalidMediaError(
            "Uploaded file is not a readable media file"
        ) from exc

    if not math.isfinite(seconds) or seconds <= 0:
        raise InvalidMediaError(
            "Media duration must be positive"
        )

    return round(seconds * 1000)