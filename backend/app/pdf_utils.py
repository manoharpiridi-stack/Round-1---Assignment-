"""
Very small helper: pulls plain text out of an uploaded PDF so we can
feed it to the same extract_fields() node used for pasted text.

The assignment explicitly says production-grade OCR is NOT required,
so this just reads the text layer of the PDF. If someone uploads a
scanned/image-only PDF, extract_text() will return "" and the graph
will simply extract nothing - that's an acceptable, honest limitation
to mention in the interview if asked.
"""
from pypdf import PdfReader
import io


def extract_text_from_pdf(file_bytes: bytes) -> str:
    reader = PdfReader(io.BytesIO(file_bytes))
    text_parts = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(text_parts).strip()
