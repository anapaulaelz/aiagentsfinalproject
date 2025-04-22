# Resume Standarizer

![BPMN Diagram](BPMN_AP.png)

## Description
An AI-powered tool built with **Streamlit** to help HR departments standardize and extract structured data from multiple CVs (PDF or Word). It uses **Groq’s LLaMA3-8B** via **LangChain** to extract key fields like education, experience, and compensation, even when CV formats vary.

The interface includes:
+ File upload (max 5 CVs/session)
+ Kanban board to track CV status: Unreviewed, Incomplete, Ready
+ Editor interface for field review and correction
+ Download of standardized CVs in `.xlsx`, `.docx`, `.pdf` or `.zip`
+ Multilingual language selection
+ Visual validation of required fields with real-time feedback

## Tech Stack

- **Frontend:** Streamlit + custom CSS
- **Backend:** Python, LangChain, Groq API
- **Parsing:** PyPDF2, python-docx
- **Exporting:** openpyxl, python-docx, ReportLab
- **Environment:** dotenv

## Project Structure
.
├── app.py                 # Streamlit interface
├── exporter.py            # Export functions (.xlsx, .docx, .pdf, .zip)
├── extractor_groq.py      # Prompt and request to Groq LLM
├── leer_cvs.py            # File parser for PDFs and DOCX
├── requirements.txt
├── README.md
├── .env                   # (Not shared) with GROQ_API_KEY
└── logo.png               # TalentWise HR logo
