from flask import Blueprint, request, Response, stream_with_context
from flask_jwt_extended import jwt_required

from ..extensions import db
from chat_api.models import Message
from chat_api.models.job_card import JobCard

from ..service.title_gen import generate_chat_title
from ..service.message_stream import stream_bot_reply

from ..utils.chat_utils import chat_brief, current_user_id, get_chat_if_owner
from ..utils.response_utils import api_ok, api_error
from ..utils.message_utils import message_dto

from flasgger import swag_from
from chat_api.service.docs_path import doc

message_bp = Blueprint("message", __name__)

@message_bp.route("/chats/<int:chat_id>/messages", methods=["GET"])
@swag_from(doc("message", "get_messages.yml"))
@jwt_required()
def get_messages(chat_id):
    user_id = current_user_id()
    chat = get_chat_if_owner(chat_id, user_id)
    if not chat:
        return api_error("chat not found", 404)

    messages = (
        Message.query
        .filter_by(chat_id=chat_id)
        .order_by(Message.created_at.asc())
        .all()
    )

    messages_data = []
    for m in message_dto_list(messages):
        messages_data.append(m)

    data = {
        "chat": chat_brief(chat),
        "messages": messages_data,
    }
    return api_ok(data=data, message="ok", http_status=200)


def message_dto_list(messages: list) -> list:
    result = []
    for m in messages:
        dto = message_dto(m)

        if m.role == "assistant":
            card_row = JobCard.query.filter_by(message_id=m.message_id).first()
            if card_row:
                dto["job_cards"] = card_row.cards_json
                dto["is_marked"] = card_row.is_marked
            else:
                dto["job_cards"] = None
                dto["is_marked"] = False

        result.append(dto)
    return result


@message_bp.route("/chats/<int:chat_id>/messages", methods=["POST"])
@swag_from(doc("message", "create_message.yml"))
@jwt_required()
def create_message(chat_id):
    user_id = current_user_id()
    chat = get_chat_if_owner(chat_id, user_id)
    if not chat:
        return api_error("chat not found", 404)

    data = request.get_json(silent=True) or {}
    content = (data.get("content") or "").strip()
    if not content:
        return api_error("content is required", 400)

    user_msg = Message(
        chat_id=chat_id,
        content=content,
        role="user",
    )
    db.session.add(user_msg)

    title_changed = False
    if not chat.title or chat.title in ("New Chat", "چت جدید"):
        new_title = generate_chat_title(content)
        if new_title and new_title != chat.title:
            chat.title = new_title
            title_changed = True

    db.session.commit()

    return Response(
        stream_with_context(
            stream_bot_reply(chat, user_msg, content, user_id, title_changed)
        ),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
