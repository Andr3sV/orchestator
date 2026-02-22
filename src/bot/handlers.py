"""Telegram bot handlers: /start and text messages to the orchestrator."""

import asyncio
import logging
import unicodedata
from datetime import datetime, timezone

from telegram import Update
from telegram.ext import ContextTypes
from langchain_core.messages import AIMessage, HumanMessage

from src.graph.state import EmailDraft
from src.graph.graph import get_app

logger = logging.getLogger(__name__)

# Pending email drafts by chat_id (confirm before sending)
pending_email_drafts: dict[int, EmailDraft] = {}

# Normalized (lowercase, no accents) confirmation words
CONFIRM_KEYWORDS = frozenset({
    "si", "confirmo", "envia", "enviar", "yes", "send", "ok", "dale", "confirm",
})


def _normalize_for_confirm(text: str) -> str:
    """Lowercase, strip, remove accents for confirmation check."""
    t = text.strip().lower()
    nfkd = unicodedata.normalize("NFKD", t)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def _is_confirmation(text: str) -> bool:
    """True if the user is confirming send (avoid 'no envíes' etc.)."""
    norm = _normalize_for_confirm(text)
    if not norm:
        return False
    if norm.startswith(("no ", "no\n", "no,")) or norm == "no":
        return False
    return norm in CONFIRM_KEYWORDS


START_MESSAGE = """Hola, soy tu miniequipo de marketing.

Puedes preguntarme:
• **Copy**: escribe textos para emails, anuncios o campañas (ej: "redacta un email para lanzar un producto").
• **Estrategia**: ideas de canales, planes de marketing, campañas (ej: "cómo debería promocionar en LinkedIn").
• **Agenda**: qué tienes hoy o un día concreto en tu calendario (ej: "qué tengo hoy", "qué hay en mi agenda").
• **Email**: envía un email por Gmail (te muestro resumen y confirmas antes de enviar; ej: "envía un email a X con asunto Y diciendo Z").

Escribe en lenguaje natural y te dirijo al experto adecuado."""


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start."""
    if update.message:
        await update.message.reply_text(START_MESSAGE, parse_mode="Markdown")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle text: confirm pending email or run graph and reply."""
    if not update.message or not update.message.text:
        return
    text = update.message.text.strip()
    if not text:
        return
    chat_id = update.effective_chat.id if update.effective_chat else 0

    # 1) Pending draft: check confirmation
    draft = pending_email_drafts.get(chat_id)
    if draft is not None:
        if _is_confirmation(text):
            try:
                from src.gmail.send import send_email
                send_email(draft["to"], draft["subject"], draft["body"])
                del pending_email_drafts[chat_id]
                await update.message.reply_text("Email enviado.")
            except Exception as e:
                logger.exception("Error sending email")
                await update.message.reply_text(
                    "No pude enviar el email; revisa permisos o intenta más tarde."
                )
            return
        # Not confirmation: cancel draft and continue to graph
        del pending_email_drafts[chat_id]

    # 2) Invoke graph (thread_id = chat:date for 24h conversation window)
    try:
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        thread_id = f"{chat_id}:{date_str}"
        config = {
            "configurable": {"thread_id": thread_id},
            "metadata": {"telegram_chat_id": str(chat_id)},
        }
        app = get_app()
        result = await asyncio.to_thread(
            app.invoke,
            {"messages": [HumanMessage(content=text)]},
            config=config,
        )
        messages = result.get("messages", [])
        last = None
        for m in reversed(messages):
            if isinstance(m, AIMessage):
                last = m
                break
        reply = (last.content if last and last.content else "") or "No pude generar una respuesta. Intenta de nuevo."

        # 3) If graph returned email_draft, store and reply with summary
        email_draft = result.get("email_draft")
        if email_draft and isinstance(email_draft, dict) and email_draft.get("to"):
            pending_email_drafts[chat_id] = EmailDraft(
                to=email_draft["to"],
                subject=email_draft.get("subject") or "(Sin asunto)",
                body=email_draft.get("body") or "",
            )
            # Reply is already the summary (last AIMessage) with "Responde 'sí' para enviar"

        await update.message.reply_text(reply)
    except Exception as e:
        logger.exception("Error processing message")
        await update.message.reply_text("Algo falló. Intenta más tarde o reformula tu mensaje.")
