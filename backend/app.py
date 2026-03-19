import os
import json
import requests
import re
import logging
import io
import pandas as pd
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
BMC_LINK = os.getenv("BMC_LINK", "https://buymeacoffee.com/default")
PIX_QR_PATH = os.getenv("PIX_QR_PATH", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# Load allowed CORS origins from env, fallback to local dev endpoints if empty
CORS_ORIGINS_STR = os.getenv("CORS_ORIGINS", "")
if CORS_ORIGINS_STR:
    origins = [origin.strip() for origin in CORS_ORIGINS_STR.split(",")]
else:
    origins = ["http://localhost:5173", "http://127.0.0.1:5173"]

# Logging configuration to record technical errors
LOG_FILE_PATH = os.getenv("LOG_FILE_PATH", "ekual_errors.log")
logging.basicConfig(
    filename=LOG_FILE_PATH,
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Ekual API")

# CORS configuration to allow requests from the React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(set(origins)),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class GenerateRequest(BaseModel):
    problem: str
    tool: str
    lang_code: str

class ExportRequest(BaseModel):
    sample_data: List[Dict[str, Any]]

@app.get("/api/config")
def get_config():
    """Returns environment configurations (e.g., donation links)"""
    return {
        "bmc_link": BMC_LINK,
        "has_pix_image": os.path.exists(PIX_QR_PATH) if PIX_QR_PATH else False
    }

@app.get("/api/locales/{lang_code}")
def get_locales(lang_code: str):
    """Provides translations based on the requested language"""
    # Basic sanitization to prevent directory traversal
    safe_lang_code = re.sub(r'[^a-zA-Z0-9_-]', '', lang_code)
    locales_dir = os.path.join(os.path.dirname(__file__), "locales")
    
    try:
        with open(os.path.join(locales_dir, f"{safe_lang_code}.json"), "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        try:
            # Fallback to English
            with open(os.path.join(locales_dir, "en.json"), "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return {} # Defensive return if fallback is also missing

@app.post("/api/export-excel")
def export_excel(request: ExportRequest):
    """Generates an in-memory Excel file from the formatted sample data and returns it for download"""
    try:
        df = pd.DataFrame(request.sample_data)
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Sample')
            
            # Forces formula recognition for compatibility with Google Sheets
            ws = writer.sheets['Sample']
            for row in ws.iter_rows():
                for cell in row:
                    if isinstance(cell.value, str) and cell.value.startswith('='):
                        cell.value = cell.value  # Triggers openpyxl setter (data_type='f')
        
        output.seek(0)
        headers = {
            'Content-Disposition': 'attachment; filename="ekual_sample.xlsx"'
        }
        
        return StreamingResponse(output, headers=headers, media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    except Exception as e:
        logger.error(f"Error generating Excel file: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Oops! An error occurred while generating the sample spreadsheet.")

@app.post("/api/generate")
def generate_solution(request: GenerateRequest):
    if not API_KEY:
        logger.error("Gemini API_KEY not found in the environment (.env).")
        raise HTTPException(status_code=500, detail="Oops! Our server is having a configuration issue at the moment. Please try again later.")
        
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={API_KEY}"
    headers = {"Content-Type": "application/json"}
    
    LANGUAGE_MAP = {"pt": "Portuguese (Brazil)", "en": "English", "es": "Spanish"}
    target_lang = LANGUAGE_MAP.get(request.lang_code, "English")

    full_prompt = f"""
    # ROLE
    You are Ekual, a high-performance Spreadsheet Agent. Your goal is to provide precise formulas or scripts for Excel 365 and Google Sheets.
    TARGET LANGUAGE: {target_lang} (Use this for ALL text fields in the JSON, except code_en).

    # PRIORITY DIRECTIVE
    1. ABSOLUTE PRIORITY: Solve the user's specific request. Do NOT suggest unrelated functions (like UNIQUE or FILTER) unless they are strictly necessary for the user's problem.
    2. If the user asks for text formatting (e.g., Capitalize), do NOT provide data counting/summarization.

    # EXECUTION RULES
    - SEPARATOR: If request.lang_code == "pt", ALWAYS use semicolon (;) for formulas in the "code" key. If "en", use comma (,).
    - LANGUAGE: If "pt", use translated function names (e.g., PROCV, SE, PRI.MAIUSC) in the "code" key.
    - SCOPE: Assume datasets can exceed 1000 rows. Prefer column references (A:A) or Table references.
    - SAFETY: If the solution uses Dynamic Arrays, add a note about the #SPILL! (#DESPEJAR!) error.

    # OUTPUT STRUCTURE (JSON ONLY)
    Return a JSON object with these exact keys:
    - "code": The clean formula or script formatted according to the user's language rules ({target_lang}).
    - "code_en": The exact same formula but STRICTLY in English, using English function names (e.g., IF, VLOOKUP) and comma (,) as the separator.
    - "explanation": A technical, concise breakdown for a professional peer, STRICTLY in {target_lang}. Use **bold** for function names. Use \\n\\n for spacing. No "AI fluff" (e.g., "Certainly!", "I hope this helps").
    - "tips": A list of 2 brief, actionable technical tips, STRICTLY in {target_lang}.
    - "sample_data": A list of dictionaries representing 5 rows of realistic sample data related to the problem. The keys must be the column names. The last column MUST contain the suggested formula as a string starting exactly with '=' and using relative row references (like A2, B2). CRITICAL: The formula inside sample_data MUST be the "code_en" version (English functions and comma separator) to ensure correct Excel file generation.

    # TONE & STYLE
    - Professional, direct, and zero-redundancy.
    - No "for dummies" language. Talk to the user like a Senior Manager.

    USER PROBLEM: {request.problem}
    """

    payload = {
        "contents": [{"parts": [{"text": full_prompt}]}],
        "generationConfig": {"responseMimeType": "application/json"}
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=60)
        if resp.status_code != 200:
            logger.error(f"Gemini API Error (Status {resp.status_code}): {resp.text}")
            raise HTTPException(status_code=500, detail="The AI couldn't respond right now. Please try again in a few moments.")
            
        raw_text = resp.json()['candidates'][0]['content']['parts'][0]['text']
        clean_text = re.sub(r'```json\s*|\s*```', '', raw_text).strip()
        return json.loads(clean_text, strict=False)
    except HTTPException:
        # Rethrow explicitly handled HTTPExceptions
        raise
    except Exception as e:
        logger.error(f"Internal processing error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Oops! Something went wrong on our servers. The error has been logged.")