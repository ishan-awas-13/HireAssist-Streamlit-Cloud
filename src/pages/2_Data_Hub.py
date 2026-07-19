"""
Page 2 — Data Hub & Asynchronous Upload
========================================
Recruiters select an active Job Post workspace, then drop in a batch of
PDF / DOCX files. Files are handed to a background worker queue and this
page polls the database for live progress updates.

STATUS: Architecture stub — background worker integration in progress.
The page currently supports synchronous parsing (same behaviour as the
original app.py) while the async queue layer is being wired in.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import time
import threading
import json
from datetime import datetime
from sqlalchemy.exc import OperationalError
import utils

# Require user login before loading the page
utils.require_login()

from database import init_db, open_session, JobPost, Candidate
from extractor import get_clean_resume_text
from parser_engine import parse_resume_text

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Data Hub — Enterprise Resume Parser",
    page_icon="📥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Inject global utility CSS ───────────────────────────────────────────────
utils.inject_global_css()

# ── DB init ───────────────────────────────────────────────────────────────────
db_available = True
try:
    init_db()
except OperationalError as e:
    db_available = False
    _db_error_msg = str(e)

# ── Model map ─────────────────────────────────────────────────────────────────
MODEL_DICT = {
    "Qwen 2.5 (7B Instruct)": "Qwen/Qwen2.5-7B-Instruct",
}

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown("""
    <style>
    div[data-testid="stMarkdownContainer"] p { font-size: 0.95rem; }
    div[data-testid="stAlert"] p,
    div[data-testid="stAlert"] div { font-size: 0.93rem !important; }
    section[data-testid="stSidebar"] div[data-testid="stColumn"] {
        border: none !important; border-radius: 0 !important; padding: 0 2px !important;
    }
    section[data-testid="stSidebar"] [data-testid="collapsedControl"] { display: none !important; }

    .page-hero {
        background: linear-gradient(135deg, #1f0404 0%, #3d0808 55%, #690e0e 100%);
        border-radius: 14px; 
        padding: 25px 40px; 
        margin-bottom: 30px;
        color: #D4EDD9; box-shadow: 0 4px 24px rgba(26,58,46,0.22);
    }
    .page-hero h1 { font-size: 2rem; font-weight: 700; margin: 0 0 6px 0; letter-spacing: -0.01em; }
    .page-hero p  { font-size: 0.97rem !important; opacity: 0.82; margin: 0; }

    .resume-header {
        background: linear-gradient(90deg, #1a1a2e 0%, #16213e 100%);
        border-left: 4px solid #4a90e2; padding: 12px 18px;
        border-radius: 6px; margin-bottom: 16px;
    }
    .resume-header h3 { margin: 0; color: #e0e0e0; font-size: 1.1rem; }
    .resume-meta { font-size: 0.8rem; color: #888; margin-top: 4px; }

    .stat-card {
        background: #EDD9A3; border: 1.5px solid #C8A96E;
        border-radius: 10px; padding: 18px 22px; text-align: center;
    }
    .stat-card .stat-val { font-size: 2rem; font-weight: 700; color: #690e0e; }
    .stat-card .stat-lbl { font-size: 0.8rem; color: #7a5c3a; text-transform: uppercase;
                           letter-spacing: 0.06em; margin-top: 2px; }
    
    /*Tp push the page up and also take more horizontal space*/
    div.block-container, [data-testid = "stAppViewBlockContainer"] { 
        padding-top: 3rem !important;
        max-width: 98% !important; 
        padding-left: 1rem !important;
        padding-right: 1rem !important;
     }

    </style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
if "dh_selected_job_id" not in st.session_state:
    st.session_state.dh_selected_job_id = st.session_state.get("active_job_post_id", None)
#    st.markdown("## 📥 Data Hub")
    #st.caption("Step 2 of 3 — Upload resumes into a workspace.")
    #st.divider()

  #  st.markdown("### 🔀 Quick Navigation")
   # st.page_link("pages/1_Job_Post_Creator.py",      label="← Page 1: Job Post Creator")
    #st.page_link("pages/3_Evaluation_Dashboard.py",  label="→ Page 3: Evaluation Dashboard")
    #st.divider()


# ── Model Configuration ─────────────────────────────────────────────────────────
# Model selection removed from sidebar to prevent bugs and hardcoded to the primary model
current_model = list(MODEL_DICT.values())[0]


# ── Page Hero ─────────────────────────────────────────────────────────────────
st.markdown("""
    <div class="page-hero">
        <h1>Data Hub & Batch Upload</h1>
        <p>Select an active job workspace, upload your resume batch, and watch the pipeline parse each file.
           Results are persisted to PostgreSQL database as they complete.</p>
    </div>
""", unsafe_allow_html=True)

if not db_available:
    st.error(f"**Database unavailable.** Check `DATABASE_URL`.\n\n```\n{_db_error_msg}\n```", icon="🔌")
    st.stop()

# ── Workspace selector ────────────────────────────────────────────────────────
session = open_session()
try:
    job_posts = session.query(JobPost).filter_by(is_active=True).order_by(JobPost.created_at.desc()).all()
    job_options = {f"#{jp.id} — {jp.title}": jp.id for jp in job_posts}
finally:
    session.close()

if not job_options:
    st.warning("⚠️ No active job workspaces found. **Create one on Page 1 first.**")
    st.page_link("pages/1_Job_Post_Creator.py", label="Go to Page 1 →", icon="📋")
    st.stop()

# Pre-select if we just came from Page 1
default_idx = 0
if st.session_state.dh_selected_job_id:
    for i, jid in enumerate(job_options.values()):
        if jid == st.session_state.dh_selected_job_id:
            default_idx = i
            break

selected_label = st.selectbox(
    "🗂️ Select Job Post Workspace",
    options=list(job_options.keys()),
    index=default_idx,
    key="dh_workspace_select"
)
active_job_id = job_options[selected_label]
st.session_state.dh_selected_job_id = active_job_id

# ── Workspace stats ───────────────────────────────────────────────────────────
session = open_session()
try:
    active_jp   = session.query(JobPost).filter_by(id=active_job_id).first()
    total_c     = active_jp.candidates.count() if active_jp else 0
    done_c      = active_jp.candidates.filter_by(status="done").count() if active_jp else 0
    error_c     = active_jp.candidates.filter_by(status="error").count() if active_jp else 0
    queued_c    = active_jp.candidates.filter_by(status="queued").count() if active_jp else 0
finally:
    session.close()

s1, s2, s3, s4 = st.columns(4)
for col, val, lbl in zip([s1, s2, s3, s4],
                          [total_c, done_c, error_c, queued_c],
                          ["Total Uploaded", "Parsed ✓", "Errors ✗", "Queued ⏳"]):
    with col:
        st.markdown(f"""
            <div class="stat-card">
                <div class="stat-val">{val}</div>
                <div class="stat-lbl">{lbl}</div>
            </div>
        """, unsafe_allow_html=True)

st.divider()

# ── File upload ───────────────────────────────────────────────────────────────
uploaded_files = st.file_uploader(
    "📂 Upload Resume Files (PDF / DOCX)",
    type=["pdf", "docx"],
    accept_multiple_files="directory",
    key="dh_uploader",
    help="Drop in up to 300+ files — they'll be queued and processed sequentially."
)

run_btn = st.button(
    "▶Parse & Ingest All Resumes",
    type="primary",
    disabled=not uploaded_files,
    key="dh_run_btn"
)

# ── Batch processing ──────────────────────────────────────────────────────────
if run_btn and uploaded_files:
    total = len(uploaded_files)
    st.info(f"Starting batch: **{total} file(s)** → workspace **{selected_label}**")
    overall_progress = st.progress(0, text="Initialising…")

    for idx, file in enumerate(uploaded_files):
        file_label = file.name
        st.markdown(
            f'<div class="resume-header">'
            f'<h3>📄 {file_label}</h3>'
            f'<div class="resume-meta">File {idx+1} of {total}</div>'
            f'</div>',
            unsafe_allow_html=True
        )
        timer_ph  = st.empty()
        status_ph = st.empty()

        # ── Insert queued record ──────────────────────────────────────────────
        session = open_session()
        try:
            candidate_row = Candidate(
                job_post_id = active_job_id,
                filename    = file_label,
                status      = "processing",
                created_at  = datetime.utcnow(),
            )
            session.add(candidate_row)
            session.commit()
            session.refresh(candidate_row)
            cand_id = candidate_row.id
        except Exception as e:
            session.rollback()
            st.error(f"DB insert failed for {file_label}: {e}")
            session.close()
            continue
        finally:
            session.close()

        # ── Parse ─────────────────────────────────────────────────────────────
        status_ph.info("Extracting text…")
        try:
            file.seek(0)
            extracted_text = get_clean_resume_text(file)
            status_ph.info(f"Sending to `{current_model}`…")

            result_box = {}
            error_box  = []
            done_event = threading.Event()

            def _worker(model=current_model, text=extracted_text):
                try:
                    result_box["data"] = parse_resume_text(model, text)
                except Exception as exc:
                    error_box.append(exc)
                finally:
                    done_event.set()

            t0 = time.time()
            threading.Thread(target=_worker, daemon=True).start()

            while not done_event.is_set():
                timer_ph.metric(f"⏱ {file_label}", f"{time.time()-t0:.1f} s")
                time.sleep(0.1)

            latency = time.time() - t0
            status_ph.empty()

            # ── Write result to DB ────────────────────────────────────────────
            session = open_session()
            try:
                row = session.query(Candidate).filter_by(id=cand_id).first()
                if error_box:
                    timer_ph.metric(f"⏱ {file_label}", f"{latency:.2f} s  ✗")
                    st.error(f"❌ Parse failed: {error_box[0]}")
                    row.status        = "error"
                    row.error_message = str(error_box[0])
                    row.latency_seconds = latency
                else:
                    parsed = result_box["data"]
                    timer_ph.metric(f"⏱ {file_label}", f"{latency:.2f} s  ✓")
                    st.success(f"✅ Parsed in {latency:.2f}s — saved to DB.")
                    row.status          = "done"
                    row.latency_seconds = latency
                    row.profile_json    = parsed.model_dump()
                session.commit()
            except Exception as e:
                session.rollback()
                st.warning(f"⚠️ DB update failed for {file_label}: {e}")
            finally:
                session.close()

        except Exception as exc:
            st.error(f"❌ Text extraction failed: {exc}")
            session = open_session()
            try:
                row = session.query(Candidate).filter_by(id=cand_id).first()
                row.status        = "error"
                row.error_message = str(exc)
                session.commit()
            except Exception:
                session.rollback()
            finally:
                session.close()

        overall_progress.progress(
            (idx + 1) / total,
            text=f"Processed {idx+1}/{total} — {file_label}"
        )

    overall_progress.progress(1.0, text="✅ All resumes ingested!")
    st.balloons()
    st.info("Head to **Page 3** to score and review candidates.")
    st.page_link("pages/3_Evaluation_Dashboard.py", label="Open Evaluation Dashboard →", icon="📊")

# ── Recent candidates for active workspace ────────────────────────────────────
st.divider()
st.markdown("### Candidates in This Workspace")
session = open_session()
try:
    recent_candidates = (
        session.query(Candidate)
        .filter_by(job_post_id=active_job_id)
        .order_by(Candidate.created_at.desc())
        .limit(50)
        .all()
    )
    if not recent_candidates:
        st.caption("No resumes uploaded yet for this workspace.")
    else:
        import pandas as pd
        rows = [{
            "ID":       c.id,
            "Filename": c.filename,
            "Status":   c.status,
            "Latency":  f"{c.latency_seconds:.2f}s" if c.latency_seconds else "—",  
            "Score":    f"{c.overall_score:.0f}%" if c.overall_score else "—",
            "Uploaded": c.created_at.strftime("%b %d, %H:%M"),
        } for c in recent_candidates]
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
finally:
    session.close()

# Render hidden logout button at the absolute bottom to prevent top spacing
import utils
utils.render_hidden_logout_button()
