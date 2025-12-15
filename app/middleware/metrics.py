"""Prometheus metrics middleware."""

from prometheus_client import Counter, Histogram, generate_latest
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import time


# Metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

ACTIVE_USERS = Counter(
    'active_users_total',
    'Total active users',
    ['role']
)


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to collect application metrics."""
    
    async def dispatch(self, request: Request, call_next):
        """Process request and collect metrics."""
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Record metrics
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code
        ).inc()
        
        REQUEST_DURATION.labels(
            method=request.method,
            endpoint=request.url.path
        ).observe(duration)
        
        return response


async def metrics_endpoint():
    """Endpoint to expose Prometheus metrics."""
    return Response(
        content=generate_latest(),
        media_type="text/plain"
    )
