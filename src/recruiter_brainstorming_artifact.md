# Recruiter‑Centric Feature Brainstorm (Resume‑Parser)

## 1️⃣ Classification Buckets (how to group resumes)

| # | Bucket | What it tells the recruiter | Typical extraction method |
|---|--------|-----------------------------|---------------------------|
| 1 | **Seniority Level** | Junior, Mid‑level, Senior, Lead, Architect | Parse job titles, years of experience, and keywords like “intern”, “manager”, “director”. |
| 2 | **Employment Type** | Full‑time, Part‑time, Contract, Freelance, Internship | Look for contract terms, “temporary”, “seasonal”, or “Freelance” in the header or work experience. |
| 3 | **Location / Remote‑Readiness** | On‑site (city/state), Remote‑only, Hybrid | Extract explicit location fields, presence of “remote”, “work from home”, or timezone clues. |
| 4 | **Domain / Functional Area** | Front‑end, Back‑end, Data Science, DevOps, UX/UI, Product Management, QA, etc. | Map listed technologies, project descriptions, and domain‑specific buzzwords to a taxonomy. |
| 5 | **Industry Experience** | FinTech, Healthcare, E‑commerce, SaaS, Education, Gaming, etc. | Detect industry‑specific terminology, company names, or project contexts. |
| 6 | **Education Tier** | PhD, Master’s, Bachelor’s, Associate, High‑School, Bootcamp | Use degree field, major, and institution ranking (if you have a reference list). |
| 7 | **Certification Presence** | Cloud (AWS, GCP, Azure), Security (CISSP), Agile (Scrum), etc. | Scan the `certifications` array for known cert names. |
| 8 | **Language Proficiency** | Native, Fluent, Conversational, Basic | Identify language sections or keywords like “Bilingual”, “Fluent in Spanish”. |
| 9 | **Visa / Work Authorization** | Eligible to work locally, Sponsorship required | Look for “eligible to work”, “requires sponsorship”, or passport info. |
|10 | **Diversity Signals (optional)** | Veteran status, disability, gender‑neutral pronouns | Pull from voluntary self‑identification sections if present. |

---

## 2️⃣ Ranking / Scoring Features (how to order candidates)

| # | Feature | What it measures | Suggested weight* | Computation |
|---|---------|------------------|-------------------|-------------|
| 1 | **Skills Match** | Overlap between required technical/soft skills and candidate’s `skills` list | 40 % | Jaccard / cosine similarity on tokenized skill sets (apply synonyms). |
| 2 | **Role Relevance** | Alignment of candidate’s past titles/projects with target role | 25 % | Fuzzy string match + recency weighting (more recent titles get higher weight). |
| 3 | **Experience Length** | Total years of relevant work experience vs. minimum required | 20 % | Sum of `start_date`/`end_date` intervals (account for `is_current`). |
| 4 | **Education Fit** | Degree level and major relevance to role | 10 % | Map degree hierarchy to numeric score; major keyword match. |
| 5 | **Project Impact** | Presence of high‑impact projects (e.g., quantified results, leadership) | 5 % | Detect numbers (e.g., “+30%”, “saved $200k”) and leadership verbs. |

*Weights can be tuned per hiring manager or saved as a profile in the UI.

**Overall Score Formula (example):**
```
overall = round(
    0.40 * skills_match +
    0.25 * role_relevance +
    0.20 * experience_match +
    0.10 * education_match +
    0.05 * project_match
)
```

---

## 3️⃣ End‑to‑End Processing Flow (modular pipeline)

1. **Upload & Text Extraction** – `extractor.get_clean_resume_text()` → raw text.
2. **LLM Parsing** (`parser_engine.py`) – Prompt → JSON conforming to `ResumeParserResponse`.
3. **Validation** – Pydantic schema validates structure; log any failures.
4. **Feature Enrichment (Python)** – Convert dates → years of experience, tokenize skills, build flags (remote‑ready, seniority, etc.).
5. **Scoring Engine (`scorer.py`)** – Send JD + key‑skill list + candidate JSON to the LLM **only** for sub‑scores (skills, role, experience, education, project). Return those sub‑scores; **compute `overall_score` in Python** using the weighted formula above.
6. **Categorization Engine** – Apply rule‑based tags (seniority, location, industry) and optionally a lightweight classifier (e.g., scikit‑learn model trained on past hires).
7. **Persist in Session State** – Store `candidate_profile`, `scores`, and all classification tags in `st.session_state.parsed_resumes`.
8. **Dashboard UI** –
   - Filters: multi‑select for each bucket (seniority, location, remote, etc.).
   - Sortable Table: columns for overall score + each sub‑score; click header to sort.
   - Score Breakdown: expand a row to see metric cards and the LLM‑generated rationale.
   - Export: CSV/JSON download of the filtered view.
9. **Feedback Loop** – Allow the recruiter to thumbs‑up / thumbs‑down a candidate; store the feedback for future model tuning.

---

## 4️⃣ Quick Implementation Checklist

| ✅ | Item |
|----|------|
| 1 | **Add `overall_score` calculation** in `scorer.py` (post‑LLM). |
| 2 | **Parse `key_skills`** as a list (comma‑separated) before passing to the model. |
| 3 | **Create classification tags** in `app.py` (e.g., `entry["seniority"] = "Senior"`). |
| 4 | **Add filter widgets** above the results table (st.multiselect for each bucket). |
| 5 | **Render a sortable DataFrame** (`st.dataframe`) that includes `overall_score` and sub‑scores. |
| 6 | **Export button** (`st.download_button`) to dump the current view as CSV/JSON. |
| 7 | **Optional**: simple ML model (Logistic Regression) trained on historic hire data to predict “Hire Yes/No” as an extra column. |

---

## 5️⃣ What a Recruiter Would See
- **Top‑level filters** on the left (Seniority, Remote, Domain, Years of Experience).
- **Main table** sorted by “Overall Match Score”.
- **Row expanders** that show a radar chart of the five sub‑scores and the LLM’s short rationale.
- **Button** to “Export shortlist” (only the rows currently visible).
- **Feedback icons** on each candidate to improve future scoring.

---

### Next Steps for You
1. Implement the weighted overall score in `score_candidate_suitability`.
2. Add classification helpers (e.g., `detect_seniority(profile)`) and store the tags.
3. Populate the UI with filter widgets and a sortable table.

That gives you a solid feature foundation before you dive into the heavier modeling work! 
