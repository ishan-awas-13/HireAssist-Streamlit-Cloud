# Phase 2: Recruiter Workflow & Tracking Plan (Revised)
> **Enterprise Resume Parser — Development Roadmap**  
> Revised July 10, 2026 · Based on mentor meeting notes + user feedback comments

---

## What Changed from v1

| Topic | Original Plan | Revised Plan |
|---|---|---|
| Leaderboard | New separate tab | Sort candidates **in-place** inside existing Scores tab |
| Expander header | Shows filename | Shows **name + contact + email + filename** |
| Notes placement | Sidebar | **Beside the eval factor results** in main content |
| Notes + Timeline | Two separate features | **One merged hybrid feature** |
| LinkedIn | Proxycurl API ($) | **On hold** — finding free alternative first |

---

## Milestone 1 — Fix: JD Update Bug on Workspace Switch

> **Priority: 🔴 Critical — Do this first**

**The Problem:**
The Job Description text area on Page 3 stays stuck with the old workspace's JD when the recruiter switches workspaces from the dropdown. The same root cause as the `ed_factors` bug we already fixed.

**How to fix it:**
When `workspace_changed` is detected, also clear the `ed_job_description` key from `session_state` before the rerun.

```python
if workspace_changed:
    st.session_state.ed_factors = saved_factors
    # Also clear the JD widget so it reloads fresh from DB
    if "ed_job_description" in st.session_state:
        del st.session_state["ed_job_description"]
    st.rerun()
```

**Files to touch:**
- `src/pages/3_Evaluation_Dashboard.py` — inside the `if workspace_changed:` block

**Effort:** ~20 minutes.

---

## Milestone 2 — Upgrade: Sorted Results + Rich Candidate Header Band

> **Priority: 🟠 High**

**What it is:**
Inside the existing **Scores & Evaluation tab** (Tab 3), after scoring is triggered, candidates are currently displayed in upload order with just the filename in the expander header.

Two changes:
1. **Sort candidates by `overall_score` descending** — highest scoring candidate appears first. The recruiter instantly sees the ranked order.
2. **Replace the filename-only header band** with a rich info band showing: `Rank · Name · Email · Phone · Filename · Score`

**What it looks like:**
```
▼  #1 · John Doe · john@gmail.com · +91 9876543210 · john_resume.pdf · 87%
▼  #2 · Priya Sharma · priya@email.com · +91 9123456789 · priya_cv.pdf · 74%
```

**How it works technically:**
After scoring is done, before rendering the expanders, sort the `candidates_data` list:
```python
# Sort in-place by overall_score descending
candidates_data.sort(key=lambda x: x.get("overall_score") or 0, reverse=True)
```

Then when building the expander label, pull name/contact from `profile_json`:
```python
personal = cd.get("profile_json", {}).get("personal_info", {})
name     = personal.get("name", "Unknown")
email    = personal.get("email", "—")
phone    = personal.get("phone", "—")
rank     = idx + 1
score    = cd.get("overall_score")
label    = f"#{rank} · {name} · {email} · {phone} · {cd['filename']} · {score}%"
```

> ⚠️ We will refine the exact formatting of the header band later — this is the structural plumbing. Visual polish comes after.

**Files to touch:**
- `src/pages/3_Evaluation_Dashboard.py` — inside `with tab_scored:`, sorting + expander label update

**Effort:** ~1.5 hours

---

## Milestone 3 — Feature: Recruiter Notes & Activity Timeline (Merged Hybrid)

> **Priority: 🟠 High**  
> **Merged from:** original M3 (Notes) + M4 (Timeline)

### The Vision
Rather than two separate features, this is one unified recruiter control panel per candidate. After a recruiter evaluates a candidate via the scoring panel, they need a place to:
- Set **where the candidate stands** in the recruitment pipeline
- Write **what action they just took** or plan to take
- See a **running history** of all past actions and notes in a chronological feed

This entire experience lives **beside the evaluation factor results** inside each candidate's expander card, not in the sidebar.

---

### Layout Concept (Inside Each Candidate Expander)

The expander will be split into two columns:

**Left column** — Evaluation Factor Score Results (already exists, just relocated slightly)  
**Right column** — Recruiter Tracking Panel (new)

The right column contains:
```
┌─────────────────────────────────────┐
│  Recruitment Stage                  │
│  [Dropdown: Screening ▼]            │
│                                     │
│  Add a note...                      │
│  [Text area                       ] │
│  [Log Entry →]                      │
│─────────────────────────────────────│
│  Activity History                   │
│                                     │
│  ▌ Jul 10 · 7:30 PM               │
│  ▌ Status → Interview Scheduled    │
│  ▌ "Called. Very promising."        │
│                                     │
│  ▌ Jul 9 · 11:00 AM               │
│  ▌ Status → Contacted              │
│  ▌ "Sent email. Awaiting reply."    │
└─────────────────────────────────────┘
```

Each log entry is a **blue left-bordered card** (the "blue box" from your notes). The stage dropdown and the note textarea are the write interface. Clicking "Log Entry" commits a new entry to the database and adds it to the history instantly.

---

### Database Changes Required

**In `src/database.py`:**

**Change 1:** Add two columns to the `Candidate` model:
```python
recruitment_status = Column(String(64), nullable=True, default="Screening")
```
*(We store status on the candidate row for fast querying)*

**Change 2:** Add a new `CandidateLog` table:
```python
class CandidateLog(Base):
    __tablename__ = "candidate_logs"
    id           = Column(Integer, primary_key=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"))
    timestamp    = Column(DateTime, default=datetime.utcnow)
    stage        = Column(String(64))   # The status at time of entry
    note         = Column(Text, nullable=True)

    candidate = relationship("Candidate", back_populates="logs")
```

**Change 3:** Add `logs` relationship to `Candidate` model:
```python
logs = relationship("CandidateLog", back_populates="candidate", 
                    order_by="CandidateLog.timestamp.desc()", cascade="all, delete-orphan")
```

> **Database migration:** Since tables already exist, run these two SQL statements manually once:
> ```sql
> ALTER TABLE candidates ADD COLUMN recruitment_status VARCHAR(64) DEFAULT 'Screening';
> CREATE TABLE candidate_logs (id SERIAL PRIMARY KEY, candidate_id INT REFERENCES candidates(id) ON DELETE CASCADE, timestamp TIMESTAMP DEFAULT NOW(), stage VARCHAR(64), note TEXT);
> ```

---

### Files to Touch

- `src/database.py` — add `recruitment_status` column + `CandidateLog` model
- `src/pages/3_Evaluation_Dashboard.py` — add the two-column layout + log write/read UI inside each scored candidate expander

**Effort:** ~5 hours (DB migration + two-column layout + write + read + styling)

---

## Milestone 4 — LinkedIn Enrichment (On Hold)

> **Status: ⏸️ Deferred**

Proxycurl and similar tools require a paid API key which is not acceptable for the current stage.

**Free alternatives to evaluate when resuming this:**
- **RapidAPI's LinkedIn scraper endpoints** — some have free tiers (100 calls/month)
- **Manual URL fallback** — recruiter pastes LinkedIn URL, app fetches publicly visible data from the HTML (fragile but free)
- **Candidate self-submission** — add a field in the app where a candidate manually submits their LinkedIn URL alongside resume

Will revisit once a cost-free path is confirmed.

---

## Revised Implementation Order

| # | Milestone | Priority | Effort |
|---|-----------|----------|--------|
| 1 | JD Update Bugfix | 🔴 Critical | 20 min |
| 2 | Sorted Results + Rich Header Band | 🟠 High | 1.5 hrs |
| 3 | Recruiter Notes + Timeline (merged) | 🟠 High | 5 hrs |
| 4 | LinkedIn Enrichment | ⏸️ On Hold | TBD |

**Total active estimate: ~7 hours of focused implementation.**

---

## Finalized Decisions ✅

| Question | Decision |
|---|---|
| **Recruitment Stage input** | **Free text field** — the recruiter types their own stage name. Real-world pipelines vary too much to restrict to a fixed dropdown. No predefined options. |
| **Timeline scope** | **Recruiter-only entries.** No system auto-logging. This feature is a smart, contextual Notes section for the recruiter to maintain their own context and tracking of each candidate. Nothing is written without the recruiter explicitly doing it. |
| **Notes panel visibility** | **After scoring only.** The Recruiter Tracking Panel appears inside a candidate's expander only once scoring has been run. It is not visible during raw profile review. |
