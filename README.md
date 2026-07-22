# ⬡ HireAssist AI

![HireAssist Banner](https://img.shields.io/badge/Status-Live-success?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.11+-blue?style=for-the-badge&logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.37+-red?style=for-the-badge&logo=streamlit)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Supabase-336791?style=for-the-badge&logo=postgresql)
![OAuth](https://img.shields.io/badge/Google_OAuth-Secure-green?style=for-the-badge&logo=google)

**HireAssist AI** is an intelligent, scalable recruitment platform built to automate the most tedious parts of hiring. It allows recruiters to create job workspaces, bulk-parse resumes (PDF/DOCX) using Large Language Models, and intelligently score candidates against specific job descriptions.

This repository houses the **Streamlit Community Cloud** deployment version of the platform.

---

## ✨ Core Features

- **Automated Resume Parsing:** Upload candidate PDFs or DOCX files and let the LLM extract structured data (Experience, Education, Skills) into a strict `Pydantic` schema.
- **Intelligent Scoring Pipeline:** Automatically score candidates against mandatory skills and job descriptions using a customized LLM evaluation engine.
- **Relational Workspace Management:** Powered by PostgreSQL & SQLAlchemy, keeping candidates strictly organized under their respective Job Posts.
- **Secure Access Control:** Native Streamlit Google OAuth integration (`st.login`), complete with a dedicated user onboarding flow and role-based tracking.
- **Recruiter Collaboration:** Leave timestamped remarks and notes on candidates that are visible to your team.

---

## 🎨 Pushing Streamlit to its Limits (Advanced UI/UX)

Streamlit is notoriously rigid when it comes to custom frontend design. To create a premium, production-grade application, HireAssist AI employs several advanced workarounds to break out of Streamlit's default constraints:

### 1. Edge-to-Edge Layouts & CSS Injection

Streamlit naturally forces padding and margins that prevent true full-screen designs. We utilize aggressive `st.markdown(unsafe_allow_html=True)` CSS injection to override the underlying React DOM.

- **The Login & Onboarding Screens** utilize zero-padding block containers, allowing for modern, split-screen gradient layouts that feel like a native web app, completely hiding the standard Streamlit UI.

### 2. The "Gate" Authentication System

Streamlit's multi-page architecture typically exposes all pages in the sidebar immediately. HireAssist uses a strict, programmatic **Gate System** inside the entry point (`app.py`):

- **Gate 1:** `st.login` OAuth verification. If unauthenticated, the sidebar, header, and top padding are destroyed via CSS, forcing the user into the custom login landing page.
- **Gate 2:** Database verification. If a user logs in but has no database record, they are locked into an Onboarding Screen to select their role.
- **Gate 3:** Only once the session state and database confirm authorization is the standard multi-page sidebar restored.

### 3. Raw HTML/CSS Component Wrappers

Rather than relying on basic `st.info` or `st.metric` boxes, the Evaluation Dashboard and Home pages render custom HTML strings wrapped in Streamlit markdown. This allows for:

- Glassmorphism effects and hover-state animations.
- Custom status pills, flexbox grids, and timeline-style recruiter remark feeds.
- Dynamic Base64 image injection for branding across all pages without relying on external image hosting.

### 4. Bulletproof State Synchronization

Because Streamlit completely reruns the script upon every user interaction, managing complex state (like parsing multiple resumes in a batch while navigating away) is incredibly difficult. We heavily leverage `st.session_state` combined with immediate SQLAlchemy commits to ensure that no parsing progress, uploaded file, or evaluation score is ever lost during a page rerun.

---

## 🛠️ Technology Stack

* **Frontend:** [Streamlit](https://streamlit.io/) (with heavy custom CSS/HTML)
* **Backend:** Python 3.11+
* **Database:** PostgreSQL (Hosted on [Supabase](https://supabase.com/)), managed via SQLAlchemy (ORM)
* **Authentication:** Google OpenID Connect (OIDC) via `Authlib`
* **Data Extraction:** Hugging Face Inference API / OpenAI via `Pydantic` structured outputs.
* **Document Processing:** `pypdf`, `python-docx`

---

## 🚀 Environment Setup (Self-Hosting)

To run this application locally or deploy it to Streamlit Cloud, you must configure a `.streamlit/secrets.toml` file in the root directory:

```toml
# Database Connection
DATABASE_URL = "postgresql://user:password@host:port/dbname"

# LLM API Keys
HF_TOKEN = "your_huggingface_token"
OPENAI_API_KEY = "your_openai_key" # If using OpenAI extractor

# Google OAuth Credentials
[auth]
redirect_uri = "https://your-app-url.streamlit.app/oauth2callback"
cookie_secret = "generate_a_random_32_character_string"
client_id = "your_google_client_id"
client_secret = "your_google_client_secret"
server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"
client_kwargs = {"prompt" = "select_account"}

# Admin Configuration
[admin]
developer_email = "your_admin_email@gmail.com"
```

Once secrets are configured, simply install the requirements and run the app:

```bash
pip install -r requirements.txt
streamlit run src/app.py
```
