"""Minimal .env loader (no new dependencies).

Reads `backend/.env` and project-root `.env` if present, without overriding
real environment variables. Lets `GOOGLE_CLIENT_ID`, `JWT_SECRET`,
`DATABASE_URL`, etc. work from a file in local dev and simple deploys.
"""
import os

_CANDIDATES = (
    os.path.join(os.path.dirname(__file__), ".env"),          # backend/.env
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"),  # root .env
)


def load() -> None:
    for path in _CANDIDATES:
        try:
            with open(path, encoding="utf-8") as f:
                for raw in f:
                    line = raw.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    key, _, val = line.partition("=")
                    key = key.strip()
                    val = val.strip().strip('"').strip("'")
                    if key and key not in os.environ:
                        os.environ[key] = val
        except FileNotFoundError:
            continue
        except OSError:
            continue
