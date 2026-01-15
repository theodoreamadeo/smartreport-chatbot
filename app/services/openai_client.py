import httpx
from app.core.config import setting
from app.services.vector_db import vector_db

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
        "- DATA_PROB: issues caused by incorrect, missing, delayed, or inconsistent data in the system. Example: TRAYSTACK TRANSFERRED TO MINI ERK BUT DATA STILL AT AMR002.\n"
        "- HARDWARE: issues caused by physical equipment or components malfunctioning. Such as amr misplacing traystacks and amr deadlock, hanging at a certain point or emergency stopping.\n"
        "- SOFTWARE: issues caused by application logic, system code, or configuration errors. Usually associated with robot arm or gripper arm. \n"
        "- MISMATCH: occurs when barcode data on a physical box does not tally with the backend system at Infineon Technologies.  Issue also may occurs when the traystack is placed on ERK and the backend system does not detect any association to the traystack. Can occur in DPP and ERK.\n"
        "- OTHERS: issues where the root cause has not yet been identified. Such as Insufficient information Investigation still ongoing. \n"
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

# Query the Excel knowledge base for relevant information
async def query_knowledge_base (question: str) -> str:
    try:
        # Search vector database
        relevant_docs = vector_db.search(question, n_results=5)

        if not relevant_docs:
            return "No relevant information found in the knowledge base."
        
        # Build context from relevant reports
        context = "📊 <b>Relevant Historical Reports:</b>\n\n"
        for i, report in enumerate(relevant_docs, 1):
            context += f"<b>Report {i}:</b>\n{report['document']}\n\n"
        
        # User prompt for OpenAI
        prompt = f"""Based on the following historical issue reports, please answer the user's question.\n{context}\nUser Question: {question}\n\nPlease provide a concise and helpful answer based on the historical data above. If you notice patterns or trends, mention them."""

        # Query OpenAI with context
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
                            "content": (
                                "You are an expert assistant helping to answer user questions based on historical issue reports.\n"
                                "Use the provided relevant reports to formulate a concise and accurate answer to the user's question."
                            )
                        },
                        {
                            "role":"user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.5,
                }
            )

            result = response.json()
            if response.status_code != 200:
                raise Exception(f"OpenAI API error: {result}")
            
            ai_response = result['choices'][0]['message']['content']
            return ai_response
    
    except Exception as e:
        return f"Error querying knowledge base: {e}"

# Refresh the vector database from the latest Excel logs
async def refresh_vector_db () -> bool:
    try:
        vector_db.load_excel_to_vectordb()
        return True
    except Exception as e:
        print(f"Error refreshing vector DB: {e}")
        return False