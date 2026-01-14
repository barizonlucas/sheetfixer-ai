# SheetFixer.AI 🤖

SheetFixer.AI is a smart spreadsheet assistant that helps you generate formulas and scripts for Excel, Google Sheets, VBA, and Apps Script.

## Features

-   **Smart Assistant:** Describe your problem in plain English and get the right formula or code.
-   **Multi-language Support:** The interface is available in English, Portuguese, and Spanish.
-   **Tool Support:** Supports Excel, Google Sheets, VBA, and Apps Script.

## How to Run

1.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Set up your environment:**
    Create a `.env` file in the root of the project and add your Gemini API key:
    ```
    GEMINI_API_KEY='YOUR_KEY_HERE'
    ```

3.  **Run the app:**
    ```bash
    streamlit run app.py
    ```

## Internationalization (i18n)

The application is internationalized to support multiple languages.

### Adding a new language

1.  **Create a new translation file:**
    -   In the `locales/` directory, create a new JSON file named with the two-letter language code (e.g., `fr.json` for French).
    -   Copy the content of `locales/en.json` and translate the values.

2.  **Update the language selector:**
    -   In `app.py`, add the new language to the `language_options` dictionary:
        ```python
        language_options = {"English": "en", "Português": "pt", "Español": "es", "Français": "fr"}
        ```

That's it! The application will now support the new language.
