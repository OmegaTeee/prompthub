"""
Tests for circuit breaker resilience pattern.

Verifies:
- State transitions (CLOSED → OPEN → HALF_OPEN → CLOSED)
- Failure threshold triggers OPEN state
- Recovery timeout enables HALF_OPEN state
- Success in HALF_OPEN returns to CLOSED
- Failure in HALF_OPEN returns to OPEN
"""

import pytest
import asyncio
from router.resilience.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitState,
    CircuitBreakerError,
)


class TestCircuitBreaker:
    """Test cases for circuit breaker pattern."""

    def test_initial_state_is_closed(self):
        """Test circuit breaker starts in CLOSED state."""
        cb = CircuitBreaker("test", CircuitBreakerConfig(failure_threshold=3))
        assert cb.state == CircuitState.CLOSED

    def test_successful_call_in_closed_state(self):
        """Test successful calls keep circuit CLOSED."""
        cb = CircuitBreaker("test", CircuitBreakerConfig(failure_threshold=3))

        cb.record_success()
        cb.record_success()

        assert cb.state == CircuitState.CLOSED
        cb.check()  # Should not raise

    def test_failure_threshold_opens_circuit(self):
        """Test circuit opens after failure threshold is reached."""
        cb = CircuitBreaker("test", CircuitBreakerConfig(failure_threshold=3))

        # Record failures up to threshold
        cb.record_failure()
        assert cb.state == CircuitState.CLOSED

        cb.record_failure()
        assert cb.state == CircuitState.CLOSED

        cb.record_failure()
        assert cb.state == CircuitState.OPEN

        # Check should raise
        with pytest.raises(CircuitBreakerError):
            cb.check()

    def test_open_circuit_rejects_calls(self):
        """Test circuit in OPEN state is not available."""
        cb = CircuitBreaker("test", CircuitBreakerConfig(failure_threshold=2))

        cb.record_failure()
        cb.record_failure()

        assert cb.state == CircuitState.OPEN
        with pytest.raises(CircuitBreakerError):
            cb.check()

    @pytest.mark.asyncio
    async def test_recovery_timeout_enters_half_open(self):
        """Test circuit enters HALF_OPEN after recovery timeout."""
        cb = CircuitBreaker(
            "test",
            CircuitBreakerConfig(failure_threshold=2, recovery_timeout=0.1)
        )

        # Open the circuit
        cb.record_failure()
        cb.record_failure()
        assert cb.state == CircuitState.OPEN

        # Wait for recovery timeout
        await asyncio.sleep(0.15)

        # Check state (should transition on next state check)
        assert cb.state == CircuitState.HALF_OPEN
        cb.check()  # Should not raise in half-open

    def test_success_in_half_open_closes_circuit(self):
        """Test successful call in HALF_OPEN returns to CLOSED."""
        cb = CircuitBreaker(
            "test",
            CircuitBreakerConfig(failure_threshold=2, success_threshold=1)
        )

        # Open the circuit
        cb.record_failure()
        cb.record_failure()

        # Force HALF_OPEN state
        cb._stats.state = CircuitState.HALF_OPEN

        # Record success
        cb.record_success()

        assert cb.state == CircuitState.CLOSED
        cb.check()  # Should not raise

    def test_failure_in_half_open_reopens_circuit(self):
        """Test failure in HALF_OPEN returns to OPEN."""
        cb = CircuitBreaker("test", CircuitBreakerConfig(failure_threshold=2))

        # Force HALF_OPEN state
        cb._stats.state = CircuitState.HALF_OPEN

        # Record failure
        cb.record_failure()

        assert cb.state == CircuitState.OPEN
        with pytest.raises(CircuitBreakerError):
            cb.check()

    def test_success_increments_success_count(self):
        """Test success increments success counter."""
        cb = CircuitBreaker("test", CircuitBreakerConfig(failure_threshold=3))

        cb.record_failure()
        cb.record_failure()
        assert cb.stats.failure_count == 2

        cb.record_success()
        # Failure count persists until circuit opens, then resets on close transition
        assert cb.stats.failure_count == 2
        assert cb.stats.success_count == 1
        assert cb.state == CircuitState.CLOSED

    def test_get_stats(self):
        """Test circuit breaker statistics."""
        cb = CircuitBreaker("test", CircuitBreakerConfig(failure_threshold=3))

        cb.record_failure()
        cb.record_failure()

        stats = cb.stats
        assert stats.state == CircuitState.CLOSED
        assert stats.failure_count == 2
        assert stats.total_failures == 2

    @pytest.mark.asyncio
    async def test_multiple_recovery_cycles(self):
        """Test circuit can recover multiple times."""
        cb = CircuitBreaker(
            "test",
            CircuitBreakerConfig(failure_threshold=2, recovery_timeout=0.05)
        )

        # First failure cycle
        cb.record_failure()
        cb.record_failure()
        assert cb.state == CircuitState.OPEN

        # Wait and recover
        await asyncio.sleep(0.1)
        assert cb.state == CircuitState.HALF_OPEN

        cb.record_success()
        assert cb.state == CircuitState.CLOSED

        # Second failure cycle
        cb.record_failure()
        cb.record_failure()
        assert cb.state == CircuitState.OPEN

        # Recover again
        await asyncio.sleep(0.1)
        assert cb.state == CircuitState.HALF_OPEN

    def test_reset_circuit_breaker(self):
        """Test resetting circuit breaker to initial state."""
        cb = CircuitBreaker("test", CircuitBreakerConfig(failure_threshold=2))

        # Open the circuit
        cb.record_failure()
        cb.record_failure()
        assert cb.state == CircuitState.OPEN

        # Reset
        cb.reset()

        assert cb.state == CircuitState.CLOSED
        assert cb.stats.failure_count == 0
        assert cb.stats.total_failures == 0
