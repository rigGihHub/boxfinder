import asyncio

from app.services.catalog_snapshots import CatalogSnapshotMiddleware


def test_simultaneous_homepage_requests_share_one_calculation_and_query_keys():
    async def scenario():
        calls = []
        async def app(scope, receive, send):
            calls.append(scope.get('query_string'))
            await asyncio.sleep(.01)
            await send({'type': 'http.response.start', 'status': 200, 'headers': []})
            await send({'type': 'http.response.body', 'body': scope.get('query_string') or b'empty'})
        middleware = CatalogSnapshotMiddleware(app)
        async def call(query):
            messages = []
            async def send(message):
                messages.append(message)
            await middleware({'type': 'http', 'method': 'GET', 'path': '/budget/recommendations',
                              'query_string': query}, None, send)
            return messages[-1]['body']
        results = await asyncio.gather(*(call(b'budget=100') for _ in range(12)))
        assert calls == [b'budget=100']
        assert results == [b'budget=100'] * 12
        assert await call(b'budget=500') == b'budget=500'
        assert len(calls) == 2
        # Expiry causes a fresh calculation; old results do not persist forever.
        key = ('/budget/recommendations', b'budget=100')
        cached = middleware.cache[key]
        middleware.cache[key] = (0, cached[1], cached[2])
        await call(b'budget=100')
        assert len(calls) == 3
    asyncio.run(scenario())


def test_error_responses_are_not_cached_and_memory_is_bounded():
    async def scenario():
        status = 503
        calls = 0
        async def app(scope, receive, send):
            nonlocal calls
            calls += 1
            await send({'type': 'http.response.start', 'status': status, 'headers': []})
            await send({'type': 'http.response.body', 'body': b'123456'})
        middleware = CatalogSnapshotMiddleware(app, max_bytes=10)
        async def send(message):
            pass
        scope = {'type': 'http', 'method': 'GET', 'path': '/deals', 'query_string': b'days=7'}
        await middleware(scope, None, send)
        await middleware(scope, None, send)
        assert calls == 2 and not middleware.cache
        status = 200
        await middleware(scope, None, send)
        await middleware({**scope, 'query_string': b'days=30'}, None, send)
        assert len(middleware.cache) == 1
        assert sum(len(value[2]) for value in middleware.cache.values()) <= 10
    asyncio.run(scenario())
