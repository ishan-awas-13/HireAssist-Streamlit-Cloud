import os
from pypdf import PdfReader
from docx import Document
import streamlit as st

def extract_text_from_pdf(file_input) -> str:
    """Extracts raw string text from a target PDF file or file-like object."""
    reader = PdfReader(file_input)
    full_text = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            full_text.append(text)
    return "\n".join(full_text)

def extract_text_from_docx(file_input) -> str:
    """Extracts raw string text from a target Word Document file or file-like object."""
    doc = Document(file_input)
    full_text = []
    for paragraph in doc.paragraphs:
        if paragraph.text:
            full_text.append(paragraph.text)
    return "\n".join(full_text)

def get_clean_resume_text(file_input) -> str:
    """Identifies file extension and channels it to the appropriate parsing utility."""
    # Determine the file name/path to extract extension
    if isinstance(file_input, (str, os.PathLike)):
        filename = file_input
    else:
        filename = file_input.name
        
    ext = os.path.splitext(filename)[1].lower()
    
    if ext == '.pdf':
        raw_text = extract_text_from_pdf(file_input)
    elif ext == '.docx':
        raw_text = extract_text_from_docx(file_input)
    else:
        raise ValueError(f"Unsupported extension context: {ext}")
        
    # Standardize string lines and remove non-printable structural gaps
    clean_lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    return "\n".join(clean_lines)

    