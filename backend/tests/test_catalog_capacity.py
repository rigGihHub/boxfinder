import asyncio

from app.services.catalog_capacity import CatalogCapacityMiddleware


def test_catalog_burst_is_bounded_while_health_remains_responsive():
    async def scenario():
        release = asyncio.Event()
        entered = asyncio.Event()
        active = 0
        peak = 0
        statuses = []

        async def app(scope, receive, send):
            nonlocal active, peak
            if scope['path'] == '/health':
                statuses.append(200)
                return
            active += 1
            peak = max(peak, active)
            if active == 2:
                entered.set()
            try:
                await release.wait()
            finally:
                active -= 1

        async def receive():
            return {'type': 'http.request', 'body': b''}

        async def send(message):
            if message['type'] == 'http.response.start':
                statuses.append(message['status'])
                assert (b'retry-after', b'1') in message['headers']

        middleware = CatalogCapacityMiddleware(app, concurrency=2, queue_timeout=.02)
        async def call(path):
            await middleware({'type': 'http', 'path': path, 'method': 'GET'}, receive, send)

        first = asyncio.create_task(call('/rankings/resale'))
        second = asyncio.create_task(call('/products'))
        await entered.wait()
        await call('/health')
        await call('/deals')
        assert statuses == [200, 503]
        assert peak == 2
        release.set()
        await asyncio.gather(first, second)
        await call('/budget/recommendations')
        assert active == 0

    asyncio.run(scenario())


def test_failed_catalog_request_releases_its_slot():
    async def scenario():
        async def app(*args):
            raise ValueError('test failure')

        middleware = CatalogCapacityMiddleware(app, concurrency=1)
        for _ in range(2):
            try:
                await middleware({'type': 'http', 'method': 'GET', 'path': '/products'}, None, None)
            except ValueError:
                pass
            else:
                raise AssertionError('slot was leaked')

    asyncio.run(scenario())
