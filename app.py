import streamlit as st
import uuid
import os
import re
from dotenv import load_dotenv
from leer_cvs import extract_text
from extractor_groq import extract_cv_data
from exporter import export_to_excel, export_to_word, export_to_pdf

# Load env variables
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

st.set_page_config(layout="wide")
st.title("Resume Standardizer")

# Logo ficticio TalentWise HR
st.markdown("""
    <div style="display: flex; justify-content: center; align-items: center; margin-bottom: 10px;">
        <img src= "logo.png" style="margin-right: 10px;">
        <span style="font-size: 20px; font-weight: bold; color: #1e293b;">TalentWise HR</span>
    </div>
""", unsafe_allow_html=True)

# Estilo visual Notion + azul-grisáceo
st.markdown("""
<style>
body {
    background-color: #f9fafb;
    font-family: 'Segoe UI', sans-serif;
}

h1 {
    text-align: center;
    font-size: 26px;
    color: #1e293b;
    margin-bottom: 20px;
}

h2, h3, h4 {
    color: #334155;
    font-size: 20px;
    text-align: center;
    margin-top: 10px;
    margin-bottom: 10px;
}

.card-section {
    background-color: #ffffff;
    border-radius: 14px;
    padding: 20px;
    margin-bottom: 20px;
    box-shadow: 0 2px 6px rgba(0,0,0,0.05);
}

input, textarea, select {
    border-radius: 10px !important;
    border: 1px solid #cbd5e1 !important;
}

label {
    font-weight: 500 !important;
    color: #1e293b !important;
}

button[kind="primary"] {
    background-color: #3b82f6 !important;
    color: white !important;
    border-radius: 10px !important;
    font-weight: 600;
    padding: 8px 20px;
}

button[kind="primary"]:hover {
    background-color: #2563eb !important;
}

.kanban-card {
    background-color: #f8fafc;
    border-radius: 12px;
    padding: 12px 16px;
    margin-bottom: 12px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.04);
    font-family: 'Segoe UI', sans-serif;
    font-size: 14px;
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.kanban-ready {
    border-left: 5px solid #22c55e;
}

.kanban-incomplete {
    border-left: 5px solid #facc15;
}

.kanban-unreviewed {
    border-left: 5px solid #94a3b8;
}

h3 {
    font-size: 18px;
    color: #1e293b;
    font-weight: 600;
}

.kanban-filename {
    font-weight: 600;
    color: #0f172a;
}

.stDownloadButton > button {
    border-radius: 10px;
    background-color: #0ea5e9;
    color: white;
    font-weight: 600;
}

.stDownloadButton > button:hover {
    background-color: #0284c7;
}
</style>
""", unsafe_allow_html=True)

# Session state setup
if "cvs" not in st.session_state:
    st.session_state.cvs = {}
if "selected_cv" not in st.session_state:
    st.session_state.selected_cv = None

REQUIRED_FIELDS = [
    "Full Name", "Email", "Phone", "Location", "Age", "Marital Status",
    "Education", "Languages", "Professional Experience", "Other Achievements", "Current Compensation"
]

def is_valid_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

def is_valid_phone(phone):
    return re.match(r"^[\d\+\-\(\) ]+$", phone)

def get_completion_errors(cv_data):
    errors = []
    try:
        pi = cv_data["Personal Information"]
        cc = cv_data["Current Compensation"]

        if not pi["Full Name"].strip():
            errors.append("Full Name")
        if not is_valid_email(pi["Email"]):
            errors.append("Email")
        if not is_valid_phone(pi["Phone"]):
            errors.append("Phone")
        if not pi["Location"].strip():
            errors.append("Location")
        if not pi["Age"].strip():
            errors.append("Age")
        if pi["Marital Status"].strip() == "--":
            errors.append("Marital Status")

        if not cv_data["Education"]:
            errors.append("Education")
        if not cv_data["Languages"]:
            errors.append("Languages")
        if not cv_data["Professional Experience"]:
            errors.append("Professional Experience")
        if not cv_data["Other Achievements"]:
            errors.append("Other Achievements")

        if not cc["Gross Salary"].strip() and not cc["Net Salary"].strip():
            errors.append("Salary")
    except Exception as e:
        errors.append(f"Invalid structure: {e}")
    return errors

# ------------- File Upload ------------------
import base64

# Custom uploader style
st.markdown("""
    <style>
    .custom-uploader .stFileUploader {
        border: 2px dashed #b0c4de;
        background-color: #f0f4fa;
        border-radius: 15px;
        padding: 30px;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
        width: 420px;
        margin: auto;
    }
    .custom-uploader .stFileUploader label {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 10px;
        font-family: 'Segoe UI', sans-serif;
        color: #333;
    }
    .custom-uploader .stFileUploader label::before {
        content: '\1F4C1';  /* folder 📁 */
        font-size: 40px;
        color: #4e8cff;
    }
    .custom-uploader .stFileUploader span {
        font-size: 18px;
    }
    </style>
""", unsafe_allow_html=True)

with st.container():
    with st.container():
        st.markdown("""<div class='custom-uploader'>""", unsafe_allow_html=True)
        uploaded_files = st.file_uploader(
            label="",
            type=["pdf", "docx"],
            accept_multiple_files=True,
            label_visibility="collapsed",
            key="upload_trigger"
        )
        st.markdown("""</div>""", unsafe_allow_html=True)

    if uploaded_files:
        for file in uploaded_files[:5 - len(st.session_state.cvs)]:
            if file.name in [cv["filename"] for cv in st.session_state.cvs.values()]:
                continue  # Avoid duplicates

            uid = str(uuid.uuid4())[:8]
            raw_text = extract_text(file)

            with st.spinner(f"Processing {file.name} with Groq..."):
                extracted_data = extract_cv_data(raw_text)

            if "Personal Information" in extracted_data:
                st.session_state.cvs[uid] = {
                    "filename": file.name,
                    "status": "incomplete",
                    "data": extracted_data
                }
            else:
                st.session_state.cvs[uid] = {
                    "filename": file.name,
                    "status": "incomplete",
                    "data": {}
                }

# ------------- Kanban Board ------------------
st.subheader("🗃️ CV Status Board")

st.markdown("""
<style>
.kanban-card {
    background-color: white;
    border-radius: 12px;
    padding: 10px 14px;
    margin-bottom: 12px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.06);
    font-family: 'Segoe UI', sans-serif;
    font-size: 14px;
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.kanban-card:hover {
    background-color: #f0f4ff;
}
.kanban-ready {
    border-left: 5px solid #4caf50;
}
.kanban-incomplete {
    border-left: 5px solid #ffc107;
}
.kanban-unreviewed {
    border-left: 5px solid #90a4ae;
}
.kanban-filename {
    font-weight: 600;
    margin: 0;
    padding: 0;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
</style>
""", unsafe_allow_html=True)

cols = st.columns(3)
statuses = ["unreviewed", "incomplete", "ready"]
titles = ["Unreviewed", "Incomplete", "Ready"]

sorted_items = sorted(
    st.session_state.cvs.items(),
    key=lambda x: (x[1]["status"] != "ready", x[1]["filename"])
)

for idx, status in enumerate(statuses):
    with cols[idx]:
        st.markdown(f"### {titles[idx]}")
        for uid, cv in sorted_items:
            if cv["status"] == status or (status == "unreviewed" and not cv["status"]):
                css_class = "kanban-card "
                css_class += (
                    "kanban-ready" if status == "ready"
                    else "kanban-incomplete" if status == "incomplete"
                    else "kanban-unreviewed"
                )

                with st.container():
                    colA, colB = st.columns([5, 1])
                    with colA:
                        st.markdown(f"<div class='{css_class}'><span class='kanban-filename'>📄 {cv['filename']}</span></div>", unsafe_allow_html=True)
                    with colB:
                        if st.button("✏️", key=f"select_{uid}"):
                            st.session_state.selected_cv = uid

                if status == "ready":
                    # Habilitar la opción de descarga
                    excel_path = f"exports/{uid}.xlsx"
                    word_path = f"exports/{uid}.docx"
                    pdf_path = f"exports/{uid}.pdf"
                    export_to_excel(cv["data"], excel_path)
                    export_to_word(cv["data"], word_path)
                    export_to_pdf(cv["data"], pdf_path)

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        with open(excel_path, "rb") as f:
                            st.download_button("⬇️ Excel", f, file_name=f"{cv['filename']}_standardized.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key=f"dl_excel_{uid}")
                    with col2:
                        with open(word_path, "rb") as f:
                            st.download_button("⬇️ Word", f, file_name=f"{cv['filename']}_standardized.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", key=f"dl_word_{uid}")
                    with col3:
                        with open(pdf_path, "rb") as f:
                            st.download_button("⬇️ PDF", f, file_name=f"{cv['filename']}_standardized.pdf", mime="application/pdf", key=f"dl_pdf_{uid}")

# ------------- CV Editor ------------------
if st.session_state.selected_cv:
    uid = st.session_state.selected_cv
    cv = st.session_state.cvs[uid]
    st.subheader(f"✏️ Editing: {cv['filename']}")

    if not cv["data"] or "Personal Information" not in cv["data"]:
        st.error("❌ This CV could not be processed correctly. Try re-uploading or editing manually.")
        st.stop()

    with st.form("edit_form", clear_on_submit=False):

        # 👤 Personal Info
        with st.container():
            st.markdown('<div class="card-section"><h4>👤 Personal Info</h4>', unsafe_allow_html=True)
            pi = cv["data"]["Personal Information"]
            col1, col2 = st.columns(2)
            with col1:
                pi["Full Name"] = st.text_input("Full Name", pi.get("Full Name", ""))
                pi["Phone"] = st.text_input("Phone", pi.get("Phone", ""))
                pi["Age"] = st.text_input("Age", pi.get("Age", ""))
            with col2:
                pi["Email"] = st.text_input("Email", pi.get("Email", ""))
                pi["Location"] = st.text_input("Location", pi.get("Location", ""))
                pi["Marital Status"] = st.selectbox("Marital Status", ["--", "Single", "Married", "Divorced", "Widowed"],
                                                    index=["--", "Single", "Married", "Divorced", "Widowed"].index(pi.get("Marital Status", "--")))
            st.markdown("</div>", unsafe_allow_html=True)

        # 🎓 Education
        with st.container():
            st.markdown('<div class="card-section"><h4>🎓 Education</h4>', unsafe_allow_html=True)
            for i, edu in enumerate(cv["data"].get("Education", [])):
                st.markdown(f"**Degree #{i+1}**")
                col1, col2 = st.columns(2)
                with col1:
                    edu["Degree"] = st.text_input("Degree", edu.get("Degree", ""), key=f"deg_{i}")
                    edu["Field"] = st.text_input("Field", edu.get("Field", ""), key=f"field_{i}")
                with col2:
                    edu["Institution"] = st.text_input("Institution", edu.get("Institution", ""), key=f"inst_{i}")
                    edu["Graduation Year"] = st.text_input("Graduation Year", edu.get("Graduation Year", ""), key=f"year_{i}")
            if st.form_submit_button("➕ Add New Degree"):
                cv["data"]["Education"].append({"Degree": "", "Field": "", "Institution": "", "Graduation Year": ""})
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        # 🌐 Languages
        with st.container():
            st.markdown('<div class="card-section"><h4>🌐 Languages</h4>', unsafe_allow_html=True)
            cv["data"]["Languages"] = st.multiselect("Languages", options=[
                "English", "Spanish", "Mandarin", "Hindi", "Arabic", "Bengali", "Portuguese", "Russian",
                "Japanese", "German", "French", "Italian", "Urdu", "Turkish", "Korean", "Vietnamese",
                "Persian", "Polish", "Dutch", "Thai"
            ], default=cv["data"].get("Languages", []))
            st.markdown("</div>", unsafe_allow_html=True)

        # 💼 Experience
        with st.container():
            st.markdown('<div class="card-section"><h4>💼 Professional Experience</h4>', unsafe_allow_html=True)
            for i, exp in enumerate(cv["data"].get("Professional Experience", [])):
                st.markdown(f"**Experience #{i+1}**")
                col1, col2 = st.columns(2)
                with col1:
                    exp["Company"] = st.text_input("Company", exp.get("Company", ""), key=f"comp_{i}")
                    exp["Total Years in Company"] = st.text_input("Years in Company", exp.get("Total Years in Company", ""), key=f"years_comp_{i}")
                    exp["Internal Rotation"] = st.text_input("Internal Rotation", exp.get("Internal Rotation", ""), key=f"rot_{i}")
                with col2:
                    exp["Position"] = st.text_input("Position", exp.get("Position", ""), key=f"pos_{i}")
                    exp["Years in Position"] = st.text_input("Years in Position", exp.get("Years in Position", ""), key=f"years_pos_{i}")
                exp["Achievements and Responsibilities"] = st.text_area(
                    "Achievements", exp.get("Achievements and Responsibilities", ""), key=f"achv_{i}", height=70
                )
            if st.form_submit_button("➕ Add New Experience"):
                cv["data"]["Professional Experience"].append({
                    "Company": "", "Position": "", "Total Years in Company": "", "Years in Position": "",
                    "Internal Rotation": "", "Achievements and Responsibilities": ""
                })
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        # 🏅 Other Achievements
        with st.container():
            st.markdown('<div class="card-section"><h4>🏅 Other Achievements</h4>', unsafe_allow_html=True)
            for i, ach in enumerate(cv["data"].get("Other Achievements", [])):
                st.markdown(f"**Achievement #{i+1}**")
                col1, col2 = st.columns(2)
                with col1:
                    ach["Title"] = st.text_input("Title", ach.get("Title", ""), key=f"title_{i}")
                    ach["Institution"] = st.text_input("Institution", ach.get("Institution", ""), key=f"ach_inst_{i}")
                with col2:
                    ach["Type"] = st.text_input("Type", ach.get("Type", ""), key=f"type_{i}")
                    ach["Year"] = st.text_input("Year", ach.get("Year", ""), key=f"ach_year_{i}")
            if st.form_submit_button("➕ Add New Achievement"):
                cv["data"]["Other Achievements"].append({"Title": "", "Type": "", "Institution": "", "Year": ""})
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        # 💰 Compensation
        with st.container():
            st.markdown('<div class="card-section"><h4>💰 Current Compensation</h4>', unsafe_allow_html=True)
            comp = cv["data"].get("Current Compensation", {})
            col1, col2 = st.columns(2)
            with col1:
                comp["Gross Salary"] = st.text_input("Gross Salary", comp.get("Gross Salary", ""))
            with col2:
                comp["Net Salary"] = st.text_input("Net Salary", comp.get("Net Salary", ""))
            comp["Compensation Type"] = st.selectbox("Compensation Type", ["--", "Gross", "Net", "Hybrid"],
                                                     index=["--", "Gross", "Net", "Hybrid"].index(comp.get("Compensation Type", "--")))
            st.markdown("</div>", unsafe_allow_html=True)

        # Botones finales
        submitted = st.form_submit_button("📂 Save Changes")
        completed = st.form_submit_button("✅ Mark as Complete")

        if submitted:
            st.success("Changes saved.")

        if completed:
            errors = get_completion_errors(cv["data"])
            if not errors:
                # Mover el CV a "Listos" en Kanban
                cv["status"] = "ready"
                st.session_state.cvs[uid] = cv  # Actualizar estado
                st.success("✅ CV marked as complete! You can now download it from the 'Listos' column.")
            else:
                st.error("❌ The following required fields are missing or invalid:")
                for err in errors:
                    st.markdown(f"- ❌ **{err}**")

# --------- Bulk Download ZIP ---------

st.divider()
st.markdown("### 📦 Download all CVs marked as Ready")

from exporter import zip_ready_cvs
if any(cv["status"] == "ready" for cv in st.session_state.cvs.values()):
    zip_path = zip_ready_cvs(st.session_state.cvs)
    with open(zip_path, "rb") as f:
        st.download_button(
            label="⬇️ Download All as ZIP",
            data=f,
            file_name="ready_cvs.zip",
            mime="application/zip"
        )
else:
    st.info("No CVs marked as 'ready' to download.")