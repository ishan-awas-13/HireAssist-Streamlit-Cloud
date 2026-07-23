"""
Page 1 — Job Post & Workspace Creation
=======================================
Recruiters fill out a job posting form here. On submission, a new record is
written to the `job_posts` PostgreSQL table, which becomes the workspace
container for all resumes uploaded in Page 2.

Key design decisions:
  - SQLAlchemy session is opened, committed, and closed within the button
    handler — no session leaks across Streamlit re-runs.
  - `init_db()` is called at module load so the table always exists before
    any writes attempt to happen.
  - Streamlit stores the newly created job_post.id in session_state so
    Page 2 can read it and automatically pre-select the new workspace.
"""

import sys
import os

# Allow importing sibling modules (database.py, etc.) from src/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from datetime import datetime
from sqlalchemy.exc import OperationalError
import utils

# Require user login and Recruiter role before loading the page
utils.require_login()
utils.enforce_role(["Recruiter"], page_name="Creating & Editing Job Workspaces")

from database import init_db, open_session, JobPost

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Create Job Post — Enterprise Resume Parser",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Inject global utility CSS ───────────────────────────────────────────────
utils.inject_global_css()

# ── Attempt DB initialisation (gracefully handles no-DB local dev) ────────────
db_available = True
try:
    init_db()
except OperationalError as e:
    db_available = False
    _db_error_msg = str(e)

# ── Global CSS (warm-earth theme consistent with config.toml) ─────────────────
st.markdown("""
    <style>
    /* ── Page-level typography tweaks ───────────────────────────────────── */
    div[data-testid="stMarkdownContainer"] p { font-size: 0.95rem; }

    /* ── Sidebar column guard (inherited from app.py pattern) ───────────── */
    section[data-testid="stSidebar"] div[data-testid="stColumn"] {
        border: none !important;
        border-radius: 0 !important;
        padding: 0 2px !important;
    }
    /* Hide sidebar collapse button ─────────────────────────────────────── */
    section[data-testid="stSidebar"] [data-testid="collapsedControl"] {
        display: none !important;
    }

    /* ── Page hero banner ────────────────────────────────────────────────── */
    .page-hero {
        background: linear-gradient(135deg, #1f0404 0%, #3d0808 55%, #690e0e 100%);
        border-radius: 14px;
        padding: 25px 40px;
        margin-bottom: 30px;
        color: #F5EAD0;
        box-shadow: 0 4px 30px rgba(105,14,14,0.18);
    }
    .page-hero h1 {
        font-size: 2rem;
        font-weight: 700;
        margin: 0 0 6px 0;
        letter-spacing: -0.01em;
    }
    .page-hero p {
        font-size: 0.97rem !important;
        opacity: 0.82;
        margin: 0;
    }

    /* ── Form section divider ───────────────────────────────────────────────── */
    .form-card {
        background: transparent;
        border: none;
        margin-bottom: 36px;
    }

    .form-card-title {
        font-size: 1.7rem;
        font-weight: bold;
        color: black;
        margin-bottom: 4px;
        letter-spacing: 0.01em;
    }
    .form-card-sub {
        font-size: 0.82rem;
        color: #7a5c3a;
        margin-bottom: 18px;
    }

    /* ── Saved workspace pill list ───────────────────────────────────────── */
    .workspace-pill {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: #F5EAD0;
        border: 1.5px solid #C8A96E;
        border-radius: 20px;
        padding: 5px 14px;
        margin: 4px;
        font-size: 0.88rem;
        color: #2A1407;
        font-weight: 500;
    }
    .workspace-pill .dot {
        width: 8px; height: 8px;
        border-radius: 50%;
        background: #4caf50;
        flex-shrink: 0;
    }
    .workspace-pill .dot.inactive { background: #aaa; }

    /* ── Status label ─────────────────────────────────────────────────────── */
    .status-badge {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 10px;
        font-size: 0.78rem;
        font-weight: 600;
    }
    .status-active   { background:#d4edda; color:#155724; }
    .status-inactive { background:#f8d7da; color:#721c24; }

    /* ── Recent workspaces table ─────────────────────────────────────────── */
    .recent-table { width: 100%; border-collapse: collapse; font-size: 0.9rem; }
    .recent-table th {
        text-align: left; padding: 8px 12px;
        background: #D4B483; color: #2A1407;
        font-weight: 600; font-size: 0.8rem;
        text-transform: uppercase; letter-spacing: 0.05em;
    }
    .recent-table td { padding: 9px 12px; border-bottom: 1px solid #C8A96E; }
    .recent-table tr:last-child td { border-bottom: none; }
    .recent-table tr:hover td { background: #EDD9A3; }

    /* ── Divider label ───────────────────────────────────────────────────── */
    .section-label {
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.09em;
        text-transform: uppercase;
        color: #7a5c3a;
        margin-bottom: 10px;
    }

    /*making the UI take more horizontal space*/
    div.block-container, [data-testid = "stAppViewBlockContainer"] { 
        padding-top: 3rem !important;
        max-width: 98% !important; 
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }
    
    </style>
""", unsafe_allow_html=True)


# ── Session state defaults ─────────────────────────────────────────────────────
if "last_created_job_id" not in st.session_state:
    st.session_state.last_created_job_id = None
if "form_submitted" not in st.session_state:
    st.session_state.form_submitted = False

#Some code for displaying minimal info 
# about current page in the sidebar
#st.markdown("## Job Post Creator")
#st.caption("Step 1 of 3 — Define your hiring workspace.")
#st.divider()



# ── Sidebar: recent workspaces ────────────────────────────────────────────────
with st.sidebar:

    if not db_available:
        st.error("⚠️ Database unavailable.\nCheck your DATABASE_URL env var.")
    else:
        st.markdown("### Recent Workspaces")
        session = open_session()
        try:
            recent = (
                session.query(JobPost)
                .order_by(JobPost.created_at.desc())
                .limit(8)
                .all()
            )
            if not recent:
                st.caption("No workspaces yet. Create one using the form →")
            else:
                for jp in recent:
                    status_cls = "status-active" if jp.is_active else "status-inactive"
                    status_txt = "Active" if jp.is_active else "Closed"
                    dot_cls    = "" if jp.is_active else " inactive"
                    st.markdown(
                        f'<div class="workspace-pill">'
                        f'<span class="dot{dot_cls}"></span>'
                        f'<span><strong>#{jp.id}</strong> {jp.title[:28]}{"…" if len(jp.title)>28 else ""}</span>'
                        f'</div>',
                        unsafe_allow_html=True
                    )
        finally:
            session.close()

    #st.divider()
    #st.markdown("### 🔀 Quick Navigation")
    #st.page_link("pages/2_Data_Hub.py", label="→ Page 2: Data Hub & Upload")
    #st.page_link("pages/3_Evaluation_Dashboard.py", label="→ Page 3: Evaluation Dashboard")


# ── Page Hero ─────────────────────────────────────────────────────────────────
st.markdown("""
    <div class="page-hero">
        <h1>Create a Job Post Workspace</h1>
        <p>Define the role, paste the job description, and set baseline evaluation criteria.
           Each submission creates a persistent workspace that resumes are uploaded into on Page 2.</p>
    </div>
""", unsafe_allow_html=True)

if not db_available:
    st.error(
        f"**Database connection failed.** The form is in read-only preview mode.\n\n"
        f"Set a valid `DATABASE_URL` environment variable and restart.\n\n"
        f"```\n{_db_error_msg}\n```",
        icon="🔌"
    )

# ── Main form ─────────────────────────────────────────────────────────────────
col_form, col_preview = st.columns([3, 2], gap="large")

with col_form:
    # ── Section 1: Role Basics ────────────────────────────────────────────────
    st.markdown('<div class="form-card">', unsafe_allow_html=True)
    st.markdown('<div class="form-card-title">Role Basics</div>', unsafe_allow_html=True)
    st.markdown('<div class="form-card-sub">Core metadata that identifies this job posting.</div>', unsafe_allow_html=True)

    job_title = st.text_input(
        "Job Title *",
        placeholder="e.g. Senior Backend Engineer",
        key="jp_title",
        help="Required. The name of the role you are hiring for."
    )

    meta_col1, meta_col2, meta_col3 = st.columns(3)
    with meta_col1:
        department = st.text_input(
            "Department",
            placeholder="e.g. Engineering",
            key="jp_department"
        )
    with meta_col2:
        location = st.text_input(
            "Location",
            placeholder="e.g. Remote / Bangalore",
            key="jp_location"
        )
    with meta_col3:
        employment_type = st.selectbox(
            "Employment Type",
            options=["Full-Time", "Part-Time", "Contract", "Internship", "Freelance"],
            index=0,
            key="jp_emp_type"
        )

    st.markdown('</div>', unsafe_allow_html=True)

    # ── Section 2: Job Description ────────────────────────────────────────────
    st.markdown('<div class="form-card">', unsafe_allow_html=True)
    st.markdown('<div class="form-card-title">Job Description</div>', unsafe_allow_html=True)
    st.markdown('<div class="form-card-sub">Paste the full JD. This is used by the AI on Page 2 to extract mandatory skills and score candidates.</div>', unsafe_allow_html=True)

    job_description = st.text_area(
        "Full Job Description",
        placeholder="Paste the complete job description here — responsibilities, requirements, qualifications...",
        height=260,
        key="jp_description"
    )
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Section 3: Evaluation Baseline ───────────────────────────────────────
    st.markdown('<div class="form-card">', unsafe_allow_html=True)
    st.markdown('<div class="form-card-title" type=strong>Evaluation Baseline</div>', unsafe_allow_html=True)
    st.markdown('<div class="form-card-sub">Pre-configure the scoring factors for this workspace. These can be adjusted later in Page 3.</div>', unsafe_allow_html=True)

    DEFAULT_FACTORS = [
        {"name": "Skills Match",      "threshold": 60},
        {"name": "Role Relevance",    "threshold": 60},
        {"name": "Experience Match",  "threshold": 50},
        {"name": "Education Match",   "threshold": 50},
    ]

    if "jp_factors" not in st.session_state:
        st.session_state.jp_factors = DEFAULT_FACTORS.copy()

    # Factor list editor
    factor_to_remove = None
    for i, factor in enumerate(st.session_state.jp_factors):
        fc1, fc2 = st.columns([4, 1])
        with fc1:
            factor["threshold"] = st.slider(
                f"{factor['name']}",
                min_value=0, max_value=100,
                value=factor["threshold"],
                step=5,
                key=f"jp_factor_slider_{i}",
                help=f"Minimum passing score for {factor['name']}"
            )
        with fc2:
            st.write("")  # vertical align
            if st.button("❌", key=f"jp_remove_factor_{i}", help=f"Remove {factor['name']}"):
                factor_to_remove = i

    if factor_to_remove is not None:
        st.session_state.jp_factors.pop(factor_to_remove)
        st.rerun()

    # Add new factor inline
    def _add_new_factor():
        name = st.session_state.jp_new_factor_name.strip()
        existing = [f["name"].lower() for f in st.session_state.jp_factors]

        if not name:
            st.toast("Enter a factor name first.", icon = "⚠️")

        elif name.lower() in existing:
            st.toast(f"'{name}' already exists.", icon = "⚠️")
        else:
            st.session_state.jp_factors.append({
                "name":name,
                "threshold": st.session_state.jp_new_factor_thresh
            })
            #forcefully clear the fields in background
            st.session_state.jp_new_factor_name = ""
            st.session_state.jp_new_factor_thresh = 60

    add_col1, add_col2, add_col3 = st.columns([3, 2, 1])
    with add_col1:
        new_factor_name = st.text_input(
            "New factor name",
            placeholder="e.g. Communication Skills",
            key="jp_new_factor_name",
            label_visibility="collapsed"
        )
    with add_col2:
        new_factor_thresh = st.slider(
            "Threshold",
            min_value=0, max_value=100, value=60, step=5,
            key="jp_new_factor_thresh",
            label_visibility="collapsed"
        )
    with add_col3:

        st.write("")
        #Use on click to trigger the logic
        st.button("➕ Add", key="jp_add_factor_btn", use_container_width=True, on_click=_add_new_factor)
      
      
      
       #"""st.write("")
       # if st.button("➕ Add", key="jp_add_factor_btn", use_container_width=True):
        #    name = new_factor_name.strip()
         #   existing = [f["name"].lower() for f in st.session_state.jp_factors]
          #  if not name:
           #     st.warning("Enter a factor name first.")
            #elif name.lower() in existing:
             #   st.warning(f"'{name}' already exists.")
            #else:
             #   st.session_state.jp_factors.append({"name": name, "threshold": new_factor_thresh})
              #  ##Delete the widget keys (text) from sessions state so the field is cleared
               # if "jp_new_factor_name" in st.session_state:
                #    del st.session_state["jp_new_factor_name"]
                #if "jp_new_factor_thresh" in st.session_state:
                 #   del st.session_state["jp_new_factor_thresh"]
                #st.rerun()
            


    notes = st.text_area(
        "Internal Notes (optional)",
        placeholder="Any additional context for your recruiting team...",
        height=80,
        key="jp_notes"
    )
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Submit button ─────────────────────────────────────────────────────────
    submit_col, _ = st.columns([1, 2])
    with submit_col:
        submitted = st.button(
            "Create Workspace",
            type="primary",
            use_container_width=True,
            disabled=not db_available,
            key="jp_submit_btn",
            help="Save this job post to PostgreSQL and open the upload workspace."
        )

    if submitted:
        if not job_title.strip():
            st.error("❌ Job Title is required.")
        else:
            session = open_session()
            try:
                new_post = JobPost(
                    title           = job_title.strip(),
                    department      = department.strip() or None,
                    location        = location.strip() or None,
                    employment_type = employment_type,
                    description     = job_description.strip() or None,
                    mandatory_skills = [],          # populated by AI on Page 2
                    eval_factors    = st.session_state.jp_factors,
                    notes           = notes.strip() or None,
                    is_active       = True,
                    created_at      = datetime.utcnow(),
                )
                session.add(new_post)
                session.commit()
                session.refresh(new_post)

                # Persist to session_state for cross-page handoff
                st.session_state.last_created_job_id    = new_post.id
                st.session_state.active_job_post_id     = new_post.id
                st.session_state.active_job_post_title  = new_post.title
                st.session_state.form_submitted         = True

                st.success(
                    f"✅ Workspace **#{new_post.id} — {new_post.title}** created successfully!  \n\n"
                    f"Head to **Page 2** to start uploading resumes."
                )
                #st.balloons()
                st.toast("Settings saved successfully!", icon="✅")
            

            except Exception as e:
                session.rollback()
                st.error(f"❌ Database write failed: {e}")
            finally:
                session.close()


# ── Right column: live preview card ───────────────────────────────────────────
with col_preview:
    #st.markdown('<div class="form-card-title" style = "padding-top: 30px;">Workspace Preview</div>', unsafe_allow_html=True)
    #st.markdown("### Workspace Preview")

    st.markdown('<div class="form-card">', unsafe_allow_html=True)
    st.markdown('<div class="form-card-title">Workspace Preview</div>', unsafe_allow_html=True)
    st.caption("Live preview of what will be saved.")
    #st.divider()

    title_val  = st.session_state.get("jp_title", "").strip() or "*Untitled Role*"
    dept_val   = st.session_state.get("jp_department", "").strip() or "—"
    loc_val    = st.session_state.get("jp_location", "").strip() or "—"
    type_val   = st.session_state.get("jp_emp_type", "Full-Time")
    desc_val   = st.session_state.get("jp_description", "").strip()
    factors    = st.session_state.get("jp_factors", DEFAULT_FACTORS)

    st.markdown(f"""
        <div style="background:#EDD9A3; border:1.5px solid #C8A96E; border-radius:12px; padding:22px 24px;">
            <div style="font-size:1.25rem; font-weight:700; color:#690e0e; margin-bottom:2px;">{title_val}</div>
            <div style="font-size:0.82rem; color:#7a5c3a; margin-bottom:14px;">
                {dept_val} &nbsp;·&nbsp; {loc_val} &nbsp;·&nbsp; {type_val}
            </div>
            <div style="font-size:0.78rem; font-weight:700; letter-spacing:0.06em;
                        text-transform:uppercase; color:#7a5c3a; margin-bottom:6px;">
                Evaluation Factors
            </div>
            {''.join(
                f'<div style="display:flex; justify-content:space-between; align-items:center; '
                f'padding:5px 0; border-bottom:1px solid #C8A96E; font-size:0.87rem;">'
                f'<span>{f["name"]}</span>'
                f'<span style="font-weight:600; color:#690e0e;">≥{f["threshold"]}%</span></div>'
                for f in factors
            )}
        </div>
    """, unsafe_allow_html=True)

    if desc_val:
        st.write("")
        with st.expander("📄 Job Description Preview", expanded=False):
            st.write(desc_val[:1200] + ("…" if len(desc_val) > 1200 else ""))

    st.write("")

    # ── All existing workspaces table ─────────────────────────────────────────
    if db_available:
        st.markdown("###  All Workspaces")
        session = open_session()
        try:
            all_posts = (
                session.query(JobPost)
                .order_by(JobPost.created_at.desc())
                .limit(20)
                .all()
            )
            if not all_posts:
                st.caption("No workspaces saved yet.")
            else:
                rows_html = ""
                for jp in all_posts:
                    status_cls = "status-active" if jp.is_active else "status-inactive"
                    status_txt = "Active" if jp.is_active else "Closed"
                    candidate_count = jp.candidates.count()
                    rows_html += (
                        f"<tr>"
                        f"<td><strong>#{jp.id}</strong></td>"
                        f"<td>{jp.title}</td>"
                        f"<td>{jp.department or '—'}</td>"
                        f"<td>{candidate_count}</td>"
                        f"<td><span class='status-badge {status_cls}'>{status_txt}</span></td>"
                        f"<td style='font-size:0.78rem; color:#7a5c3a;'>{jp.created_at.strftime('%b %d, %Y')}</td>"
                        f"</tr>"
                    )
                st.markdown(f"""
                    <table class="recent-table">
                        <thead>
                            <tr>
                                <th>#</th><th>Title</th><th>Dept.</th>
                                <th>Candidates</th><th>Status</th><th>Created</th>
                            </tr>
                        </thead>
                        <tbody>{rows_html}</tbody>
                    </table>
                """, unsafe_allow_html=True)
        finally:
            session.close()

# Render hidden logout button at the absolute bottom to prevent top spacing
import utils
utils.render_hidden_logout_button()
