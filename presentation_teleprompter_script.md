# [0:00 - 0:15 | ACT 1: THE HOOK]
## [ACTION: Start on Landing Page. Click "Sign in with Google"]
Recruiters often spend hours
manually scanning resumes,
risking bias and missing technical fit.
## [ACTION: Land on Home Dashboard]
This is HireAssist AI—
an enterprise-ready,
role-aware recruitment platform
designed to parse, score,
and evaluate candidates at scale.

# [0:15 - 0:35 | ARCHITECTURE OVERVIEW]
## [ACTION: Hover over Home Dashboard metrics, multi-page sidebar, and top-right user avatar dropdown]
Built with a multi-page architecture,
HireAssist AI combines Google OAuth security,
PostgreSQL persistence,
and serverless LLM reasoning
to give hiring teams a centralized recruitment workspace.

# [0:35 - 0:55 | ACT 2: CREATING WORKSPACE]
## [ACTION: Navigate to Page 1: Job Post Creator. Type "Senior Backend Engineer", select "Full-Time", and paste sample JD]
Every hiring pipeline begins
with a dedicated workspace.
Here, a recruiter defines the role basics,
pastes the full job description,
and sets up custom evaluation criteria

# [0:55 - 1:15 | EVALUATION FACTORS]
## [ACTION: Adjust factor sliders (e.g., Skills Match ≥ 60%, Experience Match ≥ 50%). Click "Create Workspace" and point to Live Preview card]
Instead of hardcoded rules,
recruiters can define custom evaluation factors
and passing thresholds.
Submitting this writes a persistent container
directly to PostgreSQL,
keeping all future candidate submissions organized.

# [1:15 - 1:35 | ACT 3: BATCH UPLOAD]
## [ACTION: Navigate to Page 2: Data Hub. Select workspace. Drag & drop 10 dummy PDF resumes]
Moving to the Data Hub,
we select our active workspace
and drop in a batch of 10 candidate resumes
in PDF or DOCX format.

# [1:35 - 1:55 | PARSING PIPELINE]
## [ACTION: Click "Parse & Ingest All Resumes". Show progress bar and timers ticking]
(Note: Speed up this video segment 2x-3x in video editing!)
When we launch parsing,
a background execution pipeline extracts raw text
and streams it to Qwen 2.5 7B Instruct
via Hugging Face's serverless router.
The model extracts structured JSON data
validated strictly against Pydantic schemas,
saving the candidate records into the database
in real time.

# [1:55 - 2:20 | ACT 4: SKILL DETECTION]
## [ACTION: Switch to Page 3: Evaluation Dashboard. Click "Detect Mandatory Skills". Highlight the green skill badges]
Now for the core intelligence layer.
On the Evaluation Dashboard, the AI reads our job description
and automatically extracts non-negotiable mandatory skills—
filtering out "nice-to-haves"
so recruiters don't have to.

# [2:20 - 2:45 | CANDIDATE SCORING & RANKING]
## [ACTION: Click "Score All Candidates". Point to Ranked Candidates Rail on the right. Click Candidate #1, then Candidate #5]
With one click,
HireAssist AI evaluates every parsed candidate
against our job criteria.
Candidates are automatically ranked on an interactive side-rail.
The top candidate instantly shows a full score breakdown across all defined factors, along with an AI reasoning summary.

# [2:45 - 3:10 | COLLABORATION & TIMELINE]
## [ACTION: Scroll down to Recruiter Activity Timeline. Type note: "Passed technical screen, moving to round 2". Click "Add Comment"]
Recruitment is a team sport.

# [ACTION: Point to comment table update showing the user badge, role, and timestamp]
Below each profile, recruiters can leave internal note 
and track status changes in a persistent activity timeline
tagged with their authenticated name and role.

# [3:10 - 3:30 | ACT 5: OUTRO & CTA]
## [ACTION: Switch back to Home Dashboard OR show screen with GitHub repo and live Streamlit link]
From raw resumes to a structured, collaborative candidate shortlist
in under three minutes.
HireAssist AI is live on Streamlit Cloud
and fully open source on GitHub.
Thanks for watching!