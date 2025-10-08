import streamlit as st
from typing import List
from io import BytesIO
import tempfile
import chardet
from pypdf import PdfReader
from docx import Document
import tempfile
import streamlit as st


# --- OCR imports (lazy) ---
try:
    from pdf2image import convert_from_bytes
    import pytesseract
except Exception as e:
    convert_from_bytes = None
    pytesseract = None


# --- Utility functions ---
def _to_bytes(uploaded_file) -> bytes:
    """Convert a Streamlit UploadedFile to bytes."""
    return uploaded_file.getvalue()


def _clean(text: str) -> str:
    """Clean extracted text by normalizing spaces."""
    return " ".join(text.replace("\r", " ").replace("\xa0", " ").split())


# --- Extractors for each file type ---
def _extract_txt(file_bytes: bytes) -> str:
    """Extract text from plain text files."""
    enc = chardet.detect(file_bytes).get("encoding") or "utf-8"
    try:
        return file_bytes.decode(enc, errors="ignore")
    except Exception:
        return file_bytes.decode("utf-8", errors="ignore")


def _extract_pdf(file_bytes: bytes) -> str:
    """
    Extract text from a PDF. Falls back to OCR if text is empty (for scanned PDFs).
    """
    buf = BytesIO(file_bytes)
    reader = PdfReader(buf)
    parts = []
    for page in reader.pages:
        try:
            txt = page.extract_text() or ""
            parts.append(txt)
        except Exception:
            parts.append("")
    text = "\n".join(parts)

    # OCR fallback only if no text and OCR tools are available
    if not text.strip() and convert_from_bytes and pytesseract:
        try:
            images = convert_from_bytes(file_bytes)
            ocr_text = [pytesseract.image_to_string(img, lang="eng") for img in images]
            text = "\n".join(ocr_text)
        except Exception as e:
            print("⚠️ OCR failed:", e)
    return text


def _extract_docx(file_bytes: bytes) -> str:
    """Extract text from a Word document."""
    buf = BytesIO(file_bytes)
    doc = Document(buf)
    return "\n".join([p.text for p in doc.paragraphs])


@st.cache_resource(show_spinner=False)
def _load_whisper_model():
    """
    Load and cache the faster-whisper model so it's reused across runs.
    The model is loaded once and stays in memory for later audio uploads.
    """
    from faster_whisper import WhisperModel
    print("🎧 Loading Whisper model (base)...")
    return WhisperModel("base", device="cpu", compute_type="int8")  # use 'tiny' for faster

def _transcribe_audio(file_bytes: bytes, filename: str) -> str:
    """
    Transcribe audio using faster-whisper (cached model).
    """
    print(f"🎙️ Transcribing audio file: {filename}")
    with tempfile.NamedTemporaryFile(delete=False, suffix=filename) as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    model = _load_whisper_model()
    segments, info = model.transcribe(tmp_path, beam_size=1)

    transcript_lines = []
    speaker_id = 1
    last_end = 0.0

    for seg in segments:
        # alternate speakers when there's a gap >2s
        if seg.start - last_end > 2.0:
            speaker_id = 1 if speaker_id == 2 else 2
        transcript_lines.append(f"Speaker {speaker_id}: {seg.text.strip()}")
        last_end = seg.end

    print(f"✅ Transcription complete ({filename})")
    return "\n".join(transcript_lines)

# --- Main public functions ---
def extract_text_from_upload(uploaded_file) -> str:
    """
    Handle a single file from Streamlit's st.file_uploader.
    Supports: .txt, .pdf, .docx, audio (.mp3, .wav, .m4a)
    """
    name = (uploaded_file.name or "").lower()
    b = _to_bytes(uploaded_file)

    if name.endswith(".txt"):
        raw = _extract_txt(b)
    elif name.endswith(".pdf"):
        raw = _extract_pdf(b)
    elif name.endswith(".docx"):
        raw = _extract_docx(b)
    elif name.endswith((".mp3", ".wav", ".m4a")):
        raw = _transcribe_audio(b, name)
    else:
        # Safe fallback
        raw = _extract_txt(b)

    return _clean(raw)


def extract_texts_from_uploads(files: List) -> str:
    """
    Handle multiple uploads — concatenate them in a readable way.
    """
    parts = []
    for f in files:
        text = extract_text_from_upload(f)
        parts.append(f"# File: {f.name}\n{text}")
    return "\n\n".join(parts)
