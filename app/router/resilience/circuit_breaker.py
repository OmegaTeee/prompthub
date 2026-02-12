"""
Circuit Breaker pattern implementation for resilient MCP server communication.

States:
- CLOSED: Normal operation, requests pass through
- OPEN: Failures exceeded threshold, requests fail immediately
- HALF_OPEN: Testing if service recovered, limited requests allowed

The circuit breaker prevents cascading failures by failing fast when
a service is known to be unhealthy, giving it time to recover.
"""

import asyncio
import logging
import time
from collections.abc import Callable
from enum import StrEnum
from typing import TypeVar

from pydantic import BaseModel

logger = logging.getLogger(__name__)

T = TypeVar("T")


class CircuitState(StrEnum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing fast
    HALF_OPEN = "half_open"  # Testing recovery


class CircuitBreakerConfig(BaseModel):
    """Configuration for a circuit breaker."""

    failure_threshold: int = 3  # Failures before opening
    recovery_timeout: float = 30.0  # Seconds before trying half-open
    half_open_max_calls: int = 1  # Calls allowed in half-open state
    success_threshold: int = 1  # Successes needed to close from half-open


class CircuitBreakerStats(BaseModel):
    """Statistics for a circuit breaker."""

    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: float | None = None
    last_success_time: float | None = None
    total_failures: int = 0
    total_successes: int = 0
    times_opened: int = 0


class CircuitBreakerError(Exception):
    """Raised when circuit breaker is open."""

    def __init__(self, name: str, state: CircuitState, retry_after: float | None = None):
        self.name = name
        self.state = state
        self.retry_after = retry_after
        super().__init__(f"Circuit breaker '{name}' is {state.value}")


class CircuitBreaker:
    """
    Circuit breaker for a single service.

    Usage:
        breaker = CircuitBreaker("context7")

        # Option 1: Context manager
        async with breaker:
            result = await call_service()

        # Option 2: Decorator
        @breaker
        async def call_service():
            ...

        # Option 3: Manual
        breaker.check()  # Raises if open
        try:
            result = await call_service()
            breaker.record_success()
        except Exception as e:
            breaker.record_failure()
            raise
    """

    def __init__(self, name: str, config: CircuitBreakerConfig | None = None):
        """
        Initialize the circuit breaker.

        Args:
            name: Identifier for this circuit (usually server name)
            config: Configuration options
        """
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self._stats = CircuitBreakerStats()
        self._lock = asyncio.Lock()
        self._half_open_calls = 0

    @property
    def state(self) -> CircuitState:
        """Get current state, checking for automatic transitions."""
        if self._stats.state == CircuitState.OPEN:
            # Check if recovery timeout has passed
            if self._stats.last_failure_time:
                elapsed = time.time() - self._stats.last_failure_time
                if elapsed >= self.config.recovery_timeout:
                    return CircuitState.HALF_OPEN
        return self._stats.state

    @property
    def stats(self) -> CircuitBreakerStats:
        """Get current statistics."""
        # Return copy with current state
        return CircuitBreakerStats(
            state=self.state,
            failure_count=self._stats.failure_count,
            success_count=self._stats.success_count,
            last_failure_time=self._stats.last_failure_time,
            last_success_time=self._stats.last_success_time,
            total_failures=self._stats.total_failures,
            total_successes=self._stats.total_successes,
            times_opened=self._stats.times_opened,
        )

    def check(self) -> None:
        """
        Check if requests are allowed.

        Raises:
            CircuitBreakerError: If circuit is open
        """
        current_state = self.state

        if current_state == CircuitState.CLOSED:
            return  # Allow request

        if current_state == CircuitState.OPEN:
            # Calculate retry-after time
            retry_after = None
            if self._stats.last_failure_time:
                elapsed = time.time() - self._stats.last_failure_time
                retry_after = max(0, self.config.recovery_timeout - elapsed)
            raise CircuitBreakerError(self.name, current_state, retry_after)

        if current_state == CircuitState.HALF_OPEN:
            # Allow limited calls in half-open state
            if self._half_open_calls >= self.config.half_open_max_calls:
                raise CircuitBreakerError(self.name, current_state)
            self._half_open_calls += 1

    def record_success(self) -> None:
        """Record a successful call."""
        current_state = self.state
        self._stats.success_count += 1
        self._stats.total_successes += 1
        self._stats.last_success_time = time.time()

        if current_state == CircuitState.HALF_OPEN:
            # Check if we should close the circuit
            if self._stats.success_count >= self.config.success_threshold:
                self._transition_to(CircuitState.CLOSED)
                logger.info(f"Circuit '{self.name}' closed after recovery")

    def record_failure(self, error: Exception | None = None) -> None:
        """Record a failed call."""
        current_state = self.state
        self._stats.failure_count += 1
        self._stats.total_failures += 1
        self._stats.last_failure_time = time.time()

        if current_state == CircuitState.CLOSED:
            # Check if we should open the circuit
            if self._stats.failure_count >= self.config.failure_threshold:
                self._transition_to(CircuitState.OPEN)
                logger.warning(
                    f"Circuit '{self.name}' opened after {self._stats.failure_count} failures"
                )

        elif current_state == CircuitState.HALF_OPEN:
            # Any failure in half-open goes back to open
            self._transition_to(CircuitState.OPEN)
            logger.warning(f"Circuit '{self.name}' reopened after failure in half-open")

    def _transition_to(self, new_state: CircuitState) -> None:
        """Transition to a new state."""
        old_state = self._stats.state
        self._stats.state = new_state

        if new_state == CircuitState.CLOSED:
            self._stats.failure_count = 0
            self._stats.success_count = 0
            self._half_open_calls = 0

        elif new_state == CircuitState.OPEN:
            self._stats.times_opened += 1
            self._half_open_calls = 0

        elif new_state == CircuitState.HALF_OPEN:
            self._stats.success_count = 0
            self._half_open_calls = 0

        logger.debug(f"Circuit '{self.name}' transitioned: {old_state} -> {new_state}")

    def reset(self) -> None:
        """Reset the circuit breaker to closed state."""
        self._stats = CircuitBreakerStats()
        self._half_open_calls = 0
        logger.info(f"Circuit '{self.name}' reset")

    async def __aenter__(self) -> "CircuitBreaker":
        """Async context manager entry."""
        self.check()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> bool:
        """Async context manager exit."""
        if exc_type is None:
            self.record_success()
        else:
            self.record_failure(exc_val)
        return False  # Don't suppress exceptions

    def __call__(self, func: Callable[..., T]) -> Callable[..., T]:
        """Decorator for wrapping async functions."""

        async def wrapper(*args, **kwargs) -> T:
            self.check()
            try:
                result = await func(*args, **kwargs)
                self.record_success()
                return result
            except Exception as e:
                self.record_failure(e)
                raise

        return wrapper


class CircuitBreakerRegistry:
    """
    Registry for managing multiple circuit breakers.

    Each MCP server gets its own circuit breaker to isolate failures.
    """

    def __init__(self, default_config: CircuitBreakerConfig | None = None):
        """
        Initialize the registry.

        Args:
            default_config: Default configuration for new circuit breakers
        """
        self.default_config = default_config or CircuitBreakerConfig()
        self._breakers: dict[str, CircuitBreaker] = {}
        self._lock = asyncio.Lock()

    def get(self, name: str) -> CircuitBreaker:
        """
        Get or create a circuit breaker for a service.

        Args:
            name: Service name (e.g., "context7")

        Returns:
            CircuitBreaker instance
        """
        if name not in self._breakers:
            self._breakers[name] = CircuitBreaker(name, self.default_config)
            logger.debug(f"Created circuit breaker for '{name}'")
        return self._breakers[name]

    def get_all_stats(self) -> dict[str, CircuitBreakerStats]:
        """Get statistics for all circuit breakers."""
        return {name: breaker.stats for name, breaker in self._breakers.items()}

    def reset(self, name: str) -> bool:
        """
        Reset a specific circuit breaker.

        Args:
            name: Service name

        Returns:
            True if reset, False if not found
        """
        if name in self._breakers:
            self._breakers[name].reset()
            return True
        return False

    def reset_all(self) -> None:
        """Reset all circuit breakers."""
        for breaker in self._breakers.values():
            breaker.reset()
