from pydantic import BaseModel, Field, field_validator
from typing import List, Optional


def _coerce_list(v):
    """Return [] if the LLM returned null for a list field."""
    return v if v is not None else []


class PersonalInformation(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None
    location: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None


class Skills(BaseModel):
    programming_languages: Optional[List[str]] = Field(default_factory=list)
    frameworks_and_tools: Optional[List[str]] = Field(default_factory=list)
    soft_skills: Optional[List[str]] = Field(default_factory=list)

    @field_validator("programming_languages", "frameworks_and_tools", "soft_skills", mode="before")
    @classmethod
    def coerce_none(cls, v):
        return _coerce_list(v)


class WorkExperience(BaseModel):
    company_name: Optional[str] = None
    job_title: Optional[str] = None
    location: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    is_current: bool = False
    responsibilities: Optional[List[str]] = Field(default_factory=list)

    @field_validator("responsibilities", mode="before")
    @classmethod
    def coerce_none(cls, v):
        return _coerce_list(v)


class Education(BaseModel):
    institution_name: Optional[str] = None
    degree: Optional[str] = None
    major: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    gpa: Optional[str] = None


class Certification(BaseModel):
    name: Optional[str] = None
    issuing_organization: Optional[str] = None
    issue_date: Optional[str] = None


class Project(BaseModel):
    project_name: Optional[str] = None
    description: Optional[str] = None
    technologies_used: Optional[List[str]] = Field(default_factory=list)

    @field_validator("technologies_used", mode="before")
    @classmethod
    def coerce_none(cls, v):
        return _coerce_list(v)


class CandidateProfile(BaseModel):
    personal_information: PersonalInformation
    professional_summary: Optional[str] = None
    skills: Skills
    work_experience: Optional[List[WorkExperience]] = Field(default_factory=list)
    education: Optional[List[Education]] = Field(default_factory=list)
    certifications: Optional[List[Certification]] = Field(default_factory=list)
    projects: Optional[List[Project]] = Field(default_factory=list)

    @field_validator("work_experience", "education", "certifications", "projects", mode="before")
    @classmethod
    def coerce_none(cls, v):
        return _coerce_list(v)


class ResumeParserResponse(BaseModel):
    candidate_profile: CandidateProfile
