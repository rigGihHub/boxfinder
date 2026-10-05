"""Share short-lived homepage calculations across concurrent page requests."""
import asyncio
from collections import OrderedDict
from time import monotonic


class CatalogSnapshotMiddleware:
    paths = {'/rankings/overview', '/admin/ranking-readiness', '/deals', '/budget/recommendations'}

    def __init__(self, app, ttl=30, max_bytes=16 * 1024 * 1024):
        self.app = app
        self.ttl = ttl
        self.max_bytes = max_bytes
        self.cache = OrderedDict()
        self.lock = asyncio.Lock()

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http' or scope.get('method') != 'GET' or scope.get('path') not in self.paths:
            return await self.app(scope, receive, send)
        key = (scope['path'], scope.get('query_string', b''))
        # Waiting requests retain no ORM graph and consume no capacity slot.
        async with self.lock:
            cached = self.cache.get(key)
            if cached and cached[0] > monotonic():
                self.cache.move_to_end(key)
                await send({**cached[1], 'headers': list(cached[1].get('headers', []))})
                return await send({'type': 'http.response.body', 'body': cached[2]})
            self.cache.pop(key, None)
            start = None
            parts = []
            size = 0
            complete = False

            async def capture(message):
                nonlocal start, size, complete
                if message['type'] == 'http.response.start':
                    start = {**message, 'headers': list(message.get('headers', []))}
                elif message['type'] == 'http.response.body':
                    body = message.get('body', b'')
                    size += len(body)
                    if size <= 2 * 1024 * 1024:
                        parts.append(body)
                    else:
                        parts.clear()
                    complete = not message.get('more_body', False)
                await send(message)

            await self.app(scope, receive, capture)
            if start and start['status'] == 200 and complete and size <= 2 * 1024 * 1024:
                self.cache[key] = (monotonic() + self.ttl, start, b''.join(parts))
                while len(self.cache) > 32 or sum(len(value[2]) for value in self.cache.values()) > self.max_bytes:
                    self.cache.popitem(last=False)
