import httpx
from app.core.config import setting

async def analyze_report (report_text: str) -> dict:
    """
    Send the report message from user to OpenAI API for analysis.
    Return structured data about the issue.
    """

    # Define classification categories
    allowed_types = ["DATA_PROB", "HARDWARE", "SOFTWARE", "MISMATCH", "OTHERS", "UNSURE"]

    # # Define the system prompt for the OpenAI model
    system_prompt = (
        "You have an expertise in classifying any issues in Semiconductor manufacturing daily operations.\n"
        "You will receive a report from a user describing an issue they are facing.\n"
        "Analyze the report and classify the issue into multiple fields.\n\n"
        "There are 3 fields to return, such as types of issues (following pre-defined types), equipment affected (if any), and summary of the issue in one sentence.\n\n"
        "For the given issue report, return as a STRING separated by comma.\n\n"
        "Details of the 3 fields to return:\n"
        "1) Types of issues: classify the issue into one of the predefined types.\n"
        f"Allowed issue types: {', '.join(allowed_types)}.\n"
        "Category definitions:\n"
        "- DATA_PROB: any data mismatch, logging, count errors, recipe name mismatch, etc.\n"
        "- HARDWARE: any physical failures, sensors, motors, arms, grippers, mechanical jams, etc.\n"
        "- SOFTWARE: any software bugs, configuration, version issues, communication errors, etc.\n"
        "- MISMATCH: any ID / lane / lot mismatch type cases, etc.\n"
        "- OTHERS: anything that clearly does not fit above.\n"
        "- UNSURE: description too vague to decide.\n\n"
        "2) Equipment affected: specify the equipment name or ID if mentioned in the report, otherwise return 'Unknown'.\n\n"
        "3) Summary: provide a concise one-sentence summary of the issue described in the report.\n"
    )


    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers = {
                    "Authorization": f"Bearer {setting.openai_api_key}",
                    "Content-Type": "application/json"
                },
                json = {
                    "model": "gpt-4o-mini",
                    "messages": [
                        {
                            "role":"system",
                            "content": system_prompt
                            
                        },
                        {
                            "role":"user",
                            "content": f"Analyze this issue report: {report_text}"
                        }
                    ],
                    "temperature": 0.1,
                }
            )

            result = response.json()
            if response.status_code != 200:
                raise Exception(f"OpenAI API error: {result}")
            
            ai_response = result['choices'][0]['message']['content']
            return {
                "issue_report": report_text,
                "type": ai_response,
                "success": True
            }
        
    except Exception as e:
        return {
            "issue_report": report_text,
            "ai_analysis": str(e),
            "success": False
        }  