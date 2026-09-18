import json
import subprocess
from pathlib import Path


class InvalidMediaError(ValueError):
    pass


def probe_duration_ms(path: Path) -> int:
    result = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "json",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise InvalidMediaError("Uploaded file is not a readable media file")

    payload = json.loads(result.stdout)
    try:
        seconds = float(payload["format"]["duration"])
    except (KeyError, TypeError, ValueError) as exc:
        raise InvalidMediaError("Could not determine media duration") from exc

    return round(seconds * 1000)
