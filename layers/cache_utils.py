"""Suppression flag for model cache/NOTIFY side effects during dry-run imports."""

from contextlib import contextmanager
from contextvars import ContextVar

_suppress_cache_signals = ContextVar("suppress_cache_signals", default=False)


@contextmanager
def suppress_cache_signals():
    """Suppress cache invalidation and NOTIFY emission for the duration of the block."""
    token = _suppress_cache_signals.set(True)
    try:
        yield
    finally:
        _suppress_cache_signals.reset(token)


def cache_signals_suppressed():
    return _suppress_cache_signals.get()
