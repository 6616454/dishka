__all__ = [
    "Depends",
    "inject",
    "setup_dishka",
]

from inspect import Parameter
from typing import Sequence, get_type_hints

from aiohttp import web

from dishka import Provider, make_async_container
from .base import Depends, wrap_injection


def inject(func):
    hints = get_type_hints(func)
    request_param = next(
        (name for name, hint in hints.items() if hint == web.Request),
        None,
    )
    if request_param:
        additional_params = []
    else:
        request_param = "request"
        additional_params = [
            Parameter(
                name=request_param,
                annotation=web.Request,
                kind=Parameter.POSITIONAL_OR_KEYWORD,
            )
        ]

    return wrap_injection(
        func=func,
        remove_depends=True,
        container_getter=lambda p, k: k[request_param].dishka_container
        if k.get(request_param)
        else p[0].request.dishka_container,
        additional_params=additional_params,
        is_async=True,
    )


@web.middleware
async def container_middleware(request: web.Request, handler):
    async with request.app.dishka_container(
        {web.Request: request},
    ) as request_container:
        request.dishka_container = request_container
        return await handler(request=request)


async def dishka_startup(app: web.Application) -> None:
    app.dishka_container = await app.dishka_container_wrapper.__aenter__()


async def dishka_shutdown(app: web.Application) -> None:
    await app.dishka_container_wrapper.__aexit__(None, None, None)


def setup_dishka(providers: Sequence[Provider], app: web.Application) -> None:
    container_wrapper = make_async_container(*providers)
    app.dishka_container_wrapper = container_wrapper
    app.middlewares.append(container_middleware)
    app.on_startup.append(dishka_startup)
    app.on_shutdown.append(dishka_shutdown)
