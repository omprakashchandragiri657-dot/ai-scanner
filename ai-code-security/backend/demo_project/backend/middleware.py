"""Request logging middleware."""

import time

from flask import g, request


def request_logger():
    """Attach timing metadata to every incoming request."""
    g.started_at = time.perf_counter()
    print(f"[fairshare] {request.method} {request.path}")


def after_request(response):
    started = getattr(g, "started_at", None)
    if started is not None:
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        response.headers["X-Response-Time-Ms"] = str(elapsed_ms)
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response
