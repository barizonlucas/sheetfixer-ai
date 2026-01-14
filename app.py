import streamlit as st
import os
import json
import requests
from dotenv import load_dotenv

# 1. Configuração da Página (Sempre a primeira linha)
st.set_page_config(
    page_title="SheetFixer.AI",
    page_icon="🤖",
    layout="centered"
)

# 2. Carrega variáveis
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

# --- Internacionalização (i18n) ---
def load_translation(language):
    try:
        path = f"locales/{language}.json"
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        return {} # Retorna vazio para não quebrar se falhar

language_options = {
    "🇬🇧 English": "en",
    "🇧🇷 Português": "pt",
    "🇪🇸 Español": "es"
}

if 'language' not in st.session_state:
    st.session_state.language = "🇬🇧 English"

with st.sidebar:
    st.header("SheetFixer.AI")
    selected_language_name = st.radio(
        "Language / Idioma",
        options=list(language_options.keys()),
        index=1 # Começa em Português
    )
    st.divider()
    st.markdown("Developed by Lucas Barizon")

language_code = language_options[selected_language_name]
lang = load_translation(language_code)

# Fallback de textos caso o JSON falhe
def t(key, default):
    return lang.get(key, default)

# --- Backend (REST API Direta) ---
def generate_solution_rest(problem, tool, api_key):
    if not api_key:
        return "⚠️ Erro: API Key não encontrada. Configure o arquivo .env ou Secrets."

    # AQUI ESTÁ A MÁGICA: Usando o modelo 2.5 que você descobriu
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    
    headers = {"Content-Type": "application/json"}
    
    # Prompt Otimizado
    prompt_completo = f"""
    ROLE: Senior Spreadsheet Expert.
    TASK: Provide solution for '{tool}'.
    LANGUAGE: Respond in {selected_language_name}.
    USER PROBLEM: {problem}
    RULES: 1. Code/Formula ONLY. 2. Brief explanation.
    """

    payload = {
        "contents": [{"parts": [{"text": prompt_completo}]}]
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            return response.json()['candidates'][0]['content']['parts'][0]['text']
        else:
            return f"❌ Erro do Google ({response.status_code}): {response.text}"
            
    except Exception as e:
        return f"❌ Erro de Conexão: {str(e)}"

# --- Frontend ---
st.title("SheetFixer.AI 🤖")
st.caption(t("caption", "Seu assistente inteligente de planilhas"))

with st.container(border=True):
    tool = st.selectbox(
        t("tool_selector_label", "Ferramenta"),
        ("Excel", "Google Sheets", "VBA", "Apps Script")
    )

    user_problem = st.text_area(
        t("problem_description_label", "Descreva o problema"),
        height=150,
        placeholder="Ex: Somar A e B..."
    )

    if st.button(t("generate_solution_button", "Gerar Solução"), type="primary", use_container_width=True):
        if not user_problem:
            st.warning("Descreva o problema primeiro.")
        else:
            with st.spinner("Processando..."):
                # Chama a função que usa o link do 2.5
                solution = generate_solution_rest(user_problem, tool, api_key)
                
                if "Erro" in solution:
                    st.error(solution)
                else:
                    st.subheader("Solução:")
                    st.code(solution)