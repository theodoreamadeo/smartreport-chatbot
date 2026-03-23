import httpx
import asyncio
import json
from app.core.config import setting
from app.services.vector_db import vector_db
from datetime import date

# PDF Knowledge Base
async def handle_issue_report (issue_description: str, user_info: dict) -> str:
    """Handle issue report with immediate solution."""
    
    try:
        # 1. Query vector database for relevant knowledge
        relevant_docs = vector_db.query_pdf_knowledge_base(issue_description, n_results=3)

        # 2. Build context from retrieved documents
        if relevant_docs:
            context = "\n\n".join([
                f"Reference {i+1} (from {doc['metadata']['source']}, page {doc['metadata']['page']}):\n{doc['text']}"
                for i, doc in enumerate(relevant_docs)
            ])
        else:
            context = "No relevant documents found in the knowledge base."
        
        # 3. Generate solution using OpenAI
        prompt = f"""
You are a technical support assistant. Output MUST be valid Telegram HTML (parse_mode="HTML").
Do NOT use Markdown. Do NOT use unsupported tags.
Allowed tags only: <b>, <i>, <u>, <s>, <code>, <pre>, <a>.

Issue:
{issue_description}

Knowledge Base Context:
{context}

Return the answer in this exact structure (same headings and order):

<b>Issue summary</b>
1-2 sentences.

<b>Likely cause</b>
1-3 bullet points using plain text lines that start with "• " (do not use <ul>/<li>).

<b>Step-by-step fix</b>
Numbered steps using plain text lines that start with "1) ", "2) ", etc.
Each step should be one action, with the expected result where helpful.

<b>Warnings / best practices</b>
Bullet points using lines that start with "• ".

Formatting rules:
- Escape HTML special characters in user/context content: & -> &amp;, < -> &lt;, > -> &gt;.
- Keep total length under 3500 characters if possible.
- If the KB context is insufficient, say so under <b>Likely cause</b> and propose the minimum info needed.
"""

        # 4. Send to OpenAI for analysis
        async with httpx.AsyncClient(timeout=120) as client:
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
                                "You are an expert assistant helping to analyze user-submitted issue reports.\n"
                                "Use the provided relevant reports to formulate a concise and accurate response."
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

            if response.status_code != 200:
                error_detail = response.json() if response.text else response.status_code
                raise Exception(f"OpenAI API error (status {response.status_code}): {error_detail}")
            
            result = response.json()
            ai_response = result['choices'][0]['message']['content']
            return ai_response
    
    except Exception as e:
        error_msg = f"Error analyzing issue report: {str(e)}"
        import traceback
        traceback.print_exc()
        return error_msg

async def type_classification (issue_description: str) -> dict:
    """Return structured data about the issue"""

    # Define classification categories
    allowed_types = ["DATA_PROB", "HARDWARE", "SOFTWARE", "MISMATCH", "OTHERS", "UNSURE"]
    allowed_severities = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]

    # Define the system prompt for the OpenAI model
    system_prompt = (
        "You have an expertise in classifying any issues in Semiconductor manufacturing daily operations.\n"
        "You will receive a report from a user describing an issue they are facing.\n"
        "Analyze the report and classify the issue into multiple fields.\n\n"
        "There are 4 fields to return, such as types of issues (following pre-defined types), equipment affected (if any), summary of the issue in one sentence, and severity level.\n\n"
        "For the given issue report, return as a STRING separated by comma.\n\n"
        "Details of the 4 fields to return:\n"
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
        "3) Summary: provide a concise one-sentence summary of the issue described in the report.\n\n"
        "4) Severity: classify the severity of the issue into one of the predefined levels.\n"
        f"Allowed severity levels: {', '.join(allowed_severities)}.\n"
        "You must choose only from the allowed severity levels based on the impact of the issue on production operations. If the report does not provide enough information to determine severity, choose the most appropriate level based on the potential impact.\n"
        "Severity definitions:\n"
        "- CRITICAL: Production stopped or major system failure affecting many machines or the whole line Multiple AMRs failing, conveyor system down, transfer system blocked for many stations.\n"
        "- HIGH: Machine or process cannot run but limited to one area or tool AMR cannot find path, tray not detected, handler error. Drop traystack, ic scattered, traystack damaged.\n"
        "- MEDIUM: Process delay or waiting condition but production still possible Waiting for lot, material handling delay. AMR hit.\n"
        "- LOW: Informational messages or coordination messages Requesting pictures, status updates, area blocking for maintenance. AMR DEADLOCK, AMR HANG, Traystack abnormality.TS no lot association, AMR cobot gripper fail lead to no association.\n"
        "Return format: <type>, <equipment>, <summary>, <severity>\n"
        "Example: HARDWARE, AMR002, AMR002 is deadlocked at station 5 and blocking the production line, CRITICAL\n"
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
                            "content": f"Analyze this issue report: {issue_description}"
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
                "issue_report": issue_description,
                "type": ai_response,
                "success": True
            }
        
    except Exception as e:
        return {
            "issue_report": issue_description,
            "ai_analysis": str(e),
            "success": False
        }

today = date.today().isoformat()

# Query the Excel knowledge base for relevant information
async def handle_logging_query (question: str) -> str:
    timeout = httpx.Timeout(connect=10.0, read=90.0, write=30.0, pool=30.0)
    retries = 3
    last_error = None

    try:
        # Search vector database
        relevant_docs = vector_db.query_excel_knowledge_base(question, n_results=5)

        if relevant_docs:
            context = "\n\n".join([
                f"Record {i+1}:\n{doc['text']}"
                for i, doc in enumerate(relevant_docs)
            ])
        else:
            context = "No matching records found in the issue history."
        
        # User prompt for OpenAI
        prompt = f"""
You are a data analyst assistant for a semiconductor manufacturing operation.
You have access to historical issue records logged by operators.
Answer the user's question using ONLY the records provided below.

Today's date: {today}

Question: {question}

Historical Records:
{context}

Rules:
- Use Telegram HTML only: <b>, <i>, <u>, <code>
- Never use <br>; use newline characters only.
- Do NOT use Markdown
- If records are insufficient, say so and state what info is missing
- Keep the answer under 3000 characters
"""

        # Query OpenAI with context
        for attempt in range(1, retries + 1):
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.post(
                        "https://api.openai.com/v1/chat/completions",
                        headers={
                            "Authorization": f"Bearer {setting.openai_api_key}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": "gpt-4o-mini",
                            "messages": [
                                {"role": "system", "content": "You are an expert assistant helping to answer user questions based on historical issue reports."},
                                {"role": "user", "content": prompt}
                            ],
                            "temperature": 0.3
                        }
                    )

                result = response.json()
                if response.status_code != 200:
                    raise Exception(f"OpenAI API error: {result}")

                return result["choices"][0]["message"]["content"]
            except httpx.ReadTimeout as e:
                last_error = e
                if attempt < retries:
                    await asyncio.sleep(1.5 * attempt)
                else:
                    return "The AI service is taking too long to respond right now. Please try again in a moment."
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"Error querying knowledge base: {e}"
    
# Refresh the vector database from the latest Excel logs
async def refresh_vector_db () -> bool:
    try:
        vector_db.load_excel_to_vectordb()
        return True
    except Exception as e:
        print(f"Error refreshing vector DB: {e}")
        return False