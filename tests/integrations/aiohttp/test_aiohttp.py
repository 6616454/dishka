from contextlib import asynccontextmanager
from typing import Annotated

import pytest
from aiohttp import web

from dishka.integrations.aiohttp import (
    Depends,
    setup_dishka,
    inject,
)
from ..common import (
    APP_DEP_VALUE,
    REQUEST_DEP_VALUE,
    AppDep,
    AppProvider,
    RequestDep,
)


@asynccontextmanager
async def dishka_app(view, provider):
    app = web.Application()
    setup_dishka(app=app, providers=[provider])
    yield app
