import os
import requests
from pathlib import Path
from dotenv import load_dotenv

# Գտնում ենք .env ֆայլը
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("❌ ԽՆԴԻՐ: GEMINI_API_KEY-ը չի գտնվել .env ֆայլում:")
    exit()

def parse_log_file(file_path):
    errors = []
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                if "[ERROR]" in line or "[FATAL]" in line:
                    errors.append(line.strip())
        return errors
    except FileNotFoundError:
        print(f"❌ Ֆայլը չի գտնվել: {file_path}")
        return []

def get_ai_solution(errors_list):
    if not errors_list:
        return "Սխալներ չեն գտնվել:"

    errors_text = "\n".join(errors_list)
    prompt = f"""
    You are an expert IC Design and EDA Automation engineer.
    Analyze the following simulation errors and provide a brief explanation and possible solution for each.
    Format your response in Markdown, with a clear heading for each error.
    
    Errors:
    {errors_text}
    """
    
    # Ուղղակի HTTP REST API հարցում Google Gemini API-ին
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [
            {"parts": [{"text": prompt}]}
        ]
    }

    try:
        # timeout=15-ը երաշխավորում է, որ 15 վայրկյանից ավել անիմաստ չի կախվի
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()
        return data['candidates'][0]['content']['parts'][0]['text']
    except requests.exceptions.RequestException as e:
        return f"❌ Ցանցային/API Սխալ: {e}"

def save_report(report_text, output_file="QA_Report.md"):
    with open(output_file, 'w', encoding='utf-8') as file:
        file.write(report_text)
    print(f"✅ Հաշվետվությունը հաջողությամբ պահպանվեց '{output_file}' ֆայլում:")

if __name__ == "__main__":
    extracted_errors = parse_log_file("sample_run.log")
    if extracted_errors:
        print(f"Գտնվել է {len(extracted_errors)} սխալ, ուղարկում ենք AI-ին...")
        ai_report = get_ai_solution(extracted_errors)
        save_report(ai_report)
    else:
        print("Սխալներ չկան:")