"""
Page 3 — Filters, Scoring & Evaluation Dashboard
==================================================
The interactive candidate filtering and inspection interface.
Reads candidates from PostgreSQL for the active workspace, applies
recruiter-defined scoring factors, and renders the evaluation dashboard.

This page is the migration target of the original monolithic app.py.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import time
import json
import copy
from datetime import datetime
from sqlalchemy.exc import OperationalError
import utils

# Require login for all users of the page
utils.require_login()

from database import init_db, open_session, JobPost, Candidate, User, CandidateComment
from scorer import score_candidate_suitability, extract_mandatory_skills

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Evaluation Dashboard — Enterprise Resume Parser",
    page_icon="📊",
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


# ── Global CSS (kept consistent with original app.py) ─────────────────────────
st.markdown("""
    <style>
    div[data-testid="stMarkdownContainer"] p { font-size: 0.95rem; }
    div[data-testid="stAlert"] p,
    div[data-testid="stAlert"] div { font-size: 0.93rem !important; }
    div[data-testid="stExpander"] div[data-testid="stMarkdownContainer"] p { font-size: 0.93rem; }
    div[data-testid="stColumn"] {
        border: 2px solid #444 !important;
        border-radius: 10px !important;
        padding: 8px 15px !important;
        box-sizing: border-box !important;
    }
    div[data-testid="stColumn"] div[data-testid="stColumn"] {
        border: none !important; border-radius: 0 !important; padding: 0 !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stColumn"] {
        border: none !important; border-radius: 0 !important; padding: 0 2px !important;
    }
    .field-card  { margin-bottom: 12px; line-height: 1.5; }
    .field-label { font-size: 0.75rem; color: #888; font-weight: 600;
                   text-transform: uppercase; letter-spacing: 0.04em; }
    .field-value { font-size: 0.95rem; color: inherit; word-break: break-word; }
    .resume-header {
        background: linear-gradient(90deg, #1a1a2e 0%, #16213e 100%);
        border-left: 4px solid #4a90e2; padding: 12px 18px;
        border-radius: 6px; margin-bottom: 16px;
    }
    .resume-header h3 { margin: 0; color: #e0e0e0; font-size: 1.1rem; }
    .resume-meta { font-size: 0.8rem; color: #ffff; margin-top: 4px; font-weight: 700}
    section[data-testid="stSidebar"] [data-testid="collapsedControl"] { display: none !important; }

    /* Push page content up and widen content container all the way to the screen edges */
    div.block-container, [data-testid="stAppViewBlockContainer"] { 
        padding-top: 1.2rem !important; 
        max-width: 98% !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    
    }


    /* Locked, independently-scrollable right-hand candidate rail */
    #rank-sidebar-anchor + div[data-testid="stHorizontalBlock"] {
        min-height: calc(100vh - 12rem);
        align-items: stretch !important;
    }

    /* Main column (left) — fill height + scroll independently */
    #rank-sidebar-anchor + div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]:first-child {
        max-height: calc(100vh - 14rem);
        overflow-y: auto;
    }

    /* Locked, independently-scrollable right-hand candidate rail */
    #rank-sidebar-anchor + div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]:last-child {
        position: sticky;
        top: 1rem;
        align-self: flex-start;
        max-height: calc(100vh - 14rem);
        overflow-y: auto;
        padding-right: 4px !important;
    }

    /* Compact font for candidate rail buttons */
    #rank-sidebar-anchor + div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]:last-child button {
        font-size: 0.72rem !important;
        padding: 4px 8px !important;
        line-height: 1.3 !important;
        min-height: unset !important;
    }

    </style>


""", unsafe_allow_html=True)

# Model selection removed — single model hardcoded
current_model = list(MODEL_DICT.values())[0]

# ── Session state defaults ─────────────────────────────────────────────────────
DEFAULT_FACTORS = [
    {"name": "Skills Match",     "threshold": 60},
    {"name": "Role Relevance",   "threshold": 60},
    {"name": "Experience Match", "threshold": 50},
    {"name": "Education Match",  "threshold": 50},
]

if "ed_factors"              not in st.session_state: 
    st.session_state.ed_factors = None #signals that it needs to be found from the database
if "ed_extracted_skills"     not in st.session_state: 
    st.session_state.ed_extracted_skills = []
if "ed_skills_confirmed"     not in st.session_state: 
    st.session_state.ed_skills_confirmed = False
if "ed_skills_editing"       not in st.session_state: 
    st.session_state.ed_skills_editing = False
if "ed_selected_job_id"      not in st.session_state:
    st.session_state.ed_selected_job_id = None #diff from any real ID
if "ed_scored_cache"         not in st.session_state: 
    st.session_state.ed_scored_cache = {}
if "ed_selected_candidate_id" not in st.session_state:
    st.session_state.ed_selected_candidate_id = None
if "ed_remarks_cache"          not in st.session_state:
    st.session_state.ed_remarks_cache = {}



# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════

#    st.markdown("# ⚙️ Evaluation Filter")
    #st.caption("Configure scoring criteria for the selected workspace.")
    #st.divider()

    #st.markdown("### 🔀 Quick Navigation")
    #st.page_link("pages/1_Job_Post_Creator.py", label="← Page 1: Job Post Creator")
    #st.page_link("pages/2_Data_Hub.py",         label="← Page 2: Data Hub")
    #st.divider()

with st.sidebar:
    is_recruiter_or_admin = utils.has_role(["Recruiter"])

    st.markdown("### Scoring Criteria (Factors)")
    if is_recruiter_or_admin:
        st.caption("Add / Adjust / Remove factors.")

        factor_to_remove = None
        for i, factor in enumerate(st.session_state.ed_factors or []):
            col_name, col_btn = st.columns([4, 2])
            with col_name:
                factor["threshold"] = st.slider(
                    label=f"{factor['name']}",
                    min_value=0, max_value=100,
                    value=factor["threshold"], step=5,
                    key=f"ed_threshold_{factor['name']}",
                    help=f"Minimum {factor['name']} score required to pass."
                )
                st.caption(f"Min: {factor['threshold']}%")
            with col_btn:
                if st.button("❌", key=f"ed_remove_factor_{i}",
                             help=f"Remove '{factor['name']}'", type="primary",
                             use_container_width=True):
                    factor_to_remove = i

        if factor_to_remove is not None:
            st.session_state.ed_factors.pop(factor_to_remove)
            st.rerun()

        st.divider()
        st.markdown("### ➕ Add Factor")
        new_factor_name = st.text_input("Factor name", placeholder="e.g. Communication Skills", key="ed_new_factor_name_input")
        new_factor_threshold = st.slider("Default threshold", 0, 100, 60, 5, key="ed_new_factor_threshold_input")
        if st.button("Add Factor", use_container_width=True, key="ed_add_factor_btn", type="primary"):
            name = new_factor_name.strip()
            existing = [f["name"].lower() for f in st.session_state.ed_factors]
            if not name:
                st.warning("Enter a factor name first.")
            elif name.lower() in existing:
                st.warning(f"'{name}' already exists.")
            else:
                st.session_state.ed_factors.append({"name": name, "threshold": new_factor_threshold})
                st.rerun()

        st.divider()
        if st.button("Save Workspace Criteria", use_container_width=True, type="primary"):
            if st.session_state.ed_selected_job_id:
                try:
                    session = open_session()
                    rows_updated = session.query(JobPost).filter_by(id=st.session_state.ed_selected_job_id).update({
                        "eval_factors": copy.deepcopy(st.session_state.ed_factors)
                    })
                    session.commit()
                    
                    if rows_updated > 0:
                        st.toast("✅ Workspace factors saved successfully!")
                    else:
                        st.toast("⚠️ Workspace found, but no changes detected.")
                except Exception as e:
                    st.error(f"Failed to save: {e}")
                finally:
                    if 'session' in locals():
                        session.close()
            else:
                st.warning("No workspace selected to save.")
    else:
        st.caption("🔒 *Read-Only View* — Factor thresholds managed by Recruiting Team.")
        for factor in (st.session_state.ed_factors or []):
            st.markdown(f"**{factor['name']}**: ≥`{factor['threshold']}%` passing score")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE HEADER
# ══════════════════════════════════════════════════════════════════════════════
st.title("Evaluation Dashboard")
st.write("Score, filter and inspect candidates from a parsed workspace.")

if not db_available:
    st.error(f"**Database unavailable.** Check `DATABASE_URL`.\n\n```\n{_db_error_msg}\n```", icon="🔌")
    st.stop()

# ── Workspace selector ────────────────────────────────────────────────────────
session = open_session()
try:
    job_posts   = session.query(JobPost).order_by(JobPost.created_at.desc()).all()
    job_options = {f"#{jp.id} — {jp.title}": jp.id for jp in job_posts}
finally:
    session.close()

if not job_options:
    st.warning("No job workspaces found. Create one on Page 1 first.")
    st.page_link("pages/1_Job_Post_Creator.py", label="Go to Page 1 →", icon="📋")
    st.stop()

default_idx = 0
if st.session_state.ed_selected_job_id:
    for i, jid in enumerate(job_options.values()):
        if jid == st.session_state.ed_selected_job_id:
            default_idx = i
            break

selected_label = st.selectbox(
    "🗂️ Select Job Post Workspace",
    options=list(job_options.keys()),
    index=default_idx,
    key="ed_workspace_select"
)
active_job_id = job_options[selected_label]
workspace_changed = (st.session_state.ed_selected_job_id != active_job_id)
st.session_state.ed_selected_job_id = active_job_id

# Load the active job post for its pre-configured fields
session = open_session()
try:
    active_jp = session.query(JobPost).filter_by(id=active_job_id).first()
    saved_jd        = active_jp.description or ""
    saved_skills    = active_jp.mandatory_skills or []
    saved_factors   = active_jp.eval_factors or DEFAULT_FACTORS
finally:
    session.close()

# If the workspace just changed, push the DB factors into session_state
# and rerun so the sidebar re-renders with the correct workspace factors
if workspace_changed:
    """st.session_state.ed_factors = saved_factors
    # to ensure the JD updates, clear and take from saved.
    if "ed_job_description" in st.session_state:
        del st.session_state["ed_job_description"]"""
    #-----------------------
    #new code to try and make the sidebar eval factors update everywrokspace change
    for f in (st.session_state.ed_factors or []):
        old_key = f"ed_threshold_{f['name']}"
        if old_key in st.session_state:
            del st.session_state[old_key]
    #----------------------------------------------------------------------------------------Code to make the slider obey the DB Value        
    # Forcefully inject the actual database values into session_state 
    # so the UI sliders are forced to snap to these exact numbers on rerun.
    for f in saved_factors:
        st.session_state[f"ed_threshold_{f['name']}"] = f["threshold"]
    
    st.session_state.ed_factors = copy.deepcopy(saved_factors)
    st.session_state.ed_extracted_skills = copy.deepcopy(saved_skills)
    st.session_state.ed_skills_confirmed = True
    st.session_state.ed_skills_editing = False
    st.rerun()

# ── Controls ──────────────────────────────────────────────────────────────────
ctrl_col1, ctrl_col2 = st.columns([2, 1])

with ctrl_col1:
    st.subheader("Job Description")
    job_description = st.text_area(
        "Job description (pre-loaded from workspace):",
        value=saved_jd,
        #key="ed_job_description",
        height=155,
        placeholder="Paste the job description here…"
    )

with ctrl_col2:
    st.subheader("Mandatory Skills")

    if is_recruiter_or_admin:
        if st.button(
            "Detect Mandatory Skills",
            disabled=not job_description.strip(),
            key="ed_extract_skills_btn",
            help="Analyzes your job description and extracts required skills automatically.",
            type="primary"
        ):
            with st.spinner("Analysing job description…"):
                try:
                    skills = extract_mandatory_skills(current_model, job_description)
                    st.session_state.ed_extracted_skills = skills
                    st.session_state.ed_skills_confirmed = False
                    st.session_state.ed_skills_editing   = True
                except Exception as e:
                    st.error(f"Skill extraction failed: {e}")

    # Seed from saved workspace skills if none detected yet
    if not st.session_state.ed_extracted_skills and saved_skills:
        st.session_state.ed_extracted_skills = saved_skills

    if st.session_state.ed_extracted_skills:
        if is_recruiter_or_admin and st.session_state.ed_skills_editing:
            edited = st.text_area(
                "Edit detected skills (one per line):",
                value="\n".join(st.session_state.ed_extracted_skills),
                height=130,
                key="ed_skills_edit_area"
            )
            if st.button("✅ Save Mandatory Skills", key="ed_save_skills_btn", type="primary", use_container_width=True):
                new_skills = [s.strip() for s in edited.split("\n") if s.strip()]
                st.session_state.ed_extracted_skills = new_skills
                st.session_state.ed_skills_confirmed = True
                st.session_state.ed_skills_editing   = False
                
                # Save to database
                if st.session_state.ed_selected_job_id:
                    try:
                        session = open_session()
                        session.query(JobPost).filter_by(id=st.session_state.ed_selected_job_id).update({
                            "mandatory_skills": new_skills
                        })
                        session.commit()
                        st.toast("✅ Mandatory skills saved to database!")
                    except Exception as e:
                        st.error(f"Database error: {e}")
                    finally:
                        if 'session' in locals():
                            session.close()
                st.rerun()
        else:
            skills_md = "   ".join(f"`{s}`" for s in st.session_state.ed_extracted_skills)
            st.markdown(f"**Saved requirements:** {skills_md}")
            if is_recruiter_or_admin:
                if st.button("✏️ Edit Skills", key="ed_edit_skills_btn", use_container_width=True):
                    st.session_state.ed_skills_editing = True
                    st.rerun()
    else:
        if is_recruiter_or_admin:
            st.caption("Paste a job description above and click **Detect Mandatory Skills** to auto-extract.")
        else:
            st.caption("🔒 Mandatory skills setup is restricted to Recruiters and Admins.")


# ══════════════════════════════════════════════════════════════════════════════
# HELPER — render one CandidateProfile (from JSON dict)
# ══════════════════════════════════════════════════════════════════════════════
def _render_profile_from_dict(profile_dict: dict):
    from schema import CandidateProfile
    try:
        profile = CandidateProfile(**profile_dict.get("candidate_profile", profile_dict))
    except Exception as e:
        st.warning(f"Could not deserialise profile: {e}")
        st.json(profile_dict)
        return

    def field(label, value):
        st.markdown(f"""
            <div class="field-card">
                <div class="field-label">{label}</div>
                <div class="field-value">{value or 'N/A'}</div>
            </div>
        """, unsafe_allow_html=True)

    def link_field(label, url):
        if url and str(url).strip() and str(url).lower() not in ["n/a", "none", "null"]:
            href = url if str(url).startswith("http") else f"https://{url}"
            html_link = f'<a href="{href}" target="_blank" style="color:#4a90e2; text-decoration:none; font-weight:600;">View Profile ↗</a>'
            field(label, html_link)
        else:
            field(label, "N/A")

    left, right = st.columns([1, 1])
    with left:
        st.markdown("#### Personal Information")
        p = profile.personal_information
        field("First Name",  p.first_name)
        field("Last Name",   p.last_name)
        field("✉️ Email",    p.email)
        field("📞 Phone",    p.phone_number)
        field("🏠 Location", p.location)
        link_field("👔 LinkedIn", p.linkedin_url)
        link_field("🤖 GitHub",   p.github_url)
        link_field("🌐 Portfolio",p.portfolio_url)

        st.divider()
        st.markdown("#### Technical Competencies")
        skills = profile.skills
        st.write(f"**Languages:** {', '.join(skills.programming_languages or ['N/A'])}")
        st.write(f"**Frameworks & Tools:** {', '.join(skills.frameworks_and_tools or ['N/A'])}")
        st.write(f"**Soft Skills:** {', '.join(skills.soft_skills or ['N/A'])}")

        if profile.certifications:
            st.divider()
            st.markdown("#### Certifications")
            for cert in profile.certifications:
                st.info(f"**{cert.name}** | {cert.issuing_organization} ({cert.issue_date})")

    with right:
        st.markdown("####  Professional Summary")
        st.write(profile.professional_summary or "N/A")

        if profile.work_experience:
            st.divider()
            st.markdown("#### Work Experience")
            for job in profile.work_experience:
                with st.expander(f"{job.job_title} at {job.company_name} ({job.start_date} – {job.end_date or 'Present'})"):
                    for resp in job.responsibilities:
                        st.write(f" - {resp}")

        if profile.education:
            st.divider()
            st.markdown("#### Academic Background")
            for edu in profile.education:
                st.info(f"**{edu.degree} in {edu.major}** | {edu.institution_name} ({edu.start_date} – {edu.end_date}) | GPA: {edu.gpa}")

        if profile.projects:
            st.divider()
            st.markdown("####  Projects")
            for project in profile.projects:
                with st.expander(project.project_name or "Unnamed Project"):
                    st.write(project.description)
                    if project.technologies_used:
                        st.write(f"**Technologies:** {', '.join(project.technologies_used)}")


# ══════════════════════════════════════════════════════════════════════════════
# LOAD CANDIDATES FROM DB
# ══════════════════════════════════════════════════════════════════════════════
st.divider()

session = open_session()
try:
    db_candidates = (
        session.query(Candidate)
        .filter_by(job_post_id=active_job_id, status="done")
        .order_by(Candidate.created_at.desc())
        .all()
    )
    # Detach from session by converting to plain dicts
    candidates_data = [{
        "id":           c.id,
        "filename":     c.filename,
        "profile_json": c.profile_json,
        "scores_json":  c.scores_json,
        "overall_score":c.overall_score,
        "is_shortlisted": c.is_shortlisted,
        "latency":      c.latency_seconds,
        "error":        c.error_message,
        "remarks":      c.remarks,
    } for c in db_candidates]
finally:
    session.close()

# Merge any cached in-session scores
for cd in candidates_data:
    cached = st.session_state.ed_scored_cache.get(cd["id"])
    if cached:
        cd["scores_json"]   = cached
        cd["overall_score"] = cached.get("overall_score", None)
    if cd["id"] in st.session_state.ed_remarks_cache:
        cd["remarks"] = st.session_state.ed_remarks_cache[cd["id"]]


# ══════════════════════════════════════════════════════════════════════════════
# TABS
# ══════════════════════════════════════════════════════════════════════════════
tab_results, tab_json, tab_scored = st.tabs([
    "Parsed Resumes",
    "Parsed Resume JSON",
    "Scores and Evaluations"
])

# ── TAB 1 — PARSED RESUMES ───────────────────────────────────────────────────
with tab_results:
    if not candidates_data:
        st.markdown("""
            <div style="text-align:center; padding:60px 20px; color:#666;
                        border:2px dashed #444; border-radius:12px; margin-top:20px;">
                <h3 style="color:#555; margin-bottom:10px;">No Parsed Resumes Yet</h3>
                <p style="font-size:0.95rem;">
                    Upload and parse resumes via <strong>Page 2 — Data Hub</strong>.
                </p>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.subheader(f"Results — {len(candidates_data)} candidates loaded from workspace")
        for idx, cd in enumerate(candidates_data, start=1):
            # Extract candidate personal info (same pattern as Tab 3)
            profile_json_data = cd.get("profile_json") or {}
            personal = profile_json_data.get("candidate_profile", profile_json_data).get("personal_information", {})
            first_name = personal.get("first_name", "—")
            last_name  = personal.get("last_name", "—")
            cand_email = personal.get("email", "—")
            cand_phone = personal.get("phone_number", "—")

            # Build the enriched header
            st.markdown(
                f'<div class="resume-header">'
                f'<h3>#{idx} &nbsp; {first_name} {last_name}</h3>'
                f'<div class="resume-meta">'
                f'{cand_email} &nbsp;|&nbsp; {cand_phone} &nbsp;|&nbsp; '
                f'{cd["filename"]} &nbsp;|&nbsp; '
                f'Latency: {cd["latency"]:.2f}s &nbsp;|&nbsp; '
                f'<span style="color:#4caf50;">✓ Parsed</span>'
                f'</div></div>',
                unsafe_allow_html=True
            )
            if cd["profile_json"]:
                _render_profile_from_dict(cd["profile_json"])
            st.divider()

# ── TAB 2 — RAW JSON ─────────────────────────────────────────────────────────
with tab_json:
    st.subheader(" Raw JSON Outputs")
    st.caption("JSON data extracted by the model for each candidate of this workspace.")
    #st.divider()

    #a button to make combined JSON that we can download to get all candidate JSON
    if st.button("Generate Master JSON"):
        master_json_dict = {}
        for cd in candidates_data:
            master_json_dict[cd["filename"]] = cd["profile_json"]
        
        #now store it in session_state(RAM) temp memory, not needed always
        st.session_state.ready_to_download_json = json.dumps(master_json_dict, indent = 2)


    #Now if the data is there in memory, reveal the download button to download all of it
    if "ready_to_download_json" in st.session_state:
        st.download_button(
            "Download Combined JSON",
            data=st.session_state.ready_to_download_json,
            file_name=f"workspace_resumes.json",
            mime="application/json",
            type="primary"
        )
        


        
    if not candidates_data:
        st.info("No data yet. Parse resumes via Page 2 first.")
    else:
        for cd in candidates_data:
            with st.expander(f"✅ {cd['filename']}  ({cd['latency']:.2f}s)", expanded=False):
                st.code(json.dumps(cd["profile_json"], indent=2), language="json")

# ── TAB 3 — SCORING & EVALUATION ─────────────────────────────────────────────



## New tab_scored code below:

with tab_scored:
    if not candidates_data:
        st.markdown("""
            <div style="text-align:center; padding:60px 20px; color:#666;
                        border:2px dashed #444; border-radius:12px; margin-top:20px;">
                <h3 style="color:#555; margin-bottom:10px;">No Resumes Parsed Yet</h3>
                <p style="font-size:0.95rem;">
                    Upload and parse resumes in Page 2 before scoring.
                </p>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.subheader("Score & Evaluate Candidates")
        st.caption("Calculate fit scores based on the Job Description and Key Skills above.")

        if is_recruiter_or_admin:
            can_score = True
            if st.button("Score All Candidates", type="primary", key="ed_score_btn"):
                skills_list = st.session_state.ed_extracted_skills
                progress_bar = st.progress(0.0)
                status_text  = st.empty()
                total_valid  = len(candidates_data)

                for idx, cd in enumerate(candidates_data):
                    status_text.info(f"Evaluating {cd['filename']} ({idx+1}/{total_valid})…")
                    try:
                        scores = score_candidate_suitability(
                            model_name      = current_model,
                            job_description = job_description,
                            key_skills      = skills_list,
                            resume_json     = cd["profile_json"],
                            eval_factors    = st.session_state.ed_factors
                        )
                        cd["scores_json"]   = scores
                        cd["overall_score"] = scores.get("overall_score", None)
                        st.session_state.ed_scored_cache[cd["id"]] = scores

                        session = open_session()
                        try:
                            row = session.query(Candidate).filter_by(id=cd["id"]).first()
                            row.scores_json   = scores
                            row.overall_score = scores.get("overall_score", None)
                            row.scored_at     = datetime.utcnow()
                            session.commit()
                        except Exception:
                            session.rollback()
                        finally:
                            session.close()

                    except Exception as e:
                        st.error(f"Failed to score {cd['filename']}: {e}")
                    progress_bar.progress((idx + 1) / total_valid)

                status_text.success("Scoring completed!")
                time.sleep(1)
                status_text.empty()
                progress_bar.empty()
        else:
            st.button("Score All Candidates", disabled=True, key="ed_score_btn_disabled", help="AI Candidate Scoring is restricted to Recruiters & Admins.")
            st.caption("🔒 *View-Only Mode* — Candidate scoring is executed by the Recruiting Team.")

        st.divider()

        # Sort by overall_score descending — rank 1 = best
        sorted_candidates = sorted(
            candidates_data,
            key=lambda c: c.get("overall_score") or -1,
            reverse=True
        )
        # Default selection = top-ranked candidate
        if st.session_state.ed_selected_candidate_id is None and sorted_candidates:
            st.session_state.ed_selected_candidate_id = sorted_candidates[0]["id"]

        # Anchor div used purely so the CSS above can target the row that follows
        st.markdown('<div id="rank-sidebar-anchor"></div>', unsafe_allow_html=True)

        main_col, side_col = st.columns([3.5, 1.5])

        # ── Right-hand ranked candidate rail (locked + independently scrollable) ──
        with side_col:
            st.markdown("#### Candidates")
            rank_rail = st.container(height=810, border=False)
            with rank_rail:
                for idx, cd in enumerate(sorted_candidates):
                    rank   = idx + 1
                    score  = cd.get("overall_score")
                    p_json = cd.get("profile_json") or {}
                    personal = p_json.get("candidate_profile", p_json).get("personal_information", {})
                    name = f"{personal.get('first_name','') or ''} {personal.get('last_name','') or ''}".strip() or cd["filename"]
                    label = f"#{rank} {name}" + (f" — {int(score)}%" if score is not None else " — Not scored")
                    is_selected = (cd["id"] == st.session_state.ed_selected_candidate_id)
                    if st.button(label, key=f"ed_rank_btn_{cd['id']}",
                                 type="primary" if is_selected else "secondary",
                                 use_container_width=True):
                        st.session_state.ed_selected_candidate_id = cd["id"]
                        st.rerun()

        # ── Centre panel — only the selected candidate ──────────────────────
        with main_col:
            selected_cd = next(
                (c for c in sorted_candidates if c["id"] == st.session_state.ed_selected_candidate_id),
                None
            )

            if selected_cd is None:
                st.info("Select a candidate from the panel on the right.")
            else:
                cd = selected_cd
                rank = next(i + 1 for i, c in enumerate(sorted_candidates) if c["id"] == cd["id"])
                scores     = cd.get("scores_json")
                has_scores = scores is not None

                profile_json_data = cd.get("profile_json") or {}
                personal = profile_json_data.get("candidate_profile", profile_json_data).get("personal_information", {})
                first_name = personal.get("first_name", "_")
                last_name  = personal.get("last_name", "_")
                cand_email = personal.get("email", "_")
                cand_phone = personal.get("phone_number", "_")

                if has_scores:
                    overall = int(scores.get("overall_score", 0))
                    factors_passed = sum(
                        1 for f in st.session_state.ed_factors
                        if scores.get(f["name"].lower().replace(" ", "_"), 0) >= f["threshold"]
                    )
                    # Mandatory Skills Filtering
                    pj = cd.get("profile_json") or {}
                    skills_dict = pj.get("candidate_profile", pj).get("skills", {})
                    all_cand_skills = []
                    for k in ["programming_languages", "frameworks_and_tools", "soft_skills"]:
                        all_cand_skills.extend(skills_dict.get(k) or [])
                    
                    all_cand_skills_lower = [s.lower() for s in all_cand_skills]
                    
                    missing_skills = []
                    for req_skill in (st.session_state.ed_extracted_skills or []):
                        if not any(req_skill.lower() in cand_skill or cand_skill in req_skill.lower() for cand_skill in all_cand_skills_lower):
                            missing_skills.append(req_skill)
                            
                    if not missing_skills:
                        verdict_label = "✅ Recommended"
                        verdict_color = "#4caf50"
                    else:
                        missing_str = ", ".join(missing_skills[:2]) + ("..." if len(missing_skills)>2 else "")
                        verdict_label = f"❌ Missing: {missing_str}"
                        verdict_color = "#f55"
                else:
                    overall = None
                    shortlisted   = False
                    verdict_label = "⏳ Not Scored"
                    verdict_color = "#888"

                st.markdown(
                    f'<div class="resume-header">'
                    f'<h3>#{rank} &nbsp; {first_name} {last_name}'
                    + (f' &nbsp;<span style="font-size:0.85rem; color:{verdict_color};">{verdict_label}</span>')
                    + '</h3>'
                    + f'<div class="resume-meta">'
                    + f'{cand_email} &nbsp;|&nbsp; {cand_phone} &nbsp;|&nbsp; {cd["filename"]}'
                    + (f' &nbsp;|&nbsp; <strong>Score: {overall}%</strong>' if overall is not None else '')
                    + '</div>'
                    + '</div>',
                    unsafe_allow_html=True
                )

                if not has_scores:
                    st.info("No score yet. Click 'Score All Candidates' above.")
                else:
                    st.progress(overall / 100.0)
                    st.write("")
                    st.markdown("#### Evaluation Breakdown")

                    factor_cols = st.columns(len(st.session_state.ed_factors))
                    for col, factor in zip(factor_cols, st.session_state.ed_factors):
                        key       = factor["name"].lower().replace(" ", "_")
                        score_val = scores.get(key, 0)
                        threshold = factor["threshold"]
                        passed    = score_val >= threshold
                        delta_str = f"≥{threshold}% ✓" if passed else f"<{threshold}% ✗"
                        with col:
                            st.metric(
                                label=factor["name"],
                                value=f"{score_val}%",
                                delta=delta_str,
                                delta_color="normal" if passed else "inverse"
                            )

                    st.write("")
                    st.write("")
                    st.markdown("#### Evaluation Summary")
                    st.info(scores.get("summary", "No evaluation summary returned by the model."))

                # ── Candidate Activity Timeline ────────────────────────────────
                st.write("")
                st.markdown("#### Candidate Activity Timeline")
                
                left_col, right_col = st.columns([2, 3])
                
                with left_col:
                    current_role = st.session_state.get("current_user_role", "Recruiter")
                    if current_role == "Interviewer":
                        form_label = "Add Interview Feedback & Rating:"
                        form_placeholder = "Submit technical interview notes, candidate rating (e.g. 4/5), and recommendations..."
                        btn_label = "Submit Interview Feedback"
                    else:
                        form_label = "Add note / update candidate status:"
                        form_placeholder = "Write a note about this candidate..."
                        btn_label = "Add Comment"

                    # Add new comment form
                    with st.form(key=f"ed_new_comment_form_{cd['id']}", clear_on_submit=True):
                        new_text = st.text_area(label=form_label, height=220, placeholder=form_placeholder)
                        submitted = st.form_submit_button(btn_label, use_container_width=True, type="primary")
                        if submitted and new_text.strip():
                            session = open_session()
                            try:
                                user_email = st.user.email
                                # Use current authenticated user's name/role from session_state
                                user_name = st.session_state.get("current_user_name") or st.user.name or st.user.email.split("@")[0]
                                user_role = st.session_state.get("current_user_role") or "Recruiter"
                                
                                new_comment = CandidateComment(
                                    candidate_id=cd["id"],
                                    author_name=user_name,
                                    author_role=user_role,
                                    comment_text=new_text.strip(),
                                    created_at=datetime.now()
                                )
                                session.add(new_comment)
                                session.commit()
                                st.toast("✅ Comment added to timeline!")
                                st.rerun()
                            except Exception as e:
                                session.rollback()
                                st.error(f"Failed to add comment: {e}")
                            finally:
                                session.close()
                
                with right_col:
                    session = open_session()
                    try:
                        comments = (
                            session.query(CandidateComment)
                            .filter_by(candidate_id=cd["id"])
                            .order_by(CandidateComment.created_at.desc())
                            .all()
                        )
                        
                        if not comments:
                            st.caption("No notes or activity logged for this candidate yet.")
                        else:
                            # Render a beautiful HTML table for the remarks
                            # Note: NO fixed height for the div: st.container will control scrolling
                            table_html = """
                            <div style="border: 1.5px solid #C8A96E; border-radius: 8px; overflow: hidden">
                                <table style="width: 100%; border-collapse: collapse; font-family: sans-serif; background-color: #F5EAD0; text-align: left; font-size: 0.88rem;">
                                    <thead>
                                        <tr style="background-color: #EDD9A3; color: #690e0e; border-bottom: 2px solid #C8A96E;">
                                            <th style="padding: 10px 12px; font-weight: bold; width: 25%;">User Name</th>
                                            <th style="padding: 10px 12px; font-weight: bold; width: 20%;">Role</th>
                                            <th style="padding: 10px 12px; font-weight: bold; width: 25%;">Date & Time</th>
                                            <th style="padding: 10px 12px; font-weight: bold; width: 30%;">Remarks</th>
                                        </tr>
                                    </thead>
                                <tbody>
                            """
                            for comment in comments:
                                date_str = comment.created_at.strftime('%b %d, %Y %H:%M')
                                # Style role badge
                                role_bg = "#690e0e"
                                role_color = "#F5EAD0"
                                if comment.author_role.lower() == "admin":
                                    role_bg = "#d9534f"
                                elif comment.author_role.lower() == "lead recruiter":
                                    role_bg = "#f0ad4e"
                                
                                table_html += f"""
                                        <tr style="border-bottom: 1px solid #E6D0A7; color: #2A1407;">
                                            <td style="padding: 8px 12px; font-weight: 600;">{comment.author_name}</td>
                                            <td style="padding: 8px 12px;">
                                                <span style="background: {role_bg}; color: {role_color}; padding: 2px 6px; border-radius: 10px; font-size: 0.72rem; font-weight: bold; display: inline-block;">
                                                    {comment.author_role}
                                                </span>
                                            </td>
                                            <td style="padding: 8px 12px; font-size: 0.8rem; color: #7a5c3a;">{date_str}</td>
                                            <td style="padding: 8px 12px; white-space: pre-wrap; line-height: 1.3;">{comment.comment_text}</td>
                                        </tr>"""
                            
                            table_html += """
                                    </tbody>
                                </table>
                            </div>
                            """
                            # Clean whitespace to prevent Markdown from interpreting indented lines as code blocks
                            clean_table_html = "\n".join([line.strip() for line in table_html.split("\n")])
                            # st.container handles scroll + height — keeps the outer column border clean
                            scroll_box = st.container(height=310, border=False)
                            with scroll_box:
                                st.markdown(clean_table_html, unsafe_allow_html=True)
                    finally:
                        session.close()

# Render hidden logout button at the absolute bottom to prevent top spacing
import utils
utils.render_hidden_logout_button()
