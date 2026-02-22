"""Email agent node: extract or draft to/subject/body and return structured draft for confirmation."""

import re

from langchain_core.messages import SystemMessage, AIMessage, HumanMessage

from src.agents.llm import get_llm
from src.agents.prompts import EMAIL_SYSTEM, EMAIL_SYSTEM_FROM_DRAFT_BODY
from src.graph.state import GraphState, EmailDraft, get_recent_messages


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
    """Extract or draft email fields from user message or from previous agent output (e.g. copy) as body."""
    messages = state.get("messages") or []
    if not messages:
        return {
            "messages": [AIMessage(content="No tengo el mensaje. Indica a quién y qué quieres enviar.")],
            "email_draft": None,
        }
    recent = get_recent_messages(messages)
    last = messages[-1]
    from_previous_agent = isinstance(last, AIMessage)
    user_content = getattr(last, "content", None) or ""
    if isinstance(user_content, list):
        user_content = str(user_content)

    original_request = ""
    for m in recent:
        if not isinstance(m, AIMessage) and getattr(m, "content", None):
            original_request = str(m.content).strip()
            break

    system = EMAIL_SYSTEM_FROM_DRAFT_BODY if (from_previous_agent and user_content) else EMAIL_SYSTEM
    llm = get_llm()
    response = llm.invoke([
        SystemMessage(content=system),
        *recent,
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

    # Detect language for summary (prefer original user request)
    lang_ref = original_request or user_content
    lang = "es" if any(c in "áéíóúñ¿¡" for c in (lang_ref or "").lower()) or "envía" in (lang_ref or "").lower() or "mandar" in (lang_ref or "").lower() else "en"
    summary = _make_summary_message(draft, lang)
    return {
        "messages": [AIMessage(content=summary)],
        "email_draft": draft,
    }
