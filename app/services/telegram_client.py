import httpx 
from typing import Any, Dict, Optional
from app.core.config import setting
from pathlib import Path

TELEGRAM_API_BASE = f"https://api.telegram.org/bot{setting.telegram_token}"

# Send message 
async def send_message (chat_id: int | str, text: str, reply_markup: Optional[Dict[str, Any]] = None, parse_mode: Optional[str] = None) -> None:
        
        # Prepare the json payload
        json_payload: Dict[str, Any] = {
            "chat_id": chat_id, 
            "text": text
        }

        if reply_markup is not None:
            json_payload["reply_markup"] = reply_markup

        if parse_mode is not None:
            json_payload["parse_mode"] = parse_mode
        
        async with httpx.AsyncClient(timeout=10) as client:
              response = await client.post(
                    f"{TELEGRAM_API_BASE}/sendMessage", 
                    json=json_payload
              )
              result = response.json()
              if not result.get("ok"):
                  print(f"Failed to send message: {result}")
              return result
        
async def answer_callback_query(
    callback_query_id: str,
    text: str | None = None,
    show_alert: bool = False,
) -> None:
    payload: Dict[str, Any] = {"callback_query_id": callback_query_id}
    if text is not None:
        payload["text"] = text
    if show_alert:
        payload["show_alert"] = True

    async with httpx.AsyncClient(timeout=10) as client:
        await client.post(f"{TELEGRAM_API_BASE}/answerCallbackQuery", json=payload)

async def send_document(chat_id: int | str, file_path: str, caption: str | None = None) -> None:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    data = {"chat_id": str(chat_id)}
    if caption:
        data["caption"] = caption

    async with httpx.AsyncClient(timeout=30) as client:
        with open(path, "rb") as f:
            files = {"document": (path.name, f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
            response = await client.post(f"{TELEGRAM_API_BASE}/sendDocument", data=data, files=files)
            result = response.json()
            if not result.get("ok"):
                print(f"Failed to send document: {result}")