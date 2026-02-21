"""Telegram bot handlers: /start and text messages to the orchestrator."""

import asyncio
import logging

from telegram import Update
from telegram.ext import ContextTypes
from langchain_core.messages import AIMessage

from src.graph.state import create_initial_state
from src.graph.graph import get_app

logger = logging.getLogger(__name__)

START_MESSAGE = """Hola, soy tu miniequipo de marketing.

Puedes preguntarme:
• **Copy**: escribe textos para emails, anuncios o campañas (ej: "redacta un email para lanzar un producto").
• **Estrategia**: ideas de canales, planes de marketing, campañas (ej: "cómo debería promocionar en LinkedIn").
• **Agenda**: qué tienes hoy o un día concreto en tu calendario (ej: "qué tengo hoy", "qué hay en mi agenda").

Escribe en lenguaje natural y te dirijo al experto adecuado."""


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start."""
    if update.message:
        await update.message.reply_text(START_MESSAGE, parse_mode="Markdown")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle text: run graph and reply with assistant message."""
    if not update.message or not update.message.text:
        return
    text = update.message.text.strip()
    if not text:
        return
    chat_id = update.effective_chat.id if update.effective_chat else 0
    try:
        state = create_initial_state(text)
        app = get_app()
        # Run sync invoke in thread to not block the event loop
        result = await asyncio.to_thread(app.invoke, state, config={"metadata": {"telegram_chat_id": str(chat_id)}})
        messages = result.get("messages", [])
        last = None
        for m in reversed(messages):
            if isinstance(m, AIMessage):
                last = m
                break
        if last and last.content:
            await update.message.reply_text(last.content)
        else:
            await update.message.reply_text("No pude generar una respuesta. Intenta de nuevo.")
    except Exception as e:
        logger.exception("Error processing message")
        await update.message.reply_text("Algo falló. Intenta más tarde o reformula tu mensaje.")
