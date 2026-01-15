import streamlit as st
import os
import json
import requests
from dotenv import load_dotenv
import re

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
        # Fallback para inglês se a tradução não for encontrada
        try:
            with open("locales/en.json", "r", encoding="utf-8") as file:
                return json.load(file)
        except FileNotFoundError:
            return {} # Retorna vazio para não quebrar se falhar

language_options = {
    "🇬🇧 English": "en",
    "🇧🇷 Português": "pt",
    "🇪🇸 Español": "es"
}

# Define o idioma padrão na session_state se não existir
if 'language' not in st.session_state:
    st.session_state.language = "🇧🇷 Português" # Default to Portuguese

# UI da Sidebar
with st.sidebar:
    st.header("SheetFixer.AI")
    
    # Mapeia o código do idioma para o nome completo para o selectbox
    lang_names = list(language_options.keys())
    # Encontra o índice do idioma atual na session_state
    current_lang_index = lang_names.index(next((name for name, code in language_options.items() if code == st.session_state.language), "🇧🇷 Português"))

    selected_language_name = st.radio(
        "Language / Idioma",
        options=lang_names,
        index=current_lang_index
    )
    # Atualiza o estado da sessão quando o usuário muda o idioma
    st.session_state.language = language_options[selected_language_name]

    st.divider()
    st.markdown("Developed by Lucas Barizon")

# Carrega a tradução com base no estado da sessão
lang = load_translation(st.session_state.language)

# Função de tradução com fallback
def t(key, default):
    return lang.get(key, default)

# --- Backend (REST API Direta) ---
def generate_solution_rest(problem, tool, api_key, language_name):
    if not api_key:
        return {"error": t("error_api_key_not_found", "⚠️ API Key não encontrada. Configure o arquivo .env.")}

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    
    # Prompt otimizado para exigir uma resposta JSON
    prompt_completo = f"""
    ROLE: Senior Spreadsheet Expert.
    TASK: Provide a JSON-only response for a '{tool}' problem.
    LANGUAGE: The content of the JSON fields must be in {language_name}.
    USER PROBLEM: "{problem}"
    
    OUTPUT FORMAT: Your response MUST be a single, raw JSON object (no markdown, no extra text, no code block markers like ```json).
    The JSON object must have the following keys:
    - "code": A string containing ONLY the formula or code script.
    - "explanation": A brief, one or two-sentence summary of what the solution does.
    - "tips": A short list of strings with step-by-step instructions on how to apply the solution.

    EXAMPLE RESPONSE:
    {{
        "code": "=SUM(A1:A10)",
        "explanation": "This formula calculates the sum of all values in cells A1 through A10.",
        "tips": ["Click on the cell where you want the result.", "Type the formula and press Enter."]
    }}
    """

    payload = {
        "contents": [{"parts": [{"text": prompt_completo}]}]
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=120)
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"❌ {t('error_google_api', 'Erro do Google')} ({response.status_code}): {response.text}"}
            
    except requests.exceptions.RequestException as e:
        return {"error": f"❌ {t('error_connection', 'Erro de Conexão')}: {str(e)}"}

# --- Frontend ---
st.title("SheetFixer.AI 🤖")
st.caption(t("caption", "Seu assistente inteligente para planilhas"))

with st.container(border=True):
    tool = st.selectbox(
        t("tool_selector_label", "Selecione a Ferramenta"),
        ("Excel", "Google Sheets", "VBA", "Apps Script"),
        key="tool_selector"
    )

    user_problem = st.text_area(
        t("problem_description_label", "Descreva seu problema ou dúvida"),
        height=150,
        placeholder=t("problem_placeholder", "Ex: Como somar os valores da coluna A se a coluna B for 'Pago'?"),
        key="problem_input"
    )

    if st.button(t("generate_solution_button", "Gerar Solução"), type="primary", use_container_width=True):
        if not user_problem:
            st.warning(t("warning_describe_problem", "Por favor, descreva o problema antes de gerar uma solução."))
        else:
            with st.spinner(t("spinner_processing", "Analisando o problema e gerando a melhor solução...")):
                api_response = generate_solution_rest(user_problem, tool, api_key, selected_language_name)
                
                if "error" in api_response:
                    st.error(api_response["error"])
                else:
                    try:
                        # Extrai o texto da resposta da IA
                        raw_text = api_response['candidates'][0]['content']['parts'][0]['text']
                        
                        # Limpa a resposta de possíveis blocos de markdown
                        clean_text = re.sub(r'```json\s*|\s*```', '', raw_text).strip()
                        
                        # Converte o texto JSON para um dicionário Python
                        solution_dict = json.loads(clean_text)

                        # Exibe a UI melhorada
                        st.success(t("success_solution_generated", "Solução Gerada com Sucesso!"))

                        # 1. Código/Fórmula
                        st.markdown(f"### {t('header_code', 'Código ou Fórmula')}")
                        st.code(solution_dict.get("code", t("info_not_found", "Não encontrado")), language='vbnet' if tool == "VBA" else 'javascript' if tool == "Apps Script" else 'plaintext')
                        
                        # 2. Explicação
                        st.markdown(f"### {t('header_explanation', 'Explicação')}")
                        st.markdown(solution_dict.get("explanation", t("info_not_found", "Não encontrada")))

                        # 3. Dicas de Aplicação
                        with st.expander(f"📝 {t('expander_how_to_apply', 'Como aplicar a solução')}"):
                            tips = solution_dict.get("tips", [])
                            if tips:
                                for i, tip in enumerate(tips, 1):
                                    st.markdown(f"{i}. {tip}")
                            else:
                                st.info(t("info_no_tips", "Nenhuma dica de aplicação foi fornecida."))

                    except (json.JSONDecodeError, KeyError, IndexError, TypeError) as e:
                        st.error(t("error_processing_response", "Ocorreu um erro ao processar a resposta da IA. A resposta pode estar em um formato inesperado."))
                        st.code(f"{t('label_error_details', 'Detalhes do Erro')}: {e}\n\n{t('label_raw_response', 'Resposta Bruta Recebida:')}\n{api_response.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '')}", language='text')
