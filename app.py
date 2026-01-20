import streamlit as st
import os
import json
import requests
from dotenv import load_dotenv
import re

# 1. Page Configuration (MUST BE THE FIRST STREAMLIT COMMAND)
st.set_page_config(
    page_title="Ekual",
    page_icon="🟰",
    layout="centered"
)

# 2. Load Environment Variables
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
BMC_LINK = os.getenv("BMC_LINK")
PIX_QR_PATH = os.getenv("PIX_QR_PATH")

# --- Internationalization (i18n) ---
def load_translation(language_code):
    """Loads the JSON translation file for the specified language code."""
    try:
        path = f"locales/{language_code}.json"
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}  # Return empty if file not found

LANGUAGE_OPTIONS = {
    "🇬🇧 English": "en",
    "🇧🇷 Português": "pt",
    "🇪🇸 Español": "es"
}

# Set default language in session state
if 'language_code' not in st.session_state:
    st.session_state.language_code = "pt"

# Callback to update language immediately upon selection
def update_language():
    st.session_state.language_code = LANGUAGE_OPTIONS[st.session_state.selected_language]

# --- SIDEBAR: Configuration and Support ---
with st.sidebar:
    st.header("Ekual 🟰")
    
    # Language Selector
    # Find the key (e.g., "🇧🇷 Português") based on the current value (e.g., "pt")
    current_label = next(
        (k for k, v in LANGUAGE_OPTIONS.items() if v == st.session_state.language_code),
        "🇧🇷 Português"
    )
    
    st.radio(
        "Language / Idioma",
        options=list(LANGUAGE_OPTIONS.keys()),
        index=list(LANGUAGE_OPTIONS.keys()).index(current_label),
        key="selected_language",
        on_change=update_language
    )
    
    st.divider()
    
    # --- MONETIZATION AREA ---
    st.markdown("### ☕ Apoie o projeto")
    
    if st.session_state.language_code == "pt":
        # Pix Logic (Show image if exists, otherwise show key)
        st.markdown("🇧🇷 **Pix (Brasil):**")
        if os.path.exists(PIX_QR_PATH):
            st.image(PIX_QR_PATH, caption="Escaneie para doar", width="stretch")
        else:
            # Fallback if image fails to load
            st.code("lucasbarizon@gmail.com", language="text")
    else:
        # Buy Me a Coffee Button for non-PT languages
        st.markdown(f"""
        <a href="{BMC_LINK}" target="_blank">
            <img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 40px !important;width: 145px !important;" >
        </a>
        """, unsafe_allow_html=True)
            
    st.divider()
    st.caption("Powered by Lucas Bariza")

# Load translations
translations = load_translation(st.session_state.language_code)

def t(key, default):
    """Helper function to get translation or default value."""
    return translations.get(key, default)

# --- BACKEND: REST API (Gemini 2.5 Flash) ---
def generate_solution(problem, tool, api_key, lang_code):
    """Generates a solution using the Gemini API."""
    if not api_key:
        return {"error": "⚠️ API Key não encontrada. Verifique o arquivo .env."}

    # Direct URL for Gemini 2.5 Flash
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    
    # Map language code to full name for the prompt
    language_map = {"pt": "Portuguese", "en": "English", "es": "Spanish"}
    full_lang = language_map.get(lang_code, "English")

    full_prompt = f"""
    ROLE: You are Ekual, a world-class spreadsheet expert in {tool}.
    TASK: Solve the user's problem strictly.
    OUTPUT FORMAT: JSON ONLY. No markdown blocks.
    JSON KEYS:
    - "code": The exact formula or script code.
    - "explanation": A concise explanation (max 2 lines) in {full_lang}.
    - "tips": A list of 2 short actionable tips or steps to apply the solution in {full_lang}.

    USER PROBLEM: {problem}
    """

    payload = {
        "contents": [{"parts": [{"text": full_prompt}]}]
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            try:
                return response.json()['candidates'][0]['content']['parts'][0]['text']
            except (KeyError, IndexError):
                return {"error": "Erro ao ler resposta da IA."}
        else:
            return {"error": f"Erro do Google ({response.status_code}): {response.text}"}
            
    except Exception as e:
        return {"error": f"Erro de Conexão: {str(e)}"}

# --- FRONTEND: Interface ---
st.title("Ekual 🟰")

# Dynamic Slogan
SLOGANS = {
    "en": "Your question becomes a formula.",
    "pt": "Sua dúvida vira fórmula.",
    "es": "Tu duda se convierte en fórmula."
}
st.subheader(SLOGANS.get(st.session_state.language_code, SLOGANS["en"]))

with st.container(border=True):
    selected_tool = st.selectbox(
        t("tool_selector_label", "Qual ferramenta?"),
        ("Excel", "Google Sheets", "VBA", "Google Apps Script")
    )

    problem_description = st.text_area(
        t("problem_description_label", "Descreva o problema"),
        height=120,
        placeholder=t("problem_placeholder", "Ex: Quero somar a coluna A...")
    )

    if st.button(t("generate_solution_button", "✨ Ekualizar"), type="primary", width="stretch"):
        if not problem_description:
            st.warning(t("warning_msg", "Descreva o problema primeiro."))
        else:
            with st.spinner(t("spinner_msg", "Ekualizando...")):
                raw_response = generate_solution(problem_description, selected_tool, API_KEY, st.session_state.language_code)
                
                if isinstance(raw_response, dict) and "error" in raw_response:
                    st.error(raw_response["error"])
                else:
                    try:
                        # Clean JSON (Remove ```json and ```)
                        clean_text = re.sub(r'```json\s*|\s*```', '', raw_response).strip()
                        response_data = json.loads(clean_text)
                        
                        # Display Results
                        st.success(t("success_msg", "Solução Encontrada!"))
                        
                        # 1. Code/Formula
                        st.markdown(f"**{t('code_label', 'Fórmula / Código')}:**")
                        
                        lang_syntax = "excel"
                        if "Script" in selected_tool:
                            lang_syntax = "javascript"
                        elif "VBA" in selected_tool:
                            lang_syntax = "vbnet"
                            
                        st.code(response_data.get("code", ""), language=lang_syntax)
                        
                        # 2. Explanation
                        st.info(f"💡 **Explicação:** {response_data.get('explanation', '')}")
                        
                        # 3. Tips
                        with st.expander(f"📝 {t('tips_label', 'Passo a passo')}"):
                            for tip in response_data.get("tips", []):
                                st.markdown(f"- {tip}")
                                
                        # 4. Final CTA
                        st.markdown("---")
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.caption(t("donate_caption", "Ajudou? Pague um café!"))
                        with col2:
                            st.link_button("☕ Café", BMC_LINK)

                    except json.JSONDecodeError:
                        st.error("Erro ao processar resposta da IA.")
                        st.write(raw_response)  # Debug

# Footer
st.markdown("---")
st.markdown("<div style='text-align: center; color: gray;'>Lucas Bariza © 2026</div>", unsafe_allow_html=True)