import streamlit as st
import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

# 1. Configuração da Página (DEVE SER A PRIMEIRA COISA)
st.set_page_config(
    page_title="SheetFixer.AI",
    page_icon="🤖",
    layout="centered"
)

# 2. Carrega variáveis e API Key
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

# --- Lógica de Internacionalização (i18n) ---
def load_translation(language):
    try:
        path = f"locales/{language}.json"
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        st.error(f"Arquivo de idioma não encontrado: locales/{language}.json")
        st.stop()

# Seletor de Idioma (Agora no lugar certo, na Sidebar para não poluir)
language_options = {
    "🇬🇧 English": "en",
    "🇧🇷 Português": "pt",
    "🇪🇸 Español": "es"
}

if 'language' not in st.session_state:
    st.session_state.language = "🇬🇧 English"

with st.sidebar:
    selected_language_name = st.radio(
        "Language / Idioma",
        options=list(language_options.keys()),
        index=0
    )
    st.divider()

language_code = language_options[selected_language_name]
lang = load_translation(language_code)

# Atualiza textos da sidebar
st.sidebar.markdown(lang.get("sidebar_content", "Instructions..."))

# --- Backend (IA) ---
def get_language_for_tool(tool):
    if tool in ["VBA", "Excel"]:
        return "vbnet"
    elif tool in ["Google Sheets", "Apps Script"]:
        return "javascript"
    return "plaintext"

def generate_solution(problem, tool):
    if not api_key:
        return "⚠️ API Key missing. Please configure .env or Secrets."

    # Configuração Blindada da IA
    try:
        genai.configure(api_key=api_key)
        
        system_instruction = f"""
        ROLE: Senior Spreadsheet Expert.
        TASK: Provide the exact formula or code for '{tool}'.
        LANGUAGE: Respond in {selected_language_name}.
        RULES:
        1. ONLY the code/formula.
        2. Brief explanation (1 line).
        3. No conversational filler.
        """
        
        # Tentativa com o modelo Flash (Rápido)
        # Se falhar, você pode trocar por 'gemini-1.5-pro' ou 'gemini-pro' para testar
        model = genai.GenerativeModel(
            model_name='gemini-1.5-flash',
            system_instruction=system_instruction
        )
        
        response = model.generate_content(f"Problem: {problem}")
        return response.text
        
    except Exception as e:
        return f"Error: {str(e)}"

# --- Frontend (Interface) ---
st.title(lang["title"])
st.caption(lang["caption"])

with st.container(border=True):
    tool = st.selectbox(
        lang["tool_selector_label"],
        ("Excel", "Google Sheets", "VBA", "Apps Script")
    )

    user_problem = st.text_area(
        lang["problem_description_label"],
        height=150,
        placeholder=lang["problem_description_placeholder"]
    )

    if st.button(lang["generate_solution_button"], type="primary", use_container_width=True):
        if not user_problem:
            st.warning(lang["warning_message"])
        else:
            with st.spinner(lang["spinner_text"]):
                solution = generate_solution(user_problem, tool)
                
                if solution:
                    if "Error:" in solution or "404" in solution:
                        st.error(solution)
                        st.info("Dica: Se o erro 404 persistir, tente gerar uma NOVA API Key no Google AI Studio.")
                    else:
                        st.subheader(lang["solution_subheader"])
                        st.code(solution, language=get_language_for_tool(tool))