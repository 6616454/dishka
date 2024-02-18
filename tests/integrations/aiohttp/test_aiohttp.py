from contextlib import asynccontextmanager
from typing import Annotated, AsyncGenerator
from unittest.mock import Mock

import pytest
from aiohttp import web
from aiohttp.web_response import Response

from dishka.integrations.aiohttp import (
    Depends,
    inject,
    setup_dishka,
)
from ..common import (
    APP_DEP_VALUE,
    REQUEST_DEP_VALUE,
    AppDep,
    AppProvider,
    RequestDep,
)


@asynccontextmanager
async def dishka_app(view, provider) -> web.Application:
    app = web.Application()
    app.router.add_get("/", inject(view))
    setup_dishka(app=app, providers=[provider])

    yield app


async def handle_with_app(
    a: Annotated[AppDep, Depends()],
    mock: Annotated[Mock, Depends()],
):
    mock(a)
    return web.Response(text="Success!")


@pytest.mark.asyncio
async def test_app_dependency(aiohttp_client, app_provider: AppProvider):
    async with dishka_app(handle_with_app, app_provider) as app:
        client = await aiohttp_client(app)
        async with client:
            await client.get('/')
            app_provider.mock.assert_called_with(APP_DEP_VALUE)
            app_provider.app_released.assert_not_called()
        app_provider.app_released.assert_called()


async def get_with_request(
        a: Annotated[RequestDep, Depends()],
        mock: Annotated[Mock, Depends()],
) -> Response:
    mock(a)
    return web.Response(text="Success!")


@pytest.mark.asyncio
async def test_request_dependency(aiohttp_client, app_provider: AppProvider):
    async with dishka_app(get_with_request, app_provider) as app:
        client = await aiohttp_client(app)
        async with client:
            await client.get("/")
            app_provider.mock.assert_called_with(REQUEST_DEP_VALUE)
            app_provider.request_released.assert_called_once()


@pytest.mark.asyncio
async def test_request_dependency2(aiohttp_client, app_provider: AppProvider):
    async with dishka_app(get_with_request, app_provider) as app:
        client = await aiohttp_client(app)
        async with client:
            await client.get("/")
            app_provider.mock.assert_called_with(REQUEST_DEP_VALUE)
            app_provider.mock.reset_mock()
            app_provider.request_released.assert_called_once()
            app_provider.request_released.reset_mock()
            await client.get("/")
            app_provider.mock.assert_called_with(REQUEST_DEP_VALUE)
            app_provider.request_released.assert_called_once()
