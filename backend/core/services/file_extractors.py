from PyPDF2 import PdfReader
from django.core.files.storage import default_storage
from docx import Document
from core.services.content_quality_filter import ContentQualityFilter
import os

_quality_filter = ContentQualityFilter()

def extract_text_from_file(path):
    _, ext = os.path.splitext(path.lower())
    absolute_path = default_storage.path(path)

    if ext == '.pdf':
        return extract_pdf(absolute_path)
    elif ext == '.docx':
        return extract_docx(absolute_path)
    elif ext in ['.txt', '.md']:
        return extract_txt(absolute_path)
    else:
        raise ValueError(f"Unsupported file type: {ext}")

def extract_pdf(path):
    reader = PdfReader(path)
    text = "\n".join([page.extract_text() or '' for page in reader.pages])
    return _quality_filter.remove_emojis(text)

def extract_docx(path):
    doc = Document(path)
    text = "\n".join([para.text for para in doc.paragraphs])
    return _quality_filter.remove_emojis(text)

def extract_txt(path):
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()
    return _quality_filter.remove_emojis(text)
