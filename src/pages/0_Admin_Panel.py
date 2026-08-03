"""
0_Admin_Panel.py — Dynamic RBAC Admin Panel
============================================
Accessible only by users with the `manage_rbac` permission.
Provides three management tabs:
  Tab 1: User Assignment   — assign database-defined roles to users
  Tab 2: Role Management   — create / delete custom roles
  Tab 3: Permission Matrix — toggle permissions per role in a checkbox grid
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from database import open_session, User, Role, Permission, role_permissions
from utils import require_login, inject_global_css, render_sidebar_profile, has_permission

# ── Constants ──────────────────────────────────────────────────────────────────
DEVELOPER_EMAIL = st.secrets.get("admin", {}).get("developer_email", "")

# ── Auth Gates ─────────────────────────────────────────────────────────────────
if not st.user.is_logged_in:
    st.switch_page("app.py")
    st.stop()

# Gate: must have manage_rbac permission (or be the developer)
from utils import enforce_permission
enforce_permission("manage_rbac", page_name="Admin Panel")

# ── Page Config ───────────────────────────────────────────────────────────────
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
.role-badge.hiring-manager { background: #8e24aa; color: #fff; }

.danger-zone {
    background: #fff5f5;
    border: 1.5px solid #ffcdd2;
    border-radius: 14px;
    padding: 20px 28px;
    margin-top: 10px;
}
.danger-zone h3 { color: #c62828; font-size: 1rem; margin: 0 0 6px 0; }
.danger-zone p  { font-size: 0.85rem; color: #7a5c3a; margin: 0; }

.system-badge {
    display: inline-block; background: #C8A96E; color: #2A1407;
    font-size: 0.68rem; font-weight: 700; padding: 2px 8px;
    border-radius: 10px; text-transform: uppercase; letter-spacing: 0.06em;
    margin-left: 6px;
}
</style>
""", unsafe_allow_html=True)

# ── Hero Header ───────────────────────────────────────────────────────────────
st.markdown("""
<div class="admin-hero">
    <div class="icon">🛡️</div>
    <div>
        <h1>Admin Panel</h1>
        <p>Manage users, roles, and feature permissions for the entire platform</p>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Load data ─────────────────────────────────────────────────────────────────
session = open_session()
try:
    all_users = session.query(User).order_by(User.created_at.asc()).all()
    all_roles = session.query(Role).order_by(Role.name.asc()).all()
    all_permissions = session.query(Permission).order_by(Permission.category.asc(), Permission.name.asc()).all()

    users_data = [
        {
            "id": u.id, "email": u.email, "name": u.name,
            "role_names": sorted([r.name for r in u.roles]),
            "created_at": u.created_at.strftime("%d %b %Y, %I:%M %p") if u.created_at else "—",
        }
        for u in all_users
    ]
    roles_data = [
        {
            "id": r.id, "name": r.name, "description": r.description or "",
            "is_system": r.is_system, "user_count": len(r.users),
            "perm_names": {p.name for p in r.permissions},
        }
        for r in all_roles
    ]
    perms_data = [
        {"id": p.id, "name": p.name, "display_name": p.display_name, "category": p.category}
        for p in all_permissions
    ]
finally:
    session.close()

# ── Stats Strip ───────────────────────────────────────────────────────────────
total_users = len(users_data)
total_roles = len(roles_data)
total_perms = len(perms_data)
st.markdown(f"""
<div class="stat-strip">
    <div class="stat-chip"><div class="sv">{total_users}</div><div class="sl">Users</div></div>
    <div class="stat-chip"><div class="sv">{total_roles}</div><div class="sl">Roles</div></div>
    <div class="stat-chip"><div class="sv">{total_perms}</div><div class="sl">Permissions</div></div>
</div>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# TABS
# ═══════════════════════════════════════════════════════════════════════════════
tab_users, tab_roles, tab_perms = st.tabs(["User Assignment", "Role Management", "Permission Matrix"])

role_name_list = [r["name"] for r in roles_data]

# ─── TAB 1: User Assignment ──────────────────────────────────────────────────
with tab_users:
    st.markdown("### Assign Roles to Users")
    st.caption("Assign one or more roles to each user. Effective permissions are the **union** of all assigned roles.")

    if not users_data:
        st.info("No users registered yet.")
    else:
        # Table header
        hdr_cols = st.columns([2, 2.5, 2, 1.5, 0.8])
        hdr_cols[0].markdown("**Name**")
        hdr_cols[1].markdown("**Email**")
        hdr_cols[2].markdown("**Roles**")
        hdr_cols[3].markdown("**Registered**")
        hdr_cols[4].markdown("**Action**")
        st.divider()

        for user in users_data:
            is_dev = user["email"] == DEVELOPER_EMAIL
            cols = st.columns([2, 2.5, 2, 1.5, 0.8])

            with cols[0]:
                prefix = "🛡️ " if is_dev else ""
                st.markdown(f"{prefix}**{user['name']}**")

            with cols[1]:
                st.markdown(f"`{user['email']}`")

            with cols[2]:
                current_roles = user["role_names"]
                new_roles = st.multiselect(
                    "Roles", options=role_name_list, default=[
                        r for r in current_roles if r in role_name_list
                    ],
                    key=f"role_select_{user['id']}", label_visibility="collapsed",
                )
                if sorted(new_roles) != sorted(current_roles):
                    s = open_session()
                    try:
                        target_user = s.query(User).filter_by(id=user["id"]).first()
                        if target_user:
                            resolved_roles = s.query(Role).filter(Role.name.in_(new_roles)).all()
                            target_user.roles = resolved_roles
                            target_user.role = ", ".join(new_roles) if new_roles else ""  # keep legacy in sync
                            s.commit()
                            st.toast(f"✅ {user['name']} → {', '.join(new_roles) or 'No roles'}", icon="✅")
                            st.rerun()
                    except Exception as e:
                        s.rollback()
                        st.error(f"Update failed: {e}")
                    finally:
                        s.close()

            with cols[3]:
                st.caption(user["created_at"])

            with cols[4]:
                if is_dev:
                    st.markdown("<span style='font-size:0.72rem;color:#7a5c3a;font-style:italic;'>🔒 Protected</span>", unsafe_allow_html=True)
                else:
                    delete_key = f"delete_btn_{user['id']}"
                    if st.button("❌", key=delete_key, help="Delete this user", type = "primary"):
                        st.session_state[f"confirm_delete_{user['id']}"] = True

            # Confirmation zone
            if st.session_state.get(f"confirm_delete_{user['id']}", False):
                with st.container():
                    st.markdown(f"""
                    <div class="danger-zone">
                        <h3>⚠️ Confirm Deletion</h3>
                        <p>Permanently delete <strong>{user['name']}</strong> (<code>{user['email']}</code>) from the platform?</p>
                    </div>
                    """, unsafe_allow_html=True)
                    c1, c2, _ = st.columns([1.2, 1, 4])
                    with c1:
                        if st.button("✅ Yes, Delete", key=f"confirm_yes_{user['id']}", type="primary", use_container_width=True):
                            s = open_session()
                            try:
                                target = s.query(User).filter_by(id=user["id"]).first()
                                if target and target.email != DEVELOPER_EMAIL:
                                    s.delete(target)
                                    s.commit()
                                    st.success(f"✅ User **{user['name']}** deleted.")
                                else:
                                    st.error("🚫 Cannot delete the developer account.")
                            except Exception as e:
                                s.rollback()
                                st.error(f"Deletion failed: {e}")
                            finally:
                                s.close()
                            st.session_state.pop(f"confirm_delete_{user['id']}", None)
                            st.rerun()
                    with c2:
                        if st.button("Cancel", key=f"confirm_no_{user['id']}", use_container_width=True):
                            st.session_state.pop(f"confirm_delete_{user['id']}", None)
                            st.rerun()

            st.divider()


# ─── TAB 2: Role Management ──────────────────────────────────────────────────
with tab_roles:
    st.markdown("### Manage Roles")
    st.caption("Create new roles or delete custom ones. System roles (Admin, Recruiter, Hiring Manager) cannot be deleted.")

    # ── Create New Role Form ──
    with st.expander("➕ Create a New Role", expanded=False):
        new_role_name = st.text_input("Role Name", placeholder="e.g. Talent Sourcer", key="new_role_name")
        new_role_desc = st.text_area("Description", placeholder="Brief description of what this role can do", key="new_role_desc", height=80)

        if st.button("Create Role", type="primary", key="create_role_btn"):
            name_clean = new_role_name.strip()
            if not name_clean:
                st.error("Role name cannot be empty.")
            elif name_clean.lower() in [r["name"].lower() for r in roles_data]:
                st.error(f"A role named '{name_clean}' already exists.")
            else:
                s = open_session()
                try:
                    new_r = Role(name=name_clean, description=new_role_desc.strip(), is_system=False)
                    s.add(new_r)
                    s.commit()
                    st.success(f"✅ Role **{name_clean}** created. Assign permissions in the Permission Matrix tab.")
                    st.rerun()
                except Exception as e:
                    s.rollback()
                    st.error(f"Failed: {e}")
                finally:
                    s.close()

    st.divider()

    # ── Existing Roles List ──
    for role in roles_data:
        col_name, col_desc, col_users, col_action = st.columns([1.5, 3, 1, 1])

        with col_name:
            badge = f"<span class='system-badge'>SYSTEM</span>" if role["is_system"] else ""
            st.markdown(f"**{role['name']}** {badge}", unsafe_allow_html=True)

        with col_desc:
            st.caption(role["description"] or "No description")

        with col_users:
            st.metric("Users", role["user_count"])

        with col_action:
            if role["is_system"]:
                st.caption("🔒 Protected")
            elif role["user_count"] > 0:
                st.caption("⚠️ Has users")
                if st.button("Force Delete", key=f"del_role_{role['id']}", type="secondary"):
                    st.session_state[f"confirm_del_role_{role['id']}"] = True
            else:
                if st.button("❌ Delete", key=f"del_role_{role['id']}"):
                    s = open_session()
                    try:
                        target = s.query(Role).filter_by(id=role["id"]).first()
                        if target and not target.is_system:
                            s.delete(target)
                            s.commit()
                            st.success(f"Role **{role['name']}** deleted.")
                            st.rerun()
                    except Exception as e:
                        s.rollback()
                        st.error(f"Failed: {e}")
                    finally:
                        s.close()

        # Confirm force-delete for roles with users
        if st.session_state.get(f"confirm_del_role_{role['id']}", False):
            st.warning(f"⚠️ **{role['name']}** has {role['user_count']} assigned user(s). Deleting it will set their role to NULL.")
            c1, c2, _ = st.columns([1.2, 1, 4])
            with c1:
                if st.button("Confirm Delete", key=f"force_del_yes_{role['id']}", type="primary"):
                    s = open_session()
                    try:
                        target = s.query(Role).filter_by(id=role["id"]).first()
                        if target and not target.is_system:
                            s.delete(target)
                            s.commit()
                            st.success(f"Role **{role['name']}** deleted.")
                    except Exception as e:
                        s.rollback()
                        st.error(f"Failed: {e}")
                    finally:
                        s.close()
                    st.session_state.pop(f"confirm_del_role_{role['id']}", None)
                    st.rerun()
            with c2:
                if st.button("Cancel", key=f"force_del_no_{role['id']}"):
                    st.session_state.pop(f"confirm_del_role_{role['id']}", None)
                    st.rerun()

        st.divider()


# ─── TAB 3: Permission Matrix ────────────────────────────────────────────────
with tab_perms:
    st.markdown("### Permission Matrix")
    st.caption("Toggle which permissions each role holds. Changes are saved when you click **Save Changes** at the bottom.")

    if not roles_data or not perms_data:
        st.warning("No roles or permissions found. Run `seed_rbac.py` first.")
    else:
        # Group permissions by category for visual organisation
        categories = {}
        for p in perms_data:
            categories.setdefault(p["category"], []).append(p)

        # Build a dict to track checkbox state:  key = (role_name, perm_name) -> bool
        matrix_key = "perm_matrix_state"
        if matrix_key not in st.session_state:
            st.session_state[matrix_key] = {}
            for role in roles_data:
                for perm in perms_data:
                    st.session_state[matrix_key][(role["name"], perm["name"])] = perm["name"] in role["perm_names"]

        # Render the grid
        # Header row: first column for permission name, then one column per role
        num_roles = len(roles_data)
        header_widths = [3] + [1.2] * num_roles
        header_cols = st.columns(header_widths)
        header_cols[0].markdown("**Permission**")
        for i, role in enumerate(roles_data):
            header_cols[i + 1].markdown(f"**{role['name']}**")
        st.divider()

        for cat_name, cat_perms in categories.items():
            st.markdown(f"##### {cat_name}")
            for perm in cat_perms:
                row_cols = st.columns(header_widths)
                row_cols[0].markdown(f"{perm['display_name']}")
                row_cols[0].caption(f"`{perm['name']}`")
                for i, role in enumerate(roles_data):
                    cb_key = f"cb_{role['name']}_{perm['name']}"

                    # Protect Admin's manage_rbac permission from being unchecked
                    is_protected = (role["name"] == "Admin" and perm["name"] == "manage_rbac")
                    current_val = st.session_state[matrix_key].get((role["name"], perm["name"]), False)

                    with row_cols[i + 1]:
                        if is_protected:
                            st.checkbox(
                                "✓", value=True, key=cb_key,
                                disabled=True, label_visibility="collapsed",
                                help="Admin must always retain manage_rbac"
                            )
                        else:
                            new_val = st.checkbox(
                                "✓", value=current_val, key=cb_key,
                                label_visibility="collapsed",
                            )
                            st.session_state[matrix_key][(role["name"], perm["name"])] = new_val
            st.divider()

        # ── Save Button ──
        if st.button("💾 Save Changes", type="primary", use_container_width=True, key="save_perm_matrix"):
            s = open_session()
            try:
                db_roles = {r.name: r for r in s.query(Role).all()}
                db_perms = {p.name: p for p in s.query(Permission).all()}

                for role_name, role_obj in db_roles.items():
                    desired_perms = set()
                    for perm_name in db_perms:
                        if st.session_state[matrix_key].get((role_name, perm_name), False):
                            desired_perms.add(perm_name)

                    # Enforce: Admin always keeps manage_rbac
                    if role_name == "Admin":
                        desired_perms.add("manage_rbac")

                    # Sync: set permissions to exactly the desired set
                    role_obj.permissions = [db_perms[pn] for pn in desired_perms if pn in db_perms]

                s.commit()
                st.success("✅ Permission matrix saved successfully.")
                # Clear the cached matrix so it reloads fresh
                st.session_state.pop(matrix_key, None)
                st.rerun()
            except Exception as e:
                s.rollback()
                st.error(f"Save failed: {e}")
            finally:
                s.close()


# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center; margin-top:20px; font-size:0.78rem; color:#a08060;">
    🛡️ All deletions are permanent and cannot be reversed.<br>
    Role & permission changes take effect on the user's next page load.
</div>
""", unsafe_allow_html=True)

# Render hidden logout button at the absolute bottom
import utils
utils.render_hidden_logout_button()
