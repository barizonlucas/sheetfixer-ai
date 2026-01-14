import os
import google.generativeai as genai
from dotenv import load_dotenv

def configure_ai_client():
    """
    Configures the Generative AI client with the API key from environment variables.
    """
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment variables. Please create a .env file and add it.")
    genai.configure(api_key=api_key)

def generate_solution(problem_description: str, tool: str = "Excel/Google Sheets") -> str:
    """
    Generates a solution for a spreadsheet problem using the Gemini API.

    Args:
        problem_description: A string describing the user's problem.
        tool: The specific tool the user is working with (e.g., "Excel", "VBA").

    Returns:
        A string containing the generated formula or script.
    """
    try:
        configure_ai_client()
        model = genai.GenerativeModel('gemini-2.5-flash')

        prompt = f"""
        You are a spreadsheet expert specializing in {tool}. Your task is to help users solve problems in their spreadsheets.

        Analyze the problem described by the user and provide the most suitable solution. The solution can be:
        1. A formula (for Excel or Google Sheets, specify if there is a difference).
        2. A script (VBA for Excel or Apps Script for Google Sheets).

        **Instructions for the response:**
        - Be direct and clear.
        - If it is a formula, provide the exact formula and briefly explain how to use it.
        - If it is a script, provide the complete and well-commented code, with clear instructions on how to add it and use it in the spreadsheet.
        - Indicate which software the solution applies to (Excel, Google Sheets, or both).
        - If the problem is ambiguous, ask for more details, but try to provide a general solution based on what was described.
        - Keep the response focused on the solution. Do not add greetings or unnecessary comments.

        **User Problem:**
        "{problem_description}"

        **Your Solution:**
        """

        response = model.generate_content(prompt)
        return response.text

    except Exception as e:
        return f"An error occurred while generating the solution: {e}"