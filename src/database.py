"""
database.py — SQLAlchemy engine, session factory, and ORM models.

Tables:
  - job_posts   : One record per recruiter workspace / job opening.
  - candidates  : One record per parsed resume, linked to a job_post.

Design notes:
  - JSONB is used for flexible nested data (skills, experience, scores).
  - All JSONB columns are accessed via PostgreSQL dialect; the psycopg2
    driver serialises Python dicts automatically.
  - Call `init_db()` once at app startup to create tables if they don't exist.
"""

import os
from datetime import datetime
from dotenv import load_dotenv

from sqlalchemy import (
    create_engine,
    Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

# ── Load environment ──────────────────────────────────────────────────────────
load_dotenv()

# Expected env var: DATABASE_URL=postgresql://user:password@localhost:5432/resume_parser_db
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/resume_parser_db"
)

# ── Engine & Session ──────────────────────────────────────────────────────────
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,       # detect stale connections
    pool_size=5,
    max_overflow=10,
    echo=False                # set True to debug SQL in terminal
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()


# ── ORM Models ────────────────────────────────────────────────────────────────

class JobPost(Base):
    """
    Represents a recruiter-created workspace / job opening.
    Acts as the parent container for all candidate resumes uploaded against it.
    """
    __tablename__ = "job_posts"

    id              = Column(Integer, primary_key=True, index=True)
    title           = Column(String(255), nullable=False)
    department      = Column(String(128), nullable=True)
    location        = Column(String(128), nullable=True)
    employment_type = Column(String(64), nullable=True)   # Full-time, Contract, etc.
    description     = Column(Text, nullable=True)          # Full JD text
    mandatory_skills = Column(JSONB, nullable=True)        # ["Python", "Docker", ...]
    eval_factors    = Column(JSONB, nullable=True)         # [{"name": ..., "threshold": ...}, ...]
    created_at      = Column(DateTime, default=datetime.utcnow)
    updated_at      = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active       = Column(Boolean, default=True)
    notes           = Column(Text, nullable=True)          # recruiter-internal notes

    # Relationship: one job post → many candidates
    candidates = relationship(
        "Candidate",
        back_populates="job_post",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )

    def __repr__(self):
        return f"<JobPost id={self.id} title='{self.title}'>"


class Candidate(Base):
    """
    Represents a single parsed resume submitted against a job post.
    The raw LLM output is stored in `profile_json` (JSONB).
    Scoring results are stored in `scores_json` (JSONB).
    Processing status tracks the async worker pipeline stage.
    """
    __tablename__ = "candidates"

    id              = Column(Integer, primary_key=True, index=True)
    job_post_id     = Column(Integer, ForeignKey("job_posts.id", ondelete="CASCADE"), nullable=False, index=True)
    filename        = Column(String(512), nullable=False)   # original uploaded file name
    status          = Column(String(32), default="queued")  # queued | processing | done | error
    error_message   = Column(Text, nullable=True)
    latency_seconds = Column(Float, nullable=True)          # parse latency
    profile_json    = Column(JSONB, nullable=True)          # full LLM-parsed CandidateProfile
    scores_json     = Column(JSONB, nullable=True)          # scoring output dict
    overall_score   = Column(Float, nullable=True)          # denormalised for fast sorting/filtering
    is_shortlisted  = Column(Boolean, nullable=True)
    created_at      = Column(DateTime, default=datetime.utcnow)
    scored_at       = Column(DateTime, nullable=True)
    remarks         = Column(Text, nullable=True)            # recruiter's private notes on this candidate
    comments        = relationship(
        "CandidateComment",
        back_populates="candidate",
        cascade="all, delete-orphan",
        order_by="CandidateComment.created_at.desc()"
    )

    # Relationship back to parent job post
    job_post = relationship("JobPost", back_populates="candidates")

    def __repr__(self):
        return f"<Candidate id={self.id} filename='{self.filename}' status='{self.status}'>"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    role = Column(String(64), default="Recruiter")
    created_at = Column(DateTime, default=datetime.utcnow)


class CandidateComment(Base):
    __tablename__ = "candidate_comments"

    id           = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    author_name  = Column(String(255), nullable=False)   # Mapped to st.user.name
    author_role  = Column(String(128), nullable=False)   # Mapped to the user's role
    comment_text = Column(Text, nullable=False)
    created_at   = Column(DateTime, default=datetime.utcnow)

    # Relationship back to the candidate
    candidate = relationship("Candidate", back_populates="comments")

# ── Helpers ───────────────────────────────────────────────────────────────────

def init_db():
    """Create all tables in the database (idempotent — safe to call on every startup)."""
    Base.metadata.create_all(bind=engine)


def get_session():
    """
    Yield a SQLAlchemy session and guarantee it is closed after use.
    Usage (outside Streamlit):
        with get_session() as session:
            session.add(...)
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def open_session():
    """
    Return a raw session for manual lifecycle management inside Streamlit pages.
    Callers are responsible for commit / rollback / close.
    """
    return SessionLocal()
