
import hashlib
import datetime
import fitz  # PyMuPDF
import os

SECRET_KEY = b"super-secret-salt"

def get_pdf_text(filepath):
    doc = fitz.open(filepath)
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def sign_pdf(filepath):
    text = get_pdf_text(filepath)
    h = hashlib.pbkdf2_hmac('sha256', text.encode(), SECRET_KEY, 100000)
    sig = h.hex()

    doc = fitz.open(filepath)
    doc.set_metadata({
        "modDate": datetime.datetime.now().isoformat(),
        "keywords": f"sig:{sig}"
    })

    dir_name = os.path.dirname(filepath)
    filename = os.path.basename(filepath)
    new_path = os.path.join(dir_name, "signed_" + filename)
    doc.save(new_path)

    return sig, datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), new_path

def verify_pdf(filepath):
    doc = fitz.open(filepath)
    meta = doc.metadata
    keywords = meta.get("keywords", "")
    if keywords.startswith("sig:"):
        return keywords[4:]
    return ""
