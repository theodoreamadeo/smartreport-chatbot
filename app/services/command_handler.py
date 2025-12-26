from app.services.telegram_client import send_message

# Handle command
async def handle_command(chat_id: int, user: str, text: str):
    """
    Decide what to do based on the incoming command text.
    Returns True if handled, False if ignored.
    """
    # Command: /start to show the features
    # Need to polish the wording
    if text.startswith("/start"):

        reply_markup = {
            "inline_keyboard": [
                [
                    {"text": "Ask", "url": "https://www.google.com/"},
                    {"text": "Report", "callback_data": "issue_report"},
                ]
            ]
        }
        await send_message(chat_id, "Choose an option:", reply_markup=reply_markup)
        return {"ok": True}
    
    # Not a known command
    return False