# app/api/webhook.py
from fastapi import APIRouter, Request
from app.services.command_handler import handle_command
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
        callback_id = callback.id
        chat_id = callback.message.chat.id
        data = callback.data

        # Answer the callback query first (removes loading animation)
        async with httpx.AsyncClient() as client:
            await client.post(
                f"https://api.telegram.org/bot{setting.telegram_token}/answerCallbackQuery",
                json={
                    "callback_query_id": callback_id,
                    "text": "Wait for a moment. We are still proecessing your request !",
                    "show_alert" : True
                }
            )
        
        # Handle the callback data
        if data == "issue_report":
            await send_message(chat_id, "You can just type your issue report here. Our AI system will analyze it shortly and send it to our database.")
        
        return {"ok": True}


    # Handle message 
    message = update.message or update.edited_message
    if not message:
        return {"ok": True}

    chat_id = message.chat.id
    user = message.from_user.username or message.from_user.id
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