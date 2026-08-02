"""
seed_rbac.py — One-time migration & seed script for dynamic RBAC
=================================================================
Run this ONCE after deploying the new database.py schema.
It will:
  1. Create the new tables (roles, permissions, role_permissions) if missing.
  2. Add the `role_id` column to the existing `users` table if missing.
  3. Seed the three default system roles and all permissions.
  4. Wire up the default permission mappings.
  5. Migrate every existing user from their legacy string `role` to the new FK `role_id`.

Usage:
    python src/seed_rbac.py
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import inspect, text
from database import (
    engine, Base, SessionLocal,
    Role, Permission, role_permissions, User,
)

# ── 1. Create any new tables that don't exist yet ─────────────────────────────
Base.metadata.create_all(bind=engine)
print("[✓] Tables created / verified.")

# ---- 1.5 Securing the database by enabling RSL

# this is to block public SUpabase API (PostgREST) from reading/editing tables
#the python backend is already handling functionality so it is not needed anyway
with engine.begin() as conn:
    tables =[
        "roles", "permissions", "role_permissions",
        "users", "job_posts", "candidates", "candidate_comments"
    ]

    for table in tables:
        conn.execute(text(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;"))
        
    print("[✓] Row Level Security enabled for all tables.")


# ── 2. Add role_id column to users if it doesn't exist (ALTER TABLE) ──────────
inspector = inspect(engine)
user_columns = [c["name"] for c in inspector.get_columns("users")]
if "role_id" not in user_columns:
    with engine.begin() as conn:
        conn.execute(text(
            "ALTER TABLE users ADD COLUMN role_id INTEGER REFERENCES roles(id) ON DELETE SET NULL"
        ))
    print("[✓] Added role_id column to users table.")
else:
    print("[·] role_id column already exists on users table — skipping.")

# ── 3. Seed default permissions ───────────────────────────────────────────────
DEFAULT_PERMISSIONS = [
    # (name,                     display_name,                      category)
    ("create_job_posts",         "Create Job Workspaces",           "Workspace Management"),
    ("edit_job_posts",           "Edit / Delete Job Workspaces",    "Workspace Management"),
    ("upload_resumes",           "Upload Candidate Resumes",        "Data Ingestion"),
    ("trigger_parsing",          "Run LLM Parser",                  "Data Ingestion"),
    ("view_candidate_profiles",  "View Candidate Profiles",         "Evaluation & Review"),
    ("shortlist_candidates",     "Toggle Candidate Shortlist",      "Evaluation & Review"),
    ("add_remarks",              "Add Evaluation Remarks / Logs",   "Evaluation & Review"),
    ("view_remarks",             "View Remarks / Logs Feed",        "Evaluation & Review"),
    ("access_admin_panel",       "View Admin User Directory",       "System Administration"),
    ("manage_rbac",              "Manage Roles & Permissions",      "System Administration"),
]

session = SessionLocal()

try:
    perm_map = {}  # name -> Permission object
    for name, display, category in DEFAULT_PERMISSIONS:
        existing = session.query(Permission).filter_by(name=name).first()
        if not existing:
            existing = Permission(name=name, display_name=display, category=category)
            session.add(existing)
            session.flush()
            print(f"  [+] Permission: {name}")
        else:
            print(f"  [·] Permission already exists: {name}")
        perm_map[name] = existing

    session.commit()
    print(f"[✓] {len(perm_map)} permissions seeded.")

    # ── 4. Seed default roles & their permission mappings ─────────────────────
    DEFAULT_ROLES = {
        "Admin": {
            "description": "Full platform access including role and permission management.",
            "is_system": True,
            "permissions": list(perm_map.keys()),  # ALL permissions
        },
        "Recruiter": {
            "description": "Can create job posts, upload & parse resumes, score and review candidates.",
            "is_system": True,
            "permissions": [
                "create_job_posts", "edit_job_posts",
                "upload_resumes", "trigger_parsing",
                "view_candidate_profiles", "shortlist_candidates",
                "add_remarks", "view_remarks",
            ],
        },
        "Hiring Manager": {
            "description": "Read-only reviewer who can view profiles, shortlist, and leave remarks.",
            "is_system": True,
            "permissions": [
                "view_candidate_profiles", "shortlist_candidates",
                "add_remarks", "view_remarks",
            ],
        },
    }

    role_map = {}  # name -> Role object
    for role_name, cfg in DEFAULT_ROLES.items():
        existing = session.query(Role).filter_by(name=role_name).first()
        if not existing:
            existing = Role(
                name=role_name,
                description=cfg["description"],
                is_system=cfg["is_system"],
            )
            session.add(existing)
            session.flush()
            print(f"  [+] Role: {role_name}")
        else:
            print(f"  [·] Role already exists: {role_name}")

        # Sync permissions for this role (add any missing, keep existing)
        current_perm_names = {p.name for p in existing.permissions}
        for perm_name in cfg["permissions"]:
            if perm_name not in current_perm_names:
                existing.permissions.append(perm_map[perm_name])
        role_map[role_name] = existing

    session.commit()
    print(f"[✓] {len(role_map)} roles seeded with permission mappings.")

    # ── 5. Migrate existing users ─────────────────────────────────────────────
    users_without_role_id = session.query(User).filter(User.role_id.is_(None)).all()
    migrated = 0
    for u in users_without_role_id:
        legacy = (u.role or "").strip()
        matched_role = role_map.get(legacy)
        if not matched_role:
            # Default unmapped users to Hiring Manager (read-only)
            matched_role = role_map.get("Hiring Manager")
            print(f"  [!] User '{u.email}' had unknown role '{legacy}' → mapped to Hiring Manager")
        u.role_id = matched_role.id
        migrated += 1

    session.commit()
    print(f"[✓] Migrated {migrated} user(s) from legacy role string to role_id FK.")

    print("\n══════════════════════════════════════")
    print("  RBAC seed complete. All systems go.")
    print("══════════════════════════════════════")

except Exception as e:
    session.rollback()
    print(f"[✗] Seed failed: {e}")
    raise
finally:
    session.close()
