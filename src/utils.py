# This file is for defining global CSS elements that will apply application wide
# Example: Sidebar formatting that i need done on all pages and shown at all times

import streamlit as st

def require_login():
    import streamlit as st
    if not st.session_state.get("auth_verified", False):
        # User has navigated directly to a page without going through
        # the login gate in app.py — send them back.
        st.switch_page("app.py")
        st.stop()
    else:
        render_sidebar_profile()

def has_role(allowed_roles: list) -> bool:
    import streamlit as st
    user_email = getattr(st.user, "email", "")
    DEVELOPER_EMAIL = st.secrets.get("admin", {}).get("developer_email", "")
    user_role = st.session_state.get("current_user_role", "Hiring Manager")

    # Developer email or Admin role always possesses unrestricted access
    if user_email == DEVELOPER_EMAIL or user_role == "Admin":
        return True
    
    return user_role in allowed_roles

def enforce_role(allowed_roles: list, page_name: str = "this feature"):
    import streamlit as st
    if not has_role(allowed_roles):
        inject_global_css()
        render_sidebar_profile()
        user_role = st.session_state.get("current_user_role", "Hiring Manager")
        allowed_str = ", ".join(allowed_roles)
        st.markdown(f"""
        <div style="background: #FFFDF7; border: 2px solid #690e0e; border-radius: 14px; padding: 36px 30px; margin-top: 40px; text-align: center; box-shadow: 0 4px 20px rgba(105,14,14,0.15);">
            <div style="font-size: 2.8rem; margin-bottom: 10px;">🔒</div>
            <h2 style="color: #690e0e; margin-bottom: 12px; font-weight: 800;">Access Restricted</h2>
            <p style="font-size: 1.05rem; color: #2A1407; line-height: 1.6; max-width: 600px; margin: 0 auto 20px auto;">
                You are currently signed in as <strong>{st.session_state.get("current_user_name", "User")}</strong> with the role <span style="background:#690e0e; color:#F5EAD0; padding:2px 8px; border-radius:10px; font-size:0.82rem; font-weight:700; text-transform:uppercase;">{user_role}</span>.
            </p>
            <p style="font-size: 0.95rem; color: #7a5c3a; line-height: 1.5; max-width: 550px; margin: 0 auto;">
                <em>{page_name}</em> is reserved for <strong>{allowed_str}</strong> or <strong>Admin</strong> users.
            </p>
            <hr style="border: none; border-top: 1px solid #E5D0A0; margin: 25px auto; width: 60%;">
            <p style="font-size: 0.84rem; color: #888;">
                Need access? Please contact your platform administrator to update your role.
            </p>
        </div>
        """, unsafe_allow_html=True)
        render_hidden_logout_button()
        st.stop()

def render_sidebar_profile():
    import streamlit as st
    import streamlit.components.v1 as components
    from database import open_session, User

    user_email  = st.user.email
    user_name   = st.user.name or user_email.split("@")[0]
    initials    = "".join(w[0] for w in user_name.split()[:2]).upper()

    # Query role from DB
    session = open_session()
    role = "Recruiter"
    try:
        u = session.query(User).filter_by(email=user_email).first()
        if u:
            role = u.role
        else:
            DEVELOPER_EMAIL = st.secrets.get("admin", {}).get("developer_email", "")
            assigned_role = "Admin" if user_email == DEVELOPER_EMAIL else "Recruiter"
            u = User(email=user_email, name=user_name, role=assigned_role)
            session.add(u)
            session.commit()
            session.refresh(u)
            role = u.role
    except Exception:
        pass
    finally:
        session.close()

    # ── CSS for avatar + dropdown (injected via st.markdown, no scripts needed) ─
    # NOTE: st.markdown() strips <script> tags, so only CSS goes here.
    st.markdown("""
<style>
#ha-avatar-btn {
    position: fixed; top: 10px; right: 160px; z-index: 999999;
    width: 36px; height: 36px; border-radius: 50%;
    background: linear-gradient(135deg, #690e0e, #3d0808);
    color: #F5EAD0; font-size: 0.78rem; font-weight: 800;
    font-family: 'Inter', sans-serif; letter-spacing: 0.03em;
    display: flex; align-items: center; justify-content: center;
    cursor: pointer; border: 2px solid #C8A96E;
    box-shadow: 0 2px 8px rgba(105,14,14,0.25);
    transition: box-shadow 0.2s, transform 0.15s; user-select: none;
}
#ha-avatar-btn:hover {
    box-shadow: 0 4px 16px rgba(105,14,14,0.40); transform: scale(1.07);
}
#ha-profile-dropdown {
    position: fixed; top: 54px; right: 110px; z-index: 999998;
    width: 230px; background: #FFFDF7; border: 1.5px solid #C8A96E;
    border-radius: 14px; box-shadow: 0 8px 32px rgba(105,14,14,0.15);
    padding: 0; overflow: hidden; display: none;
    font-family: 'Inter', sans-serif;
}
#ha-profile-dropdown.open { display: block; animation: ha-drop-in 0.15s ease; }
@keyframes ha-drop-in {
    from { opacity: 0; transform: translateY(-6px); }
    to   { opacity: 1; transform: translateY(0); }
}
.ha-menu-header {
    padding: 16px 16px 12px 16px; background: #F5EAD0;
    border-bottom: 1px solid #E5D0A0;
}
.ha-menu-name {
    font-size: 0.95rem; font-weight: 700; color: #2A1407;
    margin-bottom: 2px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.ha-menu-role {
    display: inline-block; background: #690e0e; color: #F5EAD0;
    font-size: 0.68rem; font-weight: 700; letter-spacing: 0.08em;
    text-transform: uppercase; padding: 2px 8px; border-radius: 10px; margin-bottom: 4px;
}
.ha-menu-email {
    font-size: 0.75rem; color: #7a5c3a;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.ha-menu-divider { border: none; border-top: 1px solid #E5D0A0; margin: 0; }
.ha-logout-item {
    padding: 12px 16px; font-size: 0.88rem; font-weight: 600; color: #690e0e;
    cursor: pointer; display: flex; align-items: center; gap: 8px; transition: background 0.15s;
}
.ha-logout-item:hover { background: #F5EAD0; }
</style>
""", unsafe_allow_html=True)


    # ── JS injection via components.v1.html ─────────────────────────────────────
    # KEY REASON: st.markdown() silently strips ALL <script> tags for security.
    # components.v1.html() renders inside a sandboxed iframe where JS DOES execute,
    # and window.parent.document lets us reach into the real Streamlit page to
    # inject the avatar div + dropdown, and to click the hidden sidebar button.
    components.html(f"""
<!DOCTYPE html>
<html>
<head><style>body{{margin:0;padding:0;overflow:hidden;}}</style></head>
<body>
<script>
(function() {{
    var pDoc = window.parent.document;

    // Remove stale elements from previous Streamlit re-renders
    ['ha-avatar-btn', 'ha-profile-dropdown'].forEach(function(id) {{
        var el = pDoc.getElementById(id);
        if (el) el.remove();
    }});

    // Build and inject avatar circle into parent page
    var avatar = pDoc.createElement('div');
    avatar.id = 'ha-avatar-btn';
    avatar.textContent = '{initials}';
    pDoc.body.appendChild(avatar);

    // Build and inject dropdown card into parent page
    var dropdown = pDoc.createElement('div');
    dropdown.id = 'ha-profile-dropdown';
    dropdown.innerHTML =
        '<div class="ha-menu-header">' +
            '<div class="ha-menu-name">{user_name}</div>' +
            '<div class="ha-menu-role">{role}</div><br>' +
            '<div class="ha-menu-email">{user_email}</div>' +
        '</div>' +
        '<hr class="ha-menu-divider">' +
        '<div class="ha-logout-item" id="ha-signout-item">\u2192 Sign out</div>';
    pDoc.body.appendChild(dropdown);

    // Toggle dropdown on avatar click
    avatar.addEventListener('click', function(e) {{
        e.stopPropagation();
        dropdown.classList.toggle('open');
    }});

    // Close dropdown on any outside click
    pDoc.addEventListener('click', function(e) {{
        if (!dropdown.contains(e.target) && !avatar.contains(e.target)) {{
            dropdown.classList.remove('open');
        }}
    }});

    // Sign out: find the hidden Streamlit button and click it
    pDoc.getElementById('ha-signout-item').addEventListener('click', function() {{
        var btns = pDoc.querySelectorAll('button');
        for (var i = 0 ; i < btns.length; i++){{
            if(btns[i].innerText.trim() === 'ha_logout__'){{
                btns[i].click();
                return;
            }}
        }}
    }});
    
    // Shrink the raw sidebar button to zero size (keep it in DOM but invisible)
    function hideRawBtn() {{
        var btns = pDoc.querySelectorAll('button');
        for (var i = 0; i < btns.length; i++) {{
            if (btns[i].innerText.trim() === 'ha_logout__') {{
                var b = btns[i];
                
                // Target the Streamlit wrapper container to kill the empty gap and push it down
                var container = b.closest('div[data-testid="element-container"]');
                if (container) {{
                    container.style.cssText = 'height:0!important; margin:0!important; padding:0!important; overflow:hidden!important; order:9999!important;';
                }}
                
                b.style.cssText =
                    'height:0!important;min-height:0!important;' +
                    'padding:0!important;margin:0!important;border:none!important;' +
                    'overflow:hidden!important;opacity:0!important;pointer-events:none!important;';
                return;
            }}
        }}
        setTimeout(hideRawBtn, 150);  // retry until Streamlit finishes rendering
    }}

    hideRawBtn();
}})();
</script>
</body>
</html>
""", height=0)


# Making a function that can be called to just inject global CSS
def inject_global_css():
    import streamlit as st

    # Check if the current user is an Admin (either via role or developer email)
    is_admin = has_role(["Admin"])

    # If they are NOT an admin, hide the Admin Panel link from the sidebar nav
    hide_admin_css = ""
    if not is_admin:
        hide_admin_css = """
        /* Hide the 0_Admin_Panel link (2nd item in sidebar nav) */
        div[data-testid="stSidebarNav"] ul li:nth-child(2) {
            display: none !important;
        }
        """

    st.markdown(f"""
    <style>
        /* Step 1: Hide the default "app" label in the sidebar nav */
        div[data-testid="stSidebarNav"] ul li:nth-child(1) span {{
            display: none !important;
        }}

        /* Step 2: Replace it with "Home Page" */
        div[data-testid="stSidebarNav"] ul li:nth-child(1) a::after {{
            content: "Home Page";
            display: block;
            font-weight: bold;
            color: inherit;
        }}

        {hide_admin_css}

    </style>
    """, unsafe_allow_html=True)

def enforce_edge_to_edge_layout():
    import streamlit as st
    st.markdown("""
        <style>
        .block-container {
            padding-top: 1rem !important;
            padding-left: 1rem !important;
            padding-right: 1rem !important;
            padding-bottom: 0rem !important;
            max-width: 100% !important;
        }
        </style>
    """, unsafe_allow_html=True)

def render_hidden_logout_button():
    """
    Renders the hidden 'ha_logout__' button triggered by JS.
    This should be called at the VERY BOTTOM of every page file 
    so that its hidden container renders at the end of the sidebar
    without leaving an ugly empty space at the top.
    """
    import streamlit as st
    if st.sidebar.button("ha_logout__", key="global_logout_btn"):
        st.session_state.clear()
        st.logout()
