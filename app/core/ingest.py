from typing import List
from io import BytesIO
import chardet
from streamlit.runtime.uploaded_file_manager import UploadedFile


def _to_bytes(uploaded_file: UploadedFile) -> bytes:
    return uploaded_file.getvalue()


def _clean(text: str) -> str:
    return " ".join(text.replace("\r", " ").replace("\xa0", " ").split())


def _extract_txt(file_bytes: bytes) -> str:
    enc = chardet.detect(file_bytes).get("encoding") or "utf-8"
    try:
        return file_bytes.decode(enc, errors="ignore")
    except Exception:
        return file_bytes.decode("utf-8", errors="ignore")


def _extract_pdf(file_bytes: bytes) -> str:
    from pypdf import PdfReader
    from pdf2image import convert_from_bytes
    import pytesseract
    from io import BytesIO

    text_pages = []

    # First try PyPDF extraction
    reader = PdfReader(BytesIO(file_bytes))
    for page in reader.pages:
        try:
            txt = page.extract_text()
            if txt:
                text_pages.append(txt)
        except Exception:
            pass
    print("PyPDF extracted:", text_pages)

    # If no text found, fallback to OCR
    if not any(text_pages):
        print("⚡ No text from PyPDF, switching to OCR...")
        images = convert_from_bytes(file_bytes,dpi=300)
        for i, img in enumerate(images, start=1):
            ocr_text = pytesseract.image_to_string(img,config="--psm 6 --oem 3")
            print(f"OCR resultpage{i}:", ocr_text[:200])
            if ocr_text.strip():
                text_pages.append(ocr_text)

    return "\n".join(text_pages)


def _extract_docx(file_bytes: bytes) -> str:
    from docx import Document
    doc = Document(BytesIO(file_bytes))
    paras = [p.text for p in doc.paragraphs]
    return "\n".join(paras)


def extract_text_from_upload(uploaded_file: UploadedFile) -> str:
    """
    Handle a single file from Streamlit's st.file_uploader.
    Supports: .txt, .pdf, .docx
    """
    name = (uploaded_file.name or "").lower()
    b = _to_bytes(uploaded_file)

    if name.endswith(".txt"):
        raw = _extract_txt(b)
    elif name.endswith(".pdf"):
        raw = _extract_pdf(b)
    elif name.endswith(".docx"):
        raw = _extract_docx(b)
    else:
        raw = _extract_txt(b)
    return _clean(raw)


def extract_texts_from_uploads(files: List[UploadedFile]) -> str:
    """
    For multiple uploads — concatenate in a readable way.
    """
    parts = []
    for f in files:
        text = extract_text_from_upload(f)
        parts.append(f"# File: {f.name}\n{text}")
    return "\n\n".join(parts)
