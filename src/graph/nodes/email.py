"""Email agent node: extract or draft to/subject/body and return structured draft for confirmation."""

import re

from langchain_core.messages import SystemMessage, AIMessage, HumanMessage

from src.agents.llm import get_llm
from src.agents.prompts import EMAIL_SYSTEM
from src.graph.state import GraphState, EmailDraft


def _parse_llm_email_response(content: str) -> EmailDraft | None:
    """Parse 'To: ...\\nSubject: ...\\nBody: ...' format. Returns None if parse fails."""
    if not content or not content.strip():
        return None
    to_match = re.search(r"^\s*To:\s*(.+?)(?=\n|$)", content, re.IGNORECASE | re.DOTALL)
    subj_match = re.search(r"^\s*Subject:\s*(.+?)(?=\n|$)", content, re.IGNORECASE | re.MULTILINE)
    body_match = re.search(r"Body:\s*(.+)", content, re.IGNORECASE | re.DOTALL)
    if not to_match:
        return None
    to_val = to_match.group(1).strip()
    if not to_val or "@" not in to_val:
        return None
    subject_val = (subj_match.group(1).strip() if subj_match else "").strip() or "(Sin asunto)"
    body_val = (body_match.group(1).strip() if body_match else "").strip() or ""
    return EmailDraft(to=to_val, subject=subject_val, body=body_val)


def _make_summary_message(draft: EmailDraft, lang: str = "es") -> str:
    """Build user-friendly summary for Telegram with confirm prompt."""
    if lang == "es":
        return (
            f"Voy a enviar este email:\n\n"
            f"**Para:** {draft['to']}\n"
            f"**Asunto:** {draft['subject']}\n"
            f"**Cuerpo:**\n{draft['body']}\n\n"
            "Responde 'sí' o 'confirmo' para enviar."
        )
    return (
        f"I will send this email:\n\n"
        f"**To:** {draft['to']}\n"
        f"**Subject:** {draft['subject']}\n"
        f"**Body:**\n{draft['body']}\n\n"
        "Reply 'yes' or 'confirm' to send."
    )


def email_node(state: GraphState) -> dict:
    """Extract or draft email fields from user message; return summary + email_draft."""
    messages = state.get("messages") or []
    if not messages:
        return {
            "messages": [AIMessage(content="No tengo el mensaje. Indica a quién y qué quieres enviar.")],
            "email_draft": None,
        }
    last = messages[-1]
    user_content = getattr(last, "content", None) or ""
    if isinstance(user_content, list):
        user_content = str(user_content)

    llm = get_llm()
    response = llm.invoke([
        SystemMessage(content=EMAIL_SYSTEM),
        HumanMessage(content=user_content),
    ])
    raw = (response.content or "").strip()
    draft = _parse_llm_email_response(raw)

    if draft is None:
        return {
            "messages": [
                AIMessage(
                    content="No pude extraer destinatario, asunto y cuerpo del mensaje. "
                    "Prueba diciendo: 'envía un email a juan@gmail.com con asunto X diciendo que...'"
                )
            ],
            "email_draft": None,
        }

    # Detect language from user message for summary
    lang = "es" if any(c in "áéíóúñ¿¡" for c in user_content.lower()) or "envía" in user_content.lower() or "mandar" in user_content.lower() else "en"
    summary = _make_summary_message(draft, lang)
    return {
        "messages": [AIMessage(content=summary)],
        "email_draft": draft,
    }
