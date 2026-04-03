
from pathlib import Path
import pdfplumber

def extract_text_from_pdf(pdf_path):
    pdf_path = Path(pdf_path)
    pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            pages.append(text)
    return "\n".join(pages)
