"""
app.py — HireAssist AI Entry Point & Authentication Gate
=========================================================
  STEP 1 – Login Landing Page  (user not authenticated)
  STEP 2 – Role Onboarding     (first-time user, no DB record yet)
  STEP 3 – Home Dashboard      (fully authenticated, role on file)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
from sqlalchemy.exc import OperationalError
from database import init_db, open_session, JobPost, Candidate, User
from PIL import Image
# ── Page config ───────────────────────────────────────────────────────────────
import base64
try:
    # Use the new logo file located one directory up (in the project root)
    logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logo2_img_no_text_lighter.png")
    ob_logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logo2_img_no_text.png")
    page_icon = Image.open(logo_path)
    
    with open(logo_path, "rb") as _f:
        global_logo_b64 = base64.b64encode(_f.read()).decode()
    with open(ob_logo_path, "rb") as _f2:
        ob_logo_b64 = base64.b64encode(_f2.read()).decode()
        
    hero_logo = f'<img src="data:image/png;base64,{global_logo_b64}" style="height:50px;width:80px;object-fit:contain;vertical-align:text-bottom;margin-right:12px;border-radius:8px;">'
    login_logo = f'<img src="data:image/png;base64,{global_logo_b64}" style="height:44px;width:auto;object-fit:contain;vertical-align:text-bottom;margin-right:14px;">'
    ob_logo = f'<img src="data:image/png;base64,{ob_logo_b64}" style="height:44px;width:auto;object-fit:contain;vertical-align:text-bottom;margin-right:14px;">'
except Exception:
    page_icon = "⬡"
    hero_logo = "⬡ HireAssist AI"
    login_logo = "⬡ "
    ob_logo = "⬡ "

st.set_page_config(
    page_title="HireAssist AI",
    page_icon=page_icon,
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Session auth tracker ──────────────────────────────────────────────────────
if "auth_verified" not in st.session_state:
    st.session_state.auth_verified = False

# ── Helper: hide sidebar on login / onboarding screens ───────────────────────
def _hide_sidebar():
    st.markdown("""
        <style>
        [data-testid="stSidebar"]        { display: none !important; }
        [data-testid="collapsedControl"] { display: none !important; }
        [data-testid="stHeader"]         { display: none !important; }
        div.block-container              { padding-top: 0rem !important; }
        </style>
    """, unsafe_allow_html=True)



# ═══════════════════════════════════════════════════════════════════════════════
# GATE 2 — Not logged in → show the branded login landing page
# ═══════════════════════════════════════════════════════════════════════════════
if not st.user.is_logged_in:
    _hide_sidebar()

    # ── Login page CSS — mirrors the onboarding split-panel design ─────────────
    st.markdown("""
<style>
/* ── Remove Streamlit default padding for edge-to-edge layout ── */
div.block-container {
    padding-top: 0 !important;
    padding-bottom: 0 !important;
    padding-left: 0 !important;
    padding-right: 0 !important;
    max-width: 100% !important;
}

/* ── Remove gap between columns ── */
div[data-testid="stHorizontalBlock"] {
    gap: 0 !important;
}

/* ── LEFT COLUMN — gradient branding side ── */
div[data-testid="stColumn"]:nth-of-type(1) {
    background: linear-gradient(135deg, #1f0404 0%, #3d0808 55%, #690e0e 100%);
    color: #F5EAD0;
    padding: 8% 6% 8% 10% !important;
    position: relative;
    overflow: hidden;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    justify-content: center;
}
div[data-testid="stColumn"]:nth-of-type(1)::before {
    content: '';
    position: absolute;
    bottom: -60px; left: -40px;
    width: 320px; height: 80px;
    background: rgba(237,217,163,0.15);
    border-radius: 50px;
    transform: rotate(-25deg);
}
div[data-testid="stColumn"]:nth-of-type(1)::after {
    content: '';
    position: absolute;
    bottom: 40px; left: 60px;
    width: 200px; height: 55px;
    background: rgba(237,217,163,0.10);
    border-radius: 50px;
    transform: rotate(-25deg);
}
.login-pill-1 {
    position: absolute;
    bottom: 120px; right: -20px;
    width: 180px; height: 50px;
    background: rgba(200,169,110,0.18);
    border-radius: 50px;
    transform: rotate(-25deg);
}
.login-pill-2 {
    position: absolute;
    bottom: 180px; left: 20px;
    width: 100px; height: 30px;
    background: rgba(237,217,163,0.12);
    border-radius: 50px;
    transform: rotate(-25deg);
}
.login-brand-logo {
    font-size: 2.5rem;
    font-weight: 1000;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    opacity: 1;
    margin-bottom: 48px;
}
div[data-testid="stColumn"]:nth-of-type(1) h1 {
    font-size: 2.6rem;
    font-weight: 800;
    line-height: 1.15;
    margin: 0 0 20px 0;
    letter-spacing: -0.02em;
    color: #F5EAD0;
}
div[data-testid="stColumn"]:nth-of-type(1) p.login-tagline {
    font-size: 0.97rem;
    opacity: 0.80;
    line-height: 1.65;
    max-width: 380px;
    margin: 0;
    color: #F5EAD0;
}

/* ── RIGHT COLUMN — sign-in form side ── */
div[data-testid="stColumn"]:nth-of-type(2) {
    background: #F5EAD0;
    padding: 8% 10% 8% 8% !important;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    justify-content: center;
}
.login-right-header {
    text-align: center;
    margin-bottom: 32px;
}

.login-right-header h2 {
    font-size: 1.7rem;
    font-weight: 800;
    color: #2A1407;
    margin: 0 0 8px 0;
}
.login-right-header .login-sub {
    font-size: 1rem;
    color: #7a5c3a;
    line-height: 1.55;
}
.login-footer {
    font-size: 0.78rem;
    color: #a08060;
    text-align: center;
    margin-top: 20px;
    line-height: 1.55;
}
.feature-chips {
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    gap: 8px;
    margin-top: 22px;
}
.chip {
    background: #EDD9A3;
    border: 1px solid #C8A96E;
    border-radius: 20px;
    padding: 4px 12px;
    font-size: 0.78rem;
    color: #690e0e;
    font-weight: 600;
}
</style>
""", unsafe_allow_html=True)

    # ── Two-column split layout ────────────────────────────────────────────────
    left_col, right_col = st.columns([1.1, 0.9])

    with left_col:
        st.markdown(f"""
<div class="login-brand-logo">{login_logo}HireAssist AI</div>
<h3>The intelligent recruiter platform.</h3>
<p class="login-tagline">
    Secure &middot; Auditable &middot; Role-aware.<br><br>
    Parse resumes at scale, score candidates against your job descriptions,
    and collaborate with your team — all in one place.
</p>
<div class="login-pill-1"></div>
<div class="login-pill-2"></div>
""", unsafe_allow_html=True)

    with right_col:
        st.markdown("""
<div class="login-right-header">
    <h1>Welcome</h1>
    <div class="login-sub">
        Sign in with your Google account to access<br>your recruitment workspace.
    </div>
</div>
<div class="feature-chips">
    <span class="chip">&#9889; AI Resume Parsing</span>
    <span class="chip">&#129504; Smart Scoring</span>
    <span class="chip">&#128274; Google Auth</span>
    <span class="chip">&#128202; PostgreSQL</span>
</div>
""", unsafe_allow_html=True)

        st.write("")
        st.button(
            "Sign in with Google",
            on_click=st.login,
            use_container_width=True,
            key="google_login_btn",
            type="primary",
        )
        st.markdown("""
<div class="login-footer">
    By signing in you agree to our usage policy.<br>
    This platform is intended for authorized recruiters only.
</div>
""", unsafe_allow_html=True)

    st.stop()

# ═══════════════════════════════════════════════════════════════════════════════
# GATE 3 — Logged in, check if user exists in DB
# ═══════════════════════════════════════════════════════════════════════════════
user_email = st.user.email
user_name = st.user.name

sess = open_session()
db_user = sess.query(User).filter_by(email=user_email).first()
sess.close()

if not db_user:
    _hide_sidebar()


    ROLE_PRESETS = ["Recruiter", "Hiring Manager", "Admin", "Other (specify below)"]

    # ═══════════════════════════════════════════════════════════════════════════════
    # CSS for the role selection page if its a new account — split panel layout
    st.markdown("""
<style>
/* ── Remove Streamlit default padding so the panel can go edge-to-edge ── */
div.block-container {
    padding-top: 0 !important;
    padding-bottom: 0 !important;
    padding-left: 0 !important;
    padding-right: 0 !important;
    max-width: 100% !important;
}

/* ── Remove gap between columns so they sit flush ── */
div[data-testid="stHorizontalBlock"] {
    gap: 0 !important;
}

/* ── LEFT COLUMN — gradient branding side ── */
div[data-testid="stColumn"]:nth-of-type(1) {
    background: linear-gradient(135deg, #690e0e 0%, #3d0808 55%, #1f0404 100%);
    color: #F5EAD0;
    /* Professional Spacing: Top Right Bottom Left */
    padding: 8% 6% 8% 10% !important; 
    position: relative;
    overflow: hidden;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    justify-content: center;
}

/* Decorative pill shapes (CSS-only, no JS) */
div[data-testid="stColumn"]:nth-of-type(1)::before {
    content: '';
    position: absolute;
    bottom: -60px; left: -40px;
    width: 320px; height: 80px;
    background: rgba(237,217,163,0.15);
    border-radius: 50px;
    transform: rotate(-25deg);
}
div[data-testid="stColumn"]:nth-of-type(1)::after {
    content: '';
    position: absolute;
    bottom: 40px; left: 60px;
    width: 200px; height: 55px;
    background: rgba(237,217,163,0.10);
    border-radius: 50px;
    transform: rotate(-25deg);
}
.ob-pill-1 {
    position: absolute;
    bottom: 120px; right: -20px;
    width: 180px; height: 50px;
    background: rgba(200,169,110,0.18);
    border-radius: 50px;
    transform: rotate(-25deg);
}
.ob-pill-2 {
    position: absolute;
    bottom: 180px; left: 20px;
    width: 100px; height: 30px;
    background: rgba(237,217,163,0.12);
    border-radius: 50px;
    transform: rotate(-25deg);
}
.ob-brand-logo {
    font-size: 2.5rem;
    font-weight: 1000;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    opacity: 1;
    margin-bottom: 48px;
}

div[data-testid="stColumn"]:nth-of-type(1) h1 {
    font-size: 2.6rem;
    font-weight: 800;
    line-height: 1.15;
    margin: 0 0 20px 0;
    letter-spacing: -0.02em;
    color: #F5EAD0;
}
div[data-testid="stColumn"]:nth-of-type(1) p {
    font-size: 0.97rem;
    opacity: 0.80;
    line-height: 1.65;
    max-width: 380px;
    margin: 0;
    color: #F5EAD0;
}

/* ── RIGHT COLUMN — form side ── */
div[data-testid="stColumn"]:nth-of-type(2) {
    background: #F5EAD0;
    /* Professional Spacing: Top Right Bottom Left */
    padding: 8% 10% 8% 8% !important; 
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    justify-content: center;
}
.ob-right-header {
    text-align: center;
    margin-bottom: 32px;
}
.ob-right-header .ob-badge {
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: #690e0e;
    margin-bottom: 10px;
}
.ob-right-header h2 {
    font-size: 1.7rem;
    font-weight: 800;
    color: #2A1407;
    margin: 0 0 6px 0;
}
.ob-right-header .ob-sub {
    font-size: 0.85rem;
    color: #7a5c3a;
    line-height: 1.5;
}
.ob-user-chip {
    display: flex;
    align-items: center;
    gap: 10px;
    background: #EDD9A3;
    border: 1.5px solid #C8A96E;
    border-radius: 50px;
    padding: 8px 16px;
    margin-bottom: 24px;
    font-size: 0.88rem;
    color: #2A1407;
}
.ob-user-chip .avatar {
    width: 32px; height: 32px;
    border-radius: 50%;
    background: linear-gradient(135deg, #690e0e, #3d0808);
    color: #F5EAD0;
    display: flex; align-items: center; justify-content: center;
    font-weight: 800; font-size: 0.9rem;
    flex-shrink: 0;
}
</style>

""", unsafe_allow_html=True)

    # Get first initial for avatar
    avatar_letter = (user_name[0] if user_name else "?").upper()

    # Create the two columns for the split layout
    left_col, right_col = st.columns([1.5, 1])

    with left_col:
        st.markdown(f"""
        <div class="ob-brand-logo">{ob_logo}HireAssist AI</div>
        <h2>One last step before we begin</h2>
        <p>
            Tell us your role so we can correctly attribute your activity
            and comments in the application. 
            This is set once and stored against your account.
        </p>
        <!-- Decorative pill shapes -->
        <div class="ob-pill-1"></div>
        <div class="ob-pill-2"></div>
        """, unsafe_allow_html=True)

    with right_col:
        st.markdown(f"""
        <div class="ob-right-header">
            <div class="ob-badge">New Account Setup</div>
            <h2>Select Your Role</h2>
            
        </div>
        <div class="ob-user-chip">
            <div class="avatar">{avatar_letter}</div>
            <div>
                <strong>{user_name}</strong><br>
                <span style="font-size:0.78rem;color:#7a5c3a;">{user_email}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        selected_preset = st.selectbox(
            "Select your role",
            options=ROLE_PRESETS,
            index=0,
            key="onboard_role_select",
        )

        custom_role = ""
        if selected_preset == "Other (specify below)":
            custom_role = st.text_input(
                "Enter your role",
                placeholder="e.g., Talent Acquisition Partner",
                key="onboard_custom_role",
            )

        final_role = custom_role.strip() if selected_preset == "Other (specify below)" else selected_preset
        st.write("")

        if st.button("Confirm & Enter HireAssist AI", type="primary", use_container_width=True, key="onboard_confirm_btn"):
            if not final_role:
                st.error("Please enter a role before continuing.")
            else:
                sess = open_session()
                try:
                    new_user = User(email=user_email, name=user_name, role=final_role)
                    sess.add(new_user)
                    sess.commit()
                    sess.refresh(new_user)
                    st.session_state.auth_verified      = True
                    st.session_state.current_user_email = user_email
                    st.session_state.current_user_name  = user_name
                    st.session_state.current_user_role  = final_role
                except Exception as e:
                    sess.rollback()
                    st.error(f"Failed to save profile: {e}")
                finally:
                    sess.close()
                st.rerun()

    st.stop()



# ═══════════════════════════════════════════════════════════════════════════════
# ALL GATES PASSED — Fully authenticated returning user → Home Dashboard
# ═══════════════════════════════════════════════════════════════════════════════
st.session_state.auth_verified      = True
st.session_state.current_user_email = user_email
st.session_state.current_user_name  = db_user.name or user_name
st.session_state.current_user_role  = db_user.role

import utils
utils.inject_global_css()
utils.render_sidebar_profile()

# ── Developer-only Admin Panel button (sidebar, home page only) ───────────────
DEVELOPER_EMAIL = st.secrets.get("admin", {}).get("developer_email", "")

    

# ── DB Stats ──────────────────────────────────────────────────────────────────
db_available = True
db_error_msg = ""
try:
    init_db()
except OperationalError as e:
    db_available = False
    db_error_msg = str(e)

# ── Page-specific CSS ─────────────────────────────────────────────────────────
st.markdown("""
    <style>
    section[data-testid="stSidebar"] [data-testid="collapsedControl"] { display: none !important; }
    section[data-testid="stSidebar"] div[data-testid="stColumn"] {
        border: none !important; border-radius: 0 !important; padding: 0 2px !important;
    }
    .home-hero {
        background: linear-gradient(135deg, #690e0e 0%, #3d0808 55%, #1f0404 100%);
        border-radius: 18px; padding: 20px 45px 30px 45px; margin-bottom: 25px;
        color: #F5EAD0; box-shadow: 0 8px 40px rgba(105,14,14,0.22);
        position: relative; overflow: hidden;
    }
    .home-hero::before {
        content: ''; position: absolute; top: -40px; right: -40px;
        width: 280px; height: 280px; border-radius: 50%;
        background: rgba(255,255,255,0.04); pointer-events: none;
    }
    .home-hero h1      { font-size: 2.6rem; font-weight: 800; margin: 0 0 10px 0; letter-spacing: -0.02em; }
    .home-hero .subtitle { font-size: 1.05rem; opacity: 0.82; max-width: 600px; margin: 0 0 28px 0; line-height: 1.55; }
    .home-hero .badge  {
        display: inline-block; background: rgba(255,255,255,0.14);
        border: 1px solid rgba(255,255,255,0.22); border-radius: 20px;
        padding: 4px 14px; font-size: 0.82rem; letter-spacing: 0.04em;
        margin-right: 8px; margin-bottom: 6px;
    }
    .pipeline-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-bottom: 36px; }
    .pipeline-card {
        background: #EDD9A3; border: 1.5px solid #C8A96E;
        border-radius: 14px; padding: 26px 24px; transition: box-shadow 0.2s;
    }
    .pipeline-card:hover { box-shadow: 0 4px 18px rgba(105,14,14,0.12); }
    .pipeline-card .step-num   { font-size: 0.72rem; font-weight: 700; letter-spacing: 0.1em;
                                  text-transform: uppercase; color: #690e0e; margin-bottom: 8px; }
    .pipeline-card .step-title { font-size: 1.05rem; font-weight: 700; color: #2A1407; }
    .pipeline-card .step-desc  {
        font-size: 0.88rem; color: #7a5c3a; line-height: 1.5;
        max-height: 0; opacity: 0; overflow: hidden;
        transition: max-height 0.4s ease, opacity 0.3s ease, margin-top 0.4s ease;
    }
    .pipeline-card:hover .step-desc { max-height: 200px; opacity: 1; margin-top: 10px; }
    .db-status {
        background: #EDD9A3; border: 1.5px solid #C8A96E;
        border-radius: 10px; padding: 16px 22px;
        display: flex; align-items: center; gap: 14px; margin-bottom: 28px;
    }
    .db-status .dot       { width: 12px; height: 12px; border-radius: 50%; flex-shrink: 0; }
    .db-status .dot.green { background: #4caf50; box-shadow: 0 0 8px #4caf5066; }
    .db-status .dot.red   { background: #f44336; box-shadow: 0 0 8px #f4433666; }
    .db-status .label     { font-size: 0.92rem; font-weight: 600; color: #2A1407; }
    .db-status .sub       { font-size: 0.8rem; color: #7a5c3a; }
    .stat-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 32px; }
    .stat-card {
        background: #F5EAD0; border: 1.5px solid #C8A96E;
        border-radius: 12px; padding: 20px 22px; text-align: center;
    }
    .stat-card .sv { font-size: 2.2rem; font-weight: 800; color: #690e0e; }
    .stat-card .sl { font-size: 0.75rem; color: #7a5c3a; text-transform: uppercase; letter-spacing: 0.06em; margin-top: 2px; }
    div.block-container, [data-testid="stAppViewBlockContainer"] {
        padding-top: 3rem !important; max-width: 98% !important;
        padding-left: 1rem !important; padding-right: 1rem !important;
    }
    </style>
""", unsafe_allow_html=True)

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown(f"""
    <div class="home-hero">
        <h1>{hero_logo}HireAssist AI</h1>
        <p class="subtitle">
            Welcome, {st.session_state.get('current_user_name', '')}.
        </p>
        <span class="badge">Streamlit Multi-Page</span>
        <span class="badge">PostgreSQL + JSONB</span>
        <span class="badge">Pydantic Schemas</span>
        <span class="badge">Hugging Face Inference API</span>
    </div>
""", unsafe_allow_html=True)

# ── DB Status card ────────────────────────────────────────────────────────────
if db_available:
    session = open_session()
    try:
        n_jobs = session.query(JobPost).count()
        n_cand = session.query(Candidate).count()
        n_done = session.query(Candidate).filter_by(status="done").count()
    finally:
        session.close()

    st.markdown(f"""
        <div class="db-status">
            <div class="dot green"></div>
            <div>
                <div class="label">PostgreSQL Connected — <code>resume_parser_db</code></div>
                <div class="sub">{n_jobs} workspaces · {n_done}/{n_cand} resumes parsed</div>
            </div>
        </div>
        <div class="stat-row">
            <div class="stat-card"><div class="sv">{n_jobs}</div><div class="sl">Job Workspaces</div></div>
            <div class="stat-card"><div class="sv">{n_cand}</div><div class="sl">Resumes Uploaded</div></div>
            <div class="stat-card"><div class="sv">{n_done}</div><div class="sl">Successfully Parsed</div></div>
            <div class="stat-card"><div class="sv">{n_cand - n_done}</div><div class="sl">Pending / Errors</div></div>
        </div>
    """, unsafe_allow_html=True)
else:
    st.markdown(f"""
        <div class="db-status">
            <div class="dot red"></div>
            <div>
                <div class="label">Database Unavailable</div>
                <div class="sub">Set DATABASE_URL in src/.env — e.g. postgresql://postgres:postgres@localhost:5432/resume_parser_db</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

# ── Pipeline step cards ───────────────────────────────────────────────────────
st.markdown("""
    <div class="pipeline-grid">
        <div class="pipeline-card">
            <div class="step-num">Step 01</div>
            <div class="step-title">Create a Job Post</div>
            <div class="step-desc">
                Define the role, paste the full job description, and choose your baseline
                evaluation criteria. Each job post creates a persistent PostgreSQL workspace
                that organises all incoming candidates.
            </div>
        </div>
        <div class="pipeline-card">
            <div class="step-num">Step 02</div>
            <div class="step-title">Upload & Parse Resumes</div>
            <div class="step-desc">
                Drop in the PDF or DOCX resume files. The pipeline hands them to the AI
                extraction engine, which extracts structured candidate profiles directly
                into PostgreSQL as each file completes.
            </div>
        </div>
        <div class="pipeline-card">
            <div class="step-num">Step 03</div>
            <div class="step-title">Score & Shortlist</div>
            <div class="step-desc">
                Score every candidate against your Job Description and mandatory skills.
                Configure custom evaluation factors and thresholds in the sidebar. The
                dashboard sorts and flags recommended candidates based on defined thresholds.
            </div>
        </div>
    </div>
""", unsafe_allow_html=True)

# ── Navigation CTA ────────────────────────────────────────────────────────────
st.markdown("### Jump to a Page")
cta1, cta2, cta3 = st.columns(3)
with cta1:
    if st.button("Create Job Post", type="primary", use_container_width=True):
        st.switch_page("pages/1_Job_Post_Creator.py")
with cta2:
    if st.button("Data Hub & File Upload", type="primary", use_container_width=True):
        st.switch_page("pages/2_Data_Hub.py")
with cta3:
    if st.button("Evaluation Dashboard", type="primary", use_container_width=True):
        st.switch_page("pages/3_Evaluation_Dashboard.py")

# Render hidden logout button at the absolute bottom to prevent top spacing
import utils
utils.render_hidden_logout_button()
