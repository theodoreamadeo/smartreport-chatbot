from app.services.telegram_client import send_message
# from app.services.openai_client import analyze_report, query_knowledge_base, refresh_vector_db
from app.services.openai_client import handle_issue_report
# from app.services.excel_logging import log_report_to_excel

# Track users in report mode
users_in_report_mode = set()
# users_in_ask_mode = set()

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
        
        # Send to OpenAI
        ai_result = await handle_issue_report(text, user_info={"username": user})
        await send_message(
            chat_id,
            f"<b>Analysis Result:</b>\n\n{ai_result}",
            parse_mode="HTML"
        )
        print (ai_result)
        # print (f"ai_result: {ai_result}")
        
        # if ai_result and ai_result.get("success"):
        #     # Log to Excel
        #     logged = await log_report_to_excel(
        #         reporter=user,
        #         type = ai_result["type"].split(",")[0].strip(),
        #         equipment = ai_result["type"].split(",")[1].strip(),
        #         issue_summary = ai_result["type"].split(",")[2].strip()
        #     )
            
            # Development: Print AI result
            # if logged:
            #     await send_message(
            #         chat_id,
            #         f"<b>Report submitted successfully!</b>\n\n<b>Result:</b>\n• Reporter: {user}\n• Type: {ai_result['type'].split(',')[0].strip()}\n• Equipment: {ai_result['type'].split(',')[1].strip()}\n• Issue Summary: {ai_result['type'].split(',')[2].strip()}\n\nThank you for your report. Our team will review it and get back to you if needed.",
            #         parse_mode="HTML"
            #     )
            # else:
            #     await send_message(chat_id, "Error saving report. Please try again.")
        # else:
        #     await send_message(chat_id, "Error analyzing report. Please try again.")
        
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