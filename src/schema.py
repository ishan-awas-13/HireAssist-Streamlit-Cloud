from pydantic import BaseModel, Field
from typing import List, Optional

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
    programming_languages: List[str] = Field(default_factory=list)
    frameworks_and_tools: List[str] = Field(default_factory=list)
    soft_skills: List[str] = Field(default_factory=list)

class WorkExperience(BaseModel):
    company_name: Optional[str] = None
    job_title: Optional[str] = None
    location: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    is_current: bool = False
    responsibilities: List[str] = Field(default_factory=list)

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
    technologies_used: List[str] = Field(default_factory=list)

class CandidateProfile(BaseModel):
    personal_information: PersonalInformation
    professional_summary: Optional[str] = None
    skills: Skills
    work_experience: List[WorkExperience] = Field(default_factory=list)
    education: List[Education] = Field(default_factory=list)
    certifications: List[Certification] = Field(default_factory=list)
    projects: List[Project] = Field(default_factory=list)

class ResumeParserResponse(BaseModel):
    candidate_profile: CandidateProfile

