# app/api/webhook.py
from fastapi import APIRouter, Request
from app.services.command_handler import handle_command, users_in_report_mode
from app.services.telegram_client import send_message
from app.models.telegram_update import Update
import httpx
from app.core.config import setting

router = APIRouter()

# Local only: Set webhook endpoint (will not be used in production)
@router.post("/set-webhook")
async def set_webhook(request: Request):
    """Set the Telegram webhook URL. Call this once with your ngrok URL."""
    body = await request.json()
    webhook_url = body.get("url")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"https://api.telegram.org/bot{setting.telegram_token}/setWebhook",
            json={"url": webhook_url}
        )
        return response.json()

@router.post("/webhook")
async def telegram_webhook(update: Update):

    if update.callback_query is not None:
        callback = update.callback_query
        print (f"Received callback query: {callback}")
        callback_id = callback.id
        chat_id = callback.message.chat.id
        data = callback.data
        user = f"{callback.from_user.first_name or ''} {callback.from_user.last_name or ''}".strip() or str(callback.from_user.username)

        # Answer the callback query first
        async with httpx.AsyncClient() as client:
            await client.post(
                f"https://api.telegram.org/bot{setting.telegram_token}/answerCallbackQuery",
                json={
                    "callback_query_id": callback_id,
                    "text": "Preparing report form...",
                    "show_alert": False
                }
            )
        
        # Handle the callback data
        if data == "issue_report":
            users_in_report_mode.add(user)
            await send_message(
                chat_id, 
                "📝 Please type your issue report below.\n\nInclude:\n• What happened\n• When it happened\n• Any error messages\n\nI'll analyze it with AI!"
            )
        
        return {"ok": True}


    # Handle message 
    message = update.message or update.edited_message
    if not message:
        return {"ok": True}

    chat_id = message.chat.id
    user = f"{message.from_user.first_name or ''} {message.from_user.last_name or ''}".strip() or str(message.from_user.username)
    text = message.text
    if not text:
        return {"ok": True}

    # delegate to command handler
    handled = await handle_command(chat_id=chat_id, user=str(user), text=text)

    # If not handled, you can either ignore or add default behavior
    if not handled:
        # Example: ignore silently
        return {"ok": True}

    return {"ok": True}