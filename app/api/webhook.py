# app/api/webhook.py
from fastapi import APIRouter, Request
from app.services.command_handler import handle_command, users_in_report_mode, users_in_ask_mode
from app.services.telegram_client import send_message, answer_callback_query, send_document
from app.services.excel_logging import EXCEL_FILE
from app.models.telegram_update import Update
import httpx
from app.core.config import setting
from pathlib import Path

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
        await answer_callback_query(callback_query_id=callback_id, text="Please wait for a moment.", show_alert=True)
        
        # Handle the callback data
        if data == "issue_report":
            users_in_report_mode.add(user)
            await send_message(
                chat_id, 
                "<b>Please type your issue report below.</b>\n\nInclude the following details where applicable:\n• What happened (symptoms and impact)\n• When it happened (date, time, and shift)\n• Equipment impacted\n• Lot ID (if relevant)\n• Any alarms, error codes, or log messages\n\n<b><u><i>The more specific the information, the faster we can triage and support.</i></u></b>",
                parse_mode="HTML"
            )
        elif data == "ask_question":
            users_in_ask_mode.add(user)
            await send_message(
                chat_id,
                "<b>Please type your question below.</b>\n\nYou can ask about equipment, processes, or facility-related queries, and I'll do my best to assist you!",
                parse_mode="HTML"
            )
        elif data == "download_logs":
            log_file = Path(EXCEL_FILE)
            if not log_file.exists():
                await send_message(chat_id, "No logs available yet.")
            else:
                await send_document(
                    chat_id=chat_id,
                    file_path=str(log_file),
                    caption="Here is the latest issue log file."
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