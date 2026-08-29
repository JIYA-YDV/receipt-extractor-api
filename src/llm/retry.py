"""Retry on the right errors only. Never on 400/401/403."""
import random
import time
from typing import Callable, TypeVar
from openai import APITimeoutError, APIConnectionError, RateLimitError, APIStatusError

T = TypeVar("T")

RETRYABLE_STATUS = {408, 409, 429, 500, 502, 503, 504}
MAX_ATTEMPTS = 3


def call_with_retry(fn: Callable[[], T]) -> T:
    """
    Call fn(). Retry on timeout, connection error, 429, or 5xx.
    Never retry on 400, 401, 403 — those won't fix themselves.
    Exponential backoff with jitter: ~1s, ~2s, ~4s.
    """
    last_exc: Exception | None = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            return fn()
        except (APITimeoutError, APIConnectionError) as e:
            last_exc = e
        except RateLimitError as e:
            last_exc = e
        except APIStatusError as e:
            if e.status_code not in RETRYABLE_STATUS:
                raise  # 400, 401, 403, 404 etc — do not retry
            last_exc = e

        if attempt == MAX_ATTEMPTS:
            break

        # Backoff: 1s, 2s, 4s + up to 500ms jitter
        wait = (2 ** (attempt - 1)) + random.uniform(0, 0.5)
        time.sleep(wait)

    assert last_exc is not None
    raise last_exc