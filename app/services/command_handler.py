from app.services.telegram_client import send_message
# from app.services.openai_client import analyze_report, query_knowledge_base, refresh_vector_db
from app.services.openai_client import handle_issue_report, type_classification
from app.services.excel_logging import log_report_to_excel
from app.core.config import setting

# Track users in report mode
users_in_report_mode = set()
# users_in_ask_mode = set()

supervisor_chat_id = setting.supervisor_chat_id

# Handle command
async def handle_command(chat_id: int, user: str, text: str) -> bool:
    global users_in_report_mode
    
    if text.startswith("/start"):
        reply_markup = {
            "inline_keyboard": [
                [
                    {"text": "Submit Report", "callback_data": "issue_report"},
                    {"text": "Ask Bot", "callback_data": "ask_question"}
                ]
            ]
        }
        await send_message(chat_id, f"<b>Welcome, {user}!</b>\n\nWrite any equipment, process, or facility issues here for timely follow-up.\n\nSelect an option below to proceed:", reply_markup=reply_markup, parse_mode="HTML")

        return True
    
    # Check if user is in report mode
    if user in users_in_report_mode:
        # Process the report
        await send_message(chat_id, "<b>Wait for a second, analyzing your report!</b>", parse_mode="HTML")
        
        # Send to OpenAI to give immediate solution 
        ai_result = await handle_issue_report(text, user_info={"username": user})
        await send_message(
            chat_id,
            f"<b>Analysis Result:</b>\n\n{ai_result}",
            parse_mode="HTML"
        )

        classification = await type_classification(text)
        if classification and classification.get("success"):
            # Loge to the excel file
            await log_report_to_excel(
                reporter=user, 
                type = classification["type"].split(",")[0].strip(),
                equipment = classification["type"].split(",")[1].strip(),
                issue_summary = classification["type"].split(",")[2].strip(),
                severity = classification["type"].split(",")[3].strip()
            )

            if classification["type"].split(",")[3].strip().lower() in ["critical", "high"]:
                # Send alert to supervisor
                if supervisor_chat_id:
                    await send_message(
                        supervisor_chat_id,
                        f"🚨 <b>Critical Issue Reported</b> 🚨\n\n<b>Reporter:</b> {user}\n<b>Type:</b> {classification['type'].split(',')[0].strip()}\n<b>Equipment:</b> {classification['type'].split(',')[1].strip()}\n<b>Issue Summary:</b> {classification['type'].split(',')[2].strip()}\n<b>Severity:</b> {classification['type'].split(',')[3].strip()}\n\nPlease review and take necessary action immediately.",
                        parse_mode="HTML"
                    )
                print ("🚨 Critical issue reported, alert sent to supervisor! 🚨")

        else:
            await send_message(chat_id, "Error classifying report. Please try again.")
        
        # Remove user from report mode
        users_in_report_mode.discard(user)
        return True
    
    # elif user in users_in_ask_mode:
    #     # Auto refresh vector DB
    #     await refresh_vector_db()

    #     # Process the question
    #     await send_message(chat_id, "<b>Wait for a second, searching for answers!</b>", parse_mode="HTML")
        
    #     # Query knowledge base
    #     ai_answer = await query_knowledge_base(text)
        
    #     await send_message(
    #         chat_id,
    #         f"<b>Answer to your question:</b>\n\n{ai_answer}",
    #         parse_mode="HTML"
    #     )
        
    #     # Remove user from ask mode
    #     users_in_ask_mode.discard(user)
    #     return True
    
    return False