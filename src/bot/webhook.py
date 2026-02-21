"""ASGI app for Telegram webhook: POST /webhook receives updates."""

from telegram import Update
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import PlainTextResponse, Response
from starlette.routing import Route


def create_webhook_app(application):
    """
    Create Starlette app that forwards POST /webhook to PTB update_queue.
    application: telegram.ext.Application (with updater=None).
    """

    async def webhook(request: Request) -> Response:
        if request.method != "POST":
            return PlainTextResponse("Method not allowed", status_code=405)
        try:
            data = await request.json()
        except Exception:
            return PlainTextResponse("Invalid JSON", status_code=400)
        await application.update_queue.put(
            Update.de_json(data=data, bot=application.bot)
        )
        return Response(status_code=200)

    async def health(_: Request) -> PlainTextResponse:
        return PlainTextResponse("ok")

    return Starlette(
        routes=[
            Route("/webhook", webhook, methods=["POST"]),
            Route("/health", health, methods=["GET"]),
        ]
    )
