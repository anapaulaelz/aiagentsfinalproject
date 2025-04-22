import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"
HEADERS = {
    "Authorization": f"Bearer {GROQ_API_KEY}",
    "Content-Type": "application/json"
}

def build_prompt(cv_text):
    return f"""
You are an AI assistant specialized in processing resumes (CVs). Your task is to extract structured data from raw, unstructured text.

Return only valid JSON, no text outside the JSON. Fill any missing info with "--" or empty lists. Handle variations and synonyms in section titles (like "Education" = "Studies", "Institution" = "University", etc.).

Output format:
{{
  "Personal Information": {{
    "Full Name": "--",
    "Email": "--",
    "Phone": "--",
    "Location": "--",
    "Age": "--",
    "Marital Status": "--"
  }},
  "Education": [
    {{
      "Degree": "--",
      "Field": "--",
      "Institution": "--",
      "Graduation Year": "--"
    }}
  ],
  "Languages": [],
  "Professional Experience": [
    {{
      "Company": "--",
      "Total Years in Company": "--",
      "Position": "--",
      "Years in Position": "--",
      "Achievements and Responsibilities": "--",
      "Internal Rotation": "--"
    }}
  ],
  "Other Achievements": [
    {{
      "Type": "--",
      "Title": "--",
      "Institution": "--",
      "Year": "--"
    }}
  ],
  "Current Compensation": {{
    "Gross Salary": "--",
    "Net Salary": "--",
    "Compensation Type": "--"
  }}
}}

Now extract this from the following CV:

\"\"\"
{cv_text}
\"\"\"
"""

def extract_cv_data(cv_text):
    body = {
        "model": "llama3-8b-8192",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": build_prompt(cv_text)}
        ],
        "temperature": 0.3
    }

    try:
        response = requests.post(ENDPOINT, headers=HEADERS, json=body)
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        return json.loads(content)
    except Exception as e:
        print("❌ Error:", e)
        return {}
