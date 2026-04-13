"""
Per-source circuit breaker for scrapers.
After N consecutive failures, the circuit opens and blocks requests for a cooldown period.
State is stored in memory (per-process). For multi-process, use Redis.
"""
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from threading import Lock
from typing import ClassVar

logger = logging.getLogger(__name__)


class CircuitState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitBreaker:
    source_name: str
    failure_threshold: int = 3
    cooldown_seconds: float = 3600.0
    success_threshold: int = 1

    _failure_count: int = field(default=0, init=False, repr=False)
    _success_count: int = field(default=0, init=False, repr=False)
    _state: CircuitState = field(default=CircuitState.CLOSED, init=False, repr=False)
    _last_failure_time: float = field(default=0.0, init=False, repr=False)
    _lock: Lock = field(default_factory=Lock, init=False, repr=False)

    _registry: ClassVar[dict[str, "CircuitBreaker"]] = {}
    _registry_lock: ClassVar[Lock] = Lock()

    @classmethod
    def get(cls, source_name: str) -> "CircuitBreaker":
        with cls._registry_lock:
            if source_name not in cls._registry:
                cls._registry[source_name] = cls(source_name=source_name)
            return cls._registry[source_name]

    @property
    def state(self) -> CircuitState:
        with self._lock:
            if self._state == CircuitState.OPEN:
                if time.monotonic() - self._last_failure_time >= self.cooldown_seconds:
                    self._state = CircuitState.HALF_OPEN
                    self._success_count = 0
                    logger.info(f"Circuit breaker [{self.source_name}] → HALF_OPEN (cooldown elapsed)")
            return self._state

    def is_allowed(self) -> bool:
        """Returns True if a request is allowed to proceed."""
        state = self.state
        if state == CircuitState.CLOSED:
            return True
        if state == CircuitState.HALF_OPEN:
            return True
        remaining = self.cooldown_seconds - (time.monotonic() - self._last_failure_time)
        logger.warning(
            f"Circuit breaker [{self.source_name}] OPEN — blocked. "
            f"Cooldown: {remaining:.0f}s remaining."
        )
        return False

    def record_success(self) -> None:
        with self._lock:
            self._failure_count = 0
            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.success_threshold:
                    self._state = CircuitState.CLOSED
                    logger.info(f"Circuit breaker [{self.source_name}] → CLOSED (recovered)")

    def record_failure(self, error_type: str = "UNKNOWN") -> None:
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.monotonic()

            if self._state == CircuitState.HALF_OPEN:
                self._state = CircuitState.OPEN
                logger.error(
                    f"Circuit breaker [{self.source_name}] → OPEN (half-open test failed: {error_type})"
                )
            elif self._failure_count >= self.failure_threshold:
                self._state = CircuitState.OPEN
                logger.error(
                    f"Circuit breaker [{self.source_name}] → OPEN "
                    f"(threshold={self.failure_threshold}, error={error_type})"
                )

    def get_status(self) -> dict:
        return {
            "source": self.source_name,
            "state": self.state.value,
            "failure_count": self._failure_count,
            "last_failure_age_seconds": (
                round(time.monotonic() - self._last_failure_time, 1)
                if self._last_failure_time > 0 else None
            ),
        }


def classify_http_error(status_code: int) -> str:
    """Classify HTTP error codes for circuit breaker decisions."""
    if status_code == 403:
        return "BLOCKED"
    if status_code == 429:
        return "RATE_LIMITED"
    if status_code >= 500:
        return "SERVER_ERROR"
    if status_code == 404:
        return "NOT_FOUND"
    return "HTTP_ERROR"
