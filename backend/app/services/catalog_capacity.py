"""Keep catalogue bursts within the small API instance's memory budget."""
import asyncio

from starlette.responses import JSONResponse


class CatalogCapacityMiddleware:
    def __init__(self, app, concurrency=3, queue_timeout=5):
        self.app = app
        self.slots = asyncio.Semaphore(concurrency)
        self.queue_timeout = queue_timeout

    async def __call__(self, scope, receive, send):
        path = scope.get("path", "")
        heavy = path == "/admin/ranking-readiness" or any(
            path == prefix or path.startswith(prefix + "/")
            for prefix in ("/products", "/rankings", "/deals", "/budget")
        )
        if scope["type"] != "http" or scope.get("method") != "GET" or not heavy:
            return await self.app(scope, receive, send)
        try:
            await asyncio.wait_for(self.slots.acquire(), timeout=self.queue_timeout)
        except TimeoutError:
            response = JSONResponse({"error": "catalog_busy", "retry_after_seconds": 1},
                                    status_code=503, headers={"Retry-After": "1"})
            return await response(scope, receive, send)
        try:
            # Hold the slot through JSON serialization and sending, not only SQL.
            await self.app(scope, receive, send)
        finally:
            self.slots.release()
