# Before Evalutaion Button

Pre evaluation paramter setting done by recruiter

1. Option to add/remove **Evaluation Factors(This will be in the sidebar for now)**
2. Allow recuiter to ALSO select the Eval Factor threshold for recommendations. **(Make the option be applicable on each eval factor)**
   Eg.If more than 3 Eval Factors hit 50% or more, recommend the candidate to be shotrlosted **(recommend)**
3. Evaluation Summary downloadable as pdf
   1. Should include **candidate Name, Contact Info, the Position they are evaluated FOR**
4. Above all features to be on a sidebar on the left, it stays always

# Re-Structured Scoring System

## Level 1: Simple Keyword Matching

Suppose the JD says:

```text
Required Skills:
Python
SQL
Machine Learning
TensorFlow
```

Resume JSON:

```json
{
  "skills": [
    "Python",
    "SQL",
    "Docker"
  ]
}
```

Python can do:

```python
required = [
    "Python",
    "SQL",
    "Machine Learning",
    "TensorFlow"
]

candidate = [
    "Python",
    "SQL",
    "Docker"
]

matches = len(set(required) & set(candidate))

score = (matches / len(required)) * 100
```

Result:

```text
2 / 4 = 50%
```

## Level 2: Weighted Skills

Recruiters don't value all skills equally.

Example:

```text
Python = Critical
SQL = Critical
TensorFlow = Important
Docker = Nice to have
```

Weights:

```python
weights = {
    "Python": 30,
    "SQL": 30,
    "TensorFlow": 20,
    "Docker": 10,
    "AWS": 10
}
```

Candidate:

```python
candidate = [
    "Python",
    "SQL",
    "Docker"
]
```

Score:

```python
score = 0

for skill in candidate:
    if skill in weights:
        score += weights[skill]
```

Result:

```text
Python     30
SQL        30
Docker     10

Total = 70
```

Now the score reflects importance.

---

# Level 3: Experience Scoring

JD:

```text
Experience Required:
3 years
```

Resume:

```json
{
  "experience_years": 2
}
```

Python:

```python
required = 3
actual = 2

score = min(actual / required, 1.0) * 100
```

Result:

```text
66.7
```

If candidate has:

```text
5 years
```

Score:

```text
100
```

(capped at 100)

---

# Level 4: Project Relevance

This is where LLM extraction helps.

Suppose the model extracts:

```json
{
  "projects": [
    "Fraud Detection using Machine Learning",
    "Image Classification using CNN"
  ]
}
```

JD:

```text
Looking for ML Engineer
```

Python can check:

```python
ml_keywords = [
    "machine learning",
    "cnn",
    "tensorflow",
    "classification",
    "prediction"
]
```

Count matches.

More matches = higher score.

---

# Level 5: Semantic Matching (Best)

This is where modern ATS systems become powerful.

Instead of matching words:

```text
Machine Learning
```

against:

```text
Machine Learning
```

you compare meanings.

Example:

JD:

```text
Machine Learning
```

Resume:

```text
Built predictive models using
scikit-learn and PyTorch.
```

No exact match.

But same meaning.

---

You generate embeddings.

Think of embeddings as coordinates.

```text
Python
    ↓
[0.23, 0.11, 0.88...]

TensorFlow
    ↓
[0.27, 0.15, 0.81...]
```

Similar concepts end up near each other.

Then:

```python
similarity = cosine_similarity(
    jd_embedding,
    resume_embedding
)
```

Result:

```text
0.92
```

which means:

```text
92% semantic similarity
```

This is much smarter than keyword matching.

---

# How actual ATS systems score

Most use something like:

```text
Overall Score

=
40% Skills Match
+
25% Experience Match
+
15% Education Match
+
10% Project Match
+
10% Certifications
```

Example:

| Category       | Score |
| -------------- | ----- |
| Skills         | 85    |
| Experience     | 70    |
| Education      | 90    |
| Projects       | 80    |
| Certifications | 50    |

Final:

```text
0.40 × 85 = 34

0.25 × 70 = 17.5

0.15 × 90 = 13.5

0.10 × 80 = 8

0.10 × 50 = 5

----------------

78.0
```

Final score:

```text
78/100
```

---

# What I would do in your project

Since you're already using an LLM:

### Step 1

Use Qwen/Gemini to extract:

```json
{
  "skills": [...],
  "experience_years": 2.5,
  "projects": [...],
  "education": "...",
  "certifications": [...]
}
```

---

### Step 2

Use the LLM once on the JD:

```text
Extract:
- Required skills
- Preferred skills
- Minimum experience
- Education requirements
```

Return:

```json
{
  "required_skills": [...],
  "preferred_skills": [...],
  "min_experience": 3
}
```

---

### Step 3

Python scores objectively:

```text
Skill Score
Experience Score
Education Score
Project Score
Certification Score
```

---

### Step 4

Combine them using weights.

---

### Step 5 (Optional but powerful)

Send the final scored profile to Gemini/Qwen:

```text
Candidate Score = 78

Explain strengths and weaknesses.
```

Now the LLM is acting like a recruiter, while Python acts like a calculator.

That's a very strong architecture because:

* Scores are reproducible.
* Rankings are consistent.
* The AI still provides human-readable reasoning.
* You avoid letting the LLM randomly invent scores.
