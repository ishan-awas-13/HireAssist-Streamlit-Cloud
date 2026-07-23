"""
0_Admin_Panel.py — Developer-only Admin Panel
==============================================
Accessible only by: ishanawasthi1306@gmail.com
Displays all registered users with their details and allows secure deletion.
- Self-delete protection for the developer account.
- Confirmation required before any deletion.
- All operations are performed directly at the DB level.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from database import open_session, User
from utils import require_login, inject_global_css, render_sidebar_profile

# ── Constants ──────────────────────────────────────────────────────────────────
DEVELOPER_EMAIL = st.secrets.get("admin", {}).get("developer_email", "")

# ── Auth Gates ─────────────────────────────────────────────────────────────────
# Gate 1: Must be logged in at all
if not st.user.is_logged_in:
    st.switch_page("app.py")
    st.stop()

# Gate 2: Must be an Admin account (role == 'Admin' or matching developer_email)
from utils import has_role
if not has_role(["Admin"]):
    st.set_page_config(page_title="Access Denied", page_icon="🚫", layout="centered")
    st.error("🚫 Access Denied. This page is restricted to platform administrators.")
    st.stop()

# ── Page Config (only set if authorized) ──────────────────────────────────────
st.set_page_config(
    page_title="Admin Panel — HireAssist AI",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_global_css()
render_sidebar_profile()

# ── Page CSS ──────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');

div.block-container, [data-testid="stAppViewBlockContainer"] {
    padding-top: 2.5rem !important;
    max-width: 98% !important;
    padding-left: 1.5rem !important;
    padding-right: 1.5rem !important;
    font-family: 'Inter', sans-serif;
}

.admin-hero {
    background: linear-gradient(135deg, #1f0404 0%, #3d0808 55%, #690e0e 100%);
    border-radius: 16px;
    padding: 28px 40px;
    margin-bottom: 28px;
    color: #e0e8ff;
    box-shadow: 0 8px 40px rgba(15,52,96,0.30);
    display: flex;
    align-items: center;
    gap: 20px;
}
.admin-hero .icon { font-size: 2.8rem; }
.admin-hero h1   { font-size: 2rem; font-weight: 800; margin: 0 0 4px 0; letter-spacing: -0.02em; }
.admin-hero p    { font-size: 0.9rem; opacity: 0.75; margin: 0; }

.user-table-wrap {
    background: #F5EAD0;
    border: 1.5px solid #C8A96E;
    border-radius: 14px;
    overflow: hidden;
    margin-bottom: 30px;
    box-shadow: 0 4px 20px rgba(105,14,14,0.08);
}
.user-table-header {
    background: linear-gradient(90deg, #690e0e, #3d0808);
    color: #F5EAD0;
    display: grid;
    grid-template-columns: 2fr 2fr 1.2fr 1.5fr 0.8fr;
    padding: 14px 20px;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
}
.user-row {
    display: grid;
    grid-template-columns: 2fr 2fr 1.2fr 1.5fr 0.8fr;
    padding: 14px 20px;
    font-size: 0.88rem;
    color: #2A1407;
    border-top: 1px solid #e0c990;
    align-items: center;
    transition: background 0.15s;
}
.user-row:hover { background: #EDD9A3; }
.user-row.dev-row { background: #fef9f0; }
.role-badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 12px;
    font-size: 0.73rem;
    font-weight: 700;
    background: #690e0e;
    color: #F5EAD0;
}
.role-badge.admin  { background: #1a1a2e; color: #e0e8ff; }
.role-badge.recruiter { background: #2e7d32; color: #fff; }
.dev-shield {
    font-size: 0.72rem;
    color: #7a5c3a;
    font-style: italic;
}
.stat-strip {
    display: flex;
    gap: 16px;
    margin-bottom: 24px;
}
.stat-chip {
    background: #EDD9A3;
    border: 1.5px solid #C8A96E;
    border-radius: 10px;
    padding: 12px 24px;
    text-align: center;
    min-width: 140px;
}
.stat-chip .sv { font-size: 2rem; font-weight: 800; color: #690e0e; }
.stat-chip .sl { font-size: 0.72rem; color: #7a5c3a; text-transform: uppercase; letter-spacing: 0.06em; margin-top: 2px; }

.danger-zone {
    background: #fff5f5;
    border: 1.5px solid #ffcdd2;
    border-radius: 14px;
    padding: 20px 28px;
    margin-top: 10px;
}
.danger-zone h3 { color: #c62828; font-size: 1rem; margin: 0 0 6px 0; }
.danger-zone p  { font-size: 0.85rem; color: #7a5c3a; margin: 0; }
</style>
""", unsafe_allow_html=True)

# ── Hero Header ───────────────────────────────────────────────────────────────
st.markdown("""
<div class="admin-hero">
    <div class="icon">🛡️</div>
    <div>
        <h1>Developer Admin Panel</h1>
        <p>Restricted access · View and manage all registered platform users · Database-level operations only</p>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Load Users from DB ────────────────────────────────────────────────────────
session = open_session()
try:
    all_users = session.query(User).order_by(User.created_at.asc()).all()
    # Snapshot the data so we can close the session safely
    users_data = [
        {
            "id":         u.id,
            "email":      u.email,
            "name":       u.name,
            "role":       u.role or "—",
            "created_at": u.created_at.strftime("%d %b %Y, %I:%M %p") if u.created_at else "—",
        }
        for u in all_users
    ]
finally:
    session.close()

total_users = len(users_data)
admin_count = sum(1 for u in users_data if u["role"].lower() == "admin")
recruiter_count = total_users - admin_count

# ── Stats Strip ───────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="stat-strip">
    <div class="stat-chip"><div class="sv">{total_users}</div><div class="sl">Total Users</div></div>
    <div class="stat-chip"><div class="sv">{admin_count}</div><div class="sl">Admins</div></div>
    <div class="stat-chip"><div class="sv">{recruiter_count}</div><div class="sl">Recruiters</div></div>
</div>
""", unsafe_allow_html=True)

# ── User Table ────────────────────────────────────────────────────────────────
st.markdown("### Registered Users")

st.markdown("""
<div class="user-table-wrap">
    <div class="user-table-header">
        <span>Name</span>
        <span>Email</span>
        <span>Role</span>
        <span>Registered At</span>
        <span>Action</span>
    </div>
</div>
""", unsafe_allow_html=True)

if not users_data:
    st.info("No users registered yet.")
else:
    for user in users_data:
        is_dev = user["email"] == DEVELOPER_EMAIL
        role_class = "admin" if user["role"].lower() == "admin" else "recruiter" if user["role"].lower() == "recruiter" else ""

        col_name, col_email, col_role, col_date, col_action = st.columns([2, 2, 1.2, 1.5, 0.8])

        with col_name:
            st.markdown(
                f"{'🛡️ ' if is_dev else ''}<strong style='color:#2A1407'>{user['name']}</strong>",
                unsafe_allow_html=True
            )
        with col_email:
            st.markdown(
                f"<span style='color:#690e0e;font-size:0.88rem'>{user['email']}</span>",
                unsafe_allow_html=True
            )
        with col_role:
            st.markdown(
                f"<span class='role-badge {role_class}'>{user['role']}</span>",
                unsafe_allow_html=True
            )
        with col_date:
            st.markdown(
                f"<span style='font-size:0.82rem;color:#7a5c3a'>{user['created_at']}</span>",
                unsafe_allow_html=True
            )
        with col_action:
            if is_dev:
                st.markdown("<span class='dev-shield'>🔒 Protected</span>", unsafe_allow_html=True)
            else:
                delete_key = f"delete_btn_{user['id']}"
                if st.button("❌ Delete", key=delete_key, type="primary", use_container_width=True):
                    st.session_state[f"confirm_delete_{user['id']}"] = True

        # Confirmation zone (renders below the row if triggered)
        if st.session_state.get(f"confirm_delete_{user['id']}", False):
            with st.container():
                st.markdown(f"""
                <div class="danger-zone">
                    <h3>⚠️ Confirm Deletion</h3>
                    <p>You are about to permanently delete <strong>{user['name']}</strong>
                    (<code>{user['email']}</code>) from the platform. This will remove their
                    account from the database. This action cannot be undone.</p>
                </div>
                """, unsafe_allow_html=True)

                confirm_col, cancel_col, _ = st.columns([1.2, 1, 4])
                with confirm_col:
                    if st.button(
                        f"✅ Yes, Delete",
                        key=f"confirm_yes_{user['id']}",
                        type="primary",
                        use_container_width=True,
                    ):
                        # ── SECURE DB-LEVEL DELETION ──────────────────────
                        del_session = open_session()
                        try:
                            target = del_session.query(User).filter_by(id=user["id"]).first()
                            if target and target.email != DEVELOPER_EMAIL:  # double-guard
                                del_session.delete(target)
                                del_session.commit()
                                st.success(f"✅ User **{user['name']}** deleted successfully.")
                            elif target and target.email == DEVELOPER_EMAIL:
                                st.error("🚫 Cannot delete the developer account.")
                            else:
                                st.warning("User not found — may have already been deleted.")
                        except Exception as e:
                            del_session.rollback()
                            st.error(f"Deletion failed: {e}")
                        finally:
                            del_session.close()
                        # Clear confirmation state and refresh page
                        st.session_state.pop(f"confirm_delete_{user['id']}", None)
                        st.rerun()

                with cancel_col:
                    if st.button(
                        "Cancel",
                        key=f"confirm_no_{user['id']}",
                        use_container_width=True,
                    ):
                        st.session_state.pop(f"confirm_delete_{user['id']}", None)
                        st.rerun()

        st.divider()

# ── Footer note ───────────────────────────────────────────────────────────────
# This panel is only visible when logged in as <code>[EMAIL_ADDRESS]</code>.
st.markdown("""
<div style="text-align:center; margin-top:20px; font-size:0.78rem; color:#a08060;">
    🛡️ All deletions are permanent and cannot be reversed.<br>
</div>
""", unsafe_allow_html=True)

# Render hidden logout button at the absolute bottom to prevent top spacing
import utils
utils.render_hidden_logout_button()
