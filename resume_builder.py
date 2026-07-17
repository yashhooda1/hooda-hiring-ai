"""
resume_builder.py — Deterministic document assembly for HoodaAgents.

No LLM calls here. Pure, testable functions:
  - detect_font(path)          : best-effort font family from PDF or DOCX
  - build_resume_docx(...)     : clean single-column ATS resume in a given font
  - build_cover_letter_docx(...)
  - tailor_existing_docx(...)  : font-PRESERVING surgical edit (DOCX upload only)

Font-preservation reality:
  * DOCX upload -> font is recoverable and preserved EXACTLY (run surgery).
  * PDF upload  -> fonts are often CID-subset with opaque names (e.g. "CIDFont+F4"),
                   so the family is unrecoverable. We fall back to a clean ATS font.
"""

import re
import copy
from io import BytesIO
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

ATS_FALLBACK_FONT = "Calibri"
# PDF generic/CID names we should NOT trust as a real family
_UNRESOLVABLE = re.compile(r"^(CIDFont|[A-Z0-9]+\+?F\d+|Font\d*)$", re.IGNORECASE)


def _normalize_font(raw):
    if not raw:
        return None
    name = re.sub(r"^[A-Z]{6}\+", "", raw)          # strip subset prefix ABCDEE+
    name = re.split(r"[-,]", name)[0]               # drop "-BoldMT" etc.
    name = re.sub(r"(MT|PS|Regular|Bold|Italic|Light|Medium)$", "", name)
    name = name.strip()
    if not name or _UNRESOLVABLE.match(name):
        return None
    return name


def detect_font(path):
    """Return a usable font family, or ATS_FALLBACK_FONT if unrecoverable."""
    p = path.lower()
    try:
        if p.endswith(".docx"):
            doc = Document(path)
            f = doc.styles["Normal"].font.name
            return _normalize_font(f) or ATS_FALLBACK_FONT
        if p.endswith(".pdf"):
            import pdfplumber
            from collections import Counter
            counter = Counter()
            with pdfplumber.open(path) as pdf:
                for page in pdf.pages:
                    for ch in page.chars:
                        counter[ch.get("fontname", "")] += 1
            for raw, _ in counter.most_common():
                fam = _normalize_font(raw)
                if fam:
                    return fam
    except Exception:
        pass
    return ATS_FALLBACK_FONT


def _apply_base_font(doc, font_name):
    style = doc.styles["Normal"]
    style.font.name = font_name
    style.font.size = Pt(10.5)


def _heading(doc, text, font_name):
    p = doc.add_paragraph()
    r = p.add_run(text.upper())
    r.bold = True
    r.font.name = font_name
    r.font.size = Pt(11.5)
    r.font.color.rgb = RGBColor(0x1a, 0x1a, 0x1a)
    p.space_before = Pt(8)
    p.space_after = Pt(2)
    # thin rule under heading
    p_fmt = p.paragraph_format
    p_fmt.space_after = Pt(2)
    return p


def build_resume_docx(data, font_name, out=None):
    """data: structured dict (see schema in resume_generator). Returns bytes if out is None."""
    doc = Document()
    _apply_base_font(doc, font_name)
    for section in doc.sections:
        section.top_margin = section.bottom_margin = Pt(36)
        section.left_margin = section.right_margin = Pt(50)

    # Name
    name_p = doc.add_paragraph()
    name_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    nr = name_p.add_run(data.get("name", ""))
    nr.bold = True
    nr.font.name = font_name
    nr.font.size = Pt(18)

    # Contact line
    if data.get("contact"):
        c = doc.add_paragraph()
        c.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cr = c.add_run(data["contact"])
        cr.font.name = font_name
        cr.font.size = Pt(9.5)

    if data.get("summary"):
        _heading(doc, "Professional Summary", font_name)
        doc.add_paragraph(data["summary"])

    if data.get("skills"):
        _heading(doc, "Skills", font_name)
        skills = data["skills"]
        text = ", ".join(skills) if isinstance(skills, list) else str(skills)
        doc.add_paragraph(text)

    if data.get("experience"):
        _heading(doc, "Experience", font_name)
        for job in data["experience"]:
            h = doc.add_paragraph()
            left = h.add_run(f"{job.get('title','')} — {job.get('company','')}")
            left.bold = True
            if job.get("dates"):
                h.add_run(f"   ({job['dates']})").italic = True
            for b in job.get("bullets", []):
                doc.add_paragraph(b, style="List Bullet")

    if data.get("projects"):
        _heading(doc, "Projects", font_name)
        for pr in data["projects"]:
            h = doc.add_paragraph()
            h.add_run(pr.get("name", "")).bold = True
            for b in pr.get("bullets", []):
                doc.add_paragraph(b, style="List Bullet")

    if data.get("education"):
        _heading(doc, "Education", font_name)
        for ed in data["education"]:
            e = doc.add_paragraph()
            e.add_run(ed.get("degree", "")).bold = True
            tail = ", ".join(x for x in [ed.get("school", ""), ed.get("dates", "")] if x)
            if tail:
                e.add_run(f" — {tail}")

    return _save(doc, out)


# ---- PDF builders (fpdf2, no system deps) ----
_SERIF_HINTS = ("times", "georgia", "garamond", "cambria", "serif", "tex",
                "computer modern", "cmr", "minion", "palatino", "book antiqua")
_PUNCT = {"\u2014": "-", "\u2013": "-", "\u2022": "-", "\u25cf": "-", "\u2011": "-",
          "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"',
          "\u2026": "...", "\u00a0": " "}


def _pdf_family(font_name):
    n = (font_name or "").lower()
    return "Times" if any(h in n for h in _SERIF_HINTS) else "Helvetica"


def _pdf_safe(s):
    """Core PDF fonts are latin-1. Convert typographic punctuation to ASCII,
    keep Western accents (é, ñ, ü...), drop anything else rather than crash."""
    s = s or ""
    for k, v in _PUNCT.items():
        s = s.replace(k, v)
    return s.encode("latin-1", "ignore").decode("latin-1")


def _pdf_out(pdf, out):
    data = bytes(pdf.output())
    if out is None:
        return data
    with open(out, "wb") as f:
        f.write(data)
    return out


def build_resume_pdf(data, font_name, out=None):
    from fpdf import FPDF
    fam = _pdf_family(font_name)
    pdf = FPDF(format="Letter")
    pdf.set_auto_page_break(auto=True, margin=14)
    pdf.set_margins(18, 14, 18)
    pdf.add_page()
    W = pdf.w - pdf.l_margin - pdf.r_margin

    pdf.set_font(fam, "B", 18)
    pdf.multi_cell(W, 8, _pdf_safe(data.get("name", "")), align="C")
    if data.get("contact"):
        pdf.set_font(fam, "", 9)
        pdf.multi_cell(W, 5, _pdf_safe(data["contact"]), align="C")

    def heading(t):
        pdf.ln(2.5)
        pdf.set_font(fam, "B", 11.5)
        pdf.multi_cell(W, 6, _pdf_safe(t.upper()))
        y = pdf.get_y()
        pdf.set_draw_color(170, 170, 170)
        pdf.line(pdf.l_margin, y, pdf.w - pdf.r_margin, y)
        pdf.ln(1)

    def body(t, size=10.5):
        pdf.set_font(fam, "", size)
        pdf.multi_cell(W, 5, _pdf_safe(t))

    def bullet(t):
        pdf.set_font(fam, "", 10.5)
        pdf.multi_cell(W, 5, _pdf_safe("- " + t))

    if data.get("summary"):
        heading("Professional Summary"); body(data["summary"])
    if data.get("skills"):
        heading("Skills")
        sk = data["skills"]
        body(", ".join(sk) if isinstance(sk, list) else str(sk))
    if data.get("experience"):
        heading("Experience")
        for job in data["experience"]:
            pdf.set_font(fam, "B", 10.5)
            dates = job.get("dates", "")
            line = f"{job.get('title','')} - {job.get('company','')}"
            pdf.multi_cell(W, 5, _pdf_safe(line + (f"   ({dates})" if dates else "")))
            for b in job.get("bullets", []):
                bullet(b)
            pdf.ln(1)
    if data.get("projects"):
        heading("Projects")
        for pr in data["projects"]:
            pdf.set_font(fam, "B", 10.5)
            pdf.multi_cell(W, 5, _pdf_safe(pr.get("name", "")))
            for b in pr.get("bullets", []):
                bullet(b)
            pdf.ln(1)
    if data.get("education"):
        heading("Education")
        for ed in data["education"]:
            pdf.set_font(fam, "B", 10.5)
            tail = ", ".join(x for x in [ed.get("school", ""), ed.get("dates", "")] if x)
            pdf.multi_cell(W, 5, _pdf_safe(ed.get("degree", "") + (f" - {tail}" if tail else "")))

    return _pdf_out(pdf, out)


def build_cover_letter_pdf(body_text, font_name, out=None):
    from fpdf import FPDF
    fam = _pdf_family(font_name)
    pdf = FPDF(format="Letter")
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.set_margins(25, 20, 25)
    pdf.add_page()
    W = pdf.w - pdf.l_margin - pdf.r_margin
    pdf.set_font(fam, "", 11)
    for para in body_text.split("\n\n"):
        para = para.strip()
        if para:
            pdf.multi_cell(W, 6, _pdf_safe(para))
            pdf.ln(3)
    return _pdf_out(pdf, out)


# ---- Faithful DOCX -> PDF via LibreOffice (exact render; needs soffice installed) ----
import os
import shutil
import subprocess
import tempfile


def libreoffice_available():
    return shutil.which("soffice") is not None or shutil.which("libreoffice") is not None


def docx_to_pdf(docx_bytes, out=None):
    """Convert DOCX bytes to PDF using headless LibreOffice.

    Produces a PDF that matches the DOCX exactly (layout + font, provided the
    font — or a metric-compatible substitute — is installed in the container).
    Raises RuntimeError if soffice is unavailable or conversion fails; callers
    should fall back to the fpdf2 builder.
    """
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice:
        raise RuntimeError("LibreOffice (soffice) is not installed")

    with tempfile.TemporaryDirectory() as tmp:
        src = os.path.join(tmp, "in.docx")
        with open(src, "wb") as f:
            f.write(docx_bytes)
        # Unique profile dir avoids "another instance is running" locks under concurrency
        profile = os.path.join(tmp, "profile")
        cmd = [
            soffice, "--headless", "--nologo", "--nofirststartwizard",
            f"-env:UserInstallation=file://{profile}",
            "--convert-to", "pdf", "--outdir", tmp, src,
        ]
        proc = subprocess.run(cmd, capture_output=True, timeout=90)
        pdf_path = os.path.join(tmp, "in.pdf")
        if proc.returncode != 0 or not os.path.exists(pdf_path):
            raise RuntimeError(
                f"LibreOffice conversion failed: {proc.stderr.decode('utf-8', 'ignore')[:300]}"
            )
        with open(pdf_path, "rb") as f:
            data = f.read()

    if out is None:
        return data
    with open(out, "wb") as f:
        f.write(data)
    return out


def build_cover_letter_docx(body_text, font_name, out=None):
    doc = Document()
    _apply_base_font(doc, font_name)
    for section in doc.sections:
        section.top_margin = section.bottom_margin = Pt(54)
        section.left_margin = section.right_margin = Pt(72)
    for para in body_text.split("\n\n"):
        para = para.strip()
        if para:
            doc.add_paragraph(para)
    return _save(doc, out)


# ---- Font-PRESERVING surgical path (DOCX upload only) ----
def _replace_paragraph_text(paragraph, new_text):
    runs = paragraph.runs
    rPr = None
    if runs:
        src = runs[0]._element.rPr
        if src is not None:
            rPr = copy.deepcopy(src)
        for r in list(runs):
            r._element.getparent().remove(r._element)
    nr = paragraph.add_run(new_text)
    if rPr is not None:
        nr._element.insert(0, rPr)


def _iter_paragraphs(doc):
    from docx.document import Document as _Doc
    from docx.text.paragraph import Paragraph
    from docx.table import Table
    def walk(parent):
        elm = parent.element.body if isinstance(parent, _Doc) else parent._element
        for child in elm.iterchildren():
            if child.tag.endswith("}p"):
                yield Paragraph(child, parent)
            elif child.tag.endswith("}tbl"):
                for row in Table(child, parent).rows:
                    for cell in row.cells:
                        yield from walk(cell)
    yield from walk(doc)


def extract_docx_paragraphs(path):
    doc = Document(path)
    return [{"index": i, "text": p.text} for i, p in enumerate(_iter_paragraphs(doc)) if p.text.strip()]


def tailor_existing_docx(path, edits, out=None):
    """edits: [{'index', 'new_text'}] -> font preserved exactly."""
    doc = Document(path)
    by_index = {e["index"]: e["new_text"] for e in edits}
    for i, p in enumerate(_iter_paragraphs(doc)):
        if i in by_index:
            _replace_paragraph_text(p, by_index[i])
    return _save(doc, out)


def extract_text(path):
    """Unified text extraction for the compare step. Handles PDF and DOCX."""
    p = path.lower()
    if p.endswith(".docx"):
        doc = Document(path)
        return "\n".join(para.text for para in _iter_paragraphs(doc))
    # default: PDF via pdfplumber
    import pdfplumber
    text = ""
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                text += t + "\n"
    return text


def _save(doc, out):
    if out is None:
        buf = BytesIO()
        doc.save(buf)
        return buf.getvalue()
    doc.save(out)
    return out
