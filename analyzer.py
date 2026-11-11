import os
import requests
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

api_key = os.getenv("GEMINI_API_KEY")

# Check if API key is present
if not api_key:
    print("❌ ERROR: GEMINI_API_KEY not found in .env file.")
    print(f"Looked in: {env_path}")
    exit(1)


def parse_log_file(file_path):
    """Reads the log file and extracts lines with [ERROR] or [FATAL]."""
    errors = []
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                if "[ERROR]" in line or "[FATAL]" in line:
                    errors.append(line.strip())
        return errors
    except FileNotFoundError:
        print(f"❌ ERROR: Log file '{file_path}' not found.")
        return []


def get_ai_solution(errors_list):
    """Sends extracted errors to Gemini AI and gets solutions."""
    if not errors_list:
        return "No errors found."

    errors_text = "\n".join(errors_list)
    prompt = f"""
    You are an expert IC Design and EDA Automation engineer.
    Analyze the following simulation errors and provide a brief explanation and possible solution for each.
    Format your response in Markdown, with a clear heading for each error.
    
    Errors:
    {errors_text}
    """
    
    # Gemini API endpoint and headers
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent"
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": api_key
    }
    payload = {
        "contents": [
            {"parts": [{"text": prompt}]}
        ]
    }

    try:
        # 15-second timeout to prevent hanging
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()
        return data['candidates'][0]['content']['parts'][0]['text']
    except requests.exceptions.RequestException as e:
        return f"❌ Network/API Error: {e}"


def save_report(report_text, output_file="QA_Report.md"):
    """Saves the AI response into a Markdown report."""
    with open(output_file, 'w', encoding='utf-8') as file:
        file.write(report_text)
    print(f"✅ Report successfully saved to '{output_file}'.")


if __name__ == "__main__":
    log_file = "sample_run.log"
    
    # Parse errors from the log
    extracted_errors = parse_log_file(log_file)
    
    # Send to AI and save output if errors are found
    if extracted_errors:
        print(f"🔍 Found {len(extracted_errors)} error(s). Sending to Gemini AI...")
        ai_report = get_ai_solution(extracted_errors)
        save_report(ai_report)
    else:
        print("ℹ️ No errors found in the log file.")