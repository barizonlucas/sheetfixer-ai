import streamlit as st
import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

# --- Internationalization (i18n) ---
def load_translation(language):
    """Loads the translation file for the selected language."""
    path = f"locales/{language}.json"
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)

# Language selection with flags in the header
language_options = {
    "🇬🇧 English": "en",
    "🇧🇷 Português": "pt",
    "🇪🇸 Español": "es"
}
# Use session state to remember the selected language
if 'language' not in st.session_state:
    st.session_state.language = "🇬🇧 English"

selected_language_name = st.radio(
    "Language",
    options=list(language_options.keys()),
    horizontal=True,
    label_visibility="collapsed",
    key='language'
)
language_code = language_options[selected_language_name]
lang = load_translation(language_code)


# Streamlit page configuration
st.set_page_config(
    page_title=lang["page_title"],
    page_icon=lang["page_icon"],
    layout="centered"
)

# --- Sidebar ---
st.sidebar.header(lang["sidebar_title"])
st.sidebar.markdown(lang["sidebar_content"])


# --- Backend ---
def get_language_for_tool(tool):
    """Returns the language for st.code syntax highlighting."""
    if tool in ["VBA", "Excel"]:
        return "vbnet"
    elif tool in ["Google Sheets", "Apps Script"]:
        return "javascript"
    return "plaintext"

# Load API KEY and configure the model
try:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        st.error(lang["api_key_error"])
        st.stop()
    genai.configure(api_key=api_key)
except Exception as e:
    st.error(lang["api_config_error"].format(e=e))
    st.stop()


def generate_solution(problem, tool):
    """
    Calls the Gemini API to generate a solution for the user's problem.
    """
    system_instruction = f"""
    You are a Senior Spreadsheet Specialist. Your sole task is to provide the exact formula or code for the '{tool}' tool that solves the user's problem.
    **Strict Instructions:**
    1.  **DO NOT** use phrases like 'Sure, here is the formula', 'You can use the following code', or any other introduction.
    2.  Provide **ONLY** the formula or code block.
    3.  After the formula/code, add an **extremely brief** and direct explanation (1-2 lines maximum) of what it does.
    4.  DO NOT add usage examples or additional notes.
    Get straight to the point.
    """
    model = genai.GenerativeModel(
        model_name='gemini-1.5-flash',
        system_instruction=system_instruction
    )
    try:
        response = model.generate_content(f"Problem: {problem}")
        return response.text
    except Exception as e:
        st.error(lang["api_call_error"].format(e=e))
        return None

# --- Frontend Interface ---

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
        if user_problem and tool:
            with st.spinner(lang["spinner_text"]):
                solution = generate_solution(user_problem, tool)
                if solution:
                    st.subheader(lang["solution_subheader"])
                    language = get_language_for_tool(tool)
                    st.code(solution, language=language)
        else:
            st.warning(lang["warning_message"])

