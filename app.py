''' import streamlit as st
from resume_parser import parse_resume
from job_matcher import match_candidate

st.title("HoodaAgents AI Hiring Engine")

resume = st.file_uploader("Upload Resume")
job_desc = st.text_area("Paste Job Description")

if resume and job_desc:

    with open("resume.pdf", "wb") as f:
        f.write(resume.read())

    parsed = parse_resume("resume.pdf")

    score = match_candidate(parsed["raw_text"], job_desc)

    st.write("Candidate Match Score:", score) '''

import streamlit as st

st.set_page_config(
    page_title="HoodaAgents AI Hiring Engine",
    page_icon="🤖",
    layout="wide",
)

# SEO meta injection
st.markdown("""
    <head>
        <meta name="description" content="AI-powered resume intelligence engine. Upload a resume and get instant candidate fit analysis against any job description.">
        <meta name="keywords" content="AI hiring, resume parser, job matching, AI recruiting, candidate intelligence">
        <meta property="og:title" content="HoodaAgents AI Hiring Engine">
        <meta property="og:description" content="AI-powered resume intelligence and job fit analysis.">
        <meta property="og:url" content="https://hoodahiring.ai">
    </head>
""", unsafe_allow_html=True)

# --- Brand polish (fonts + buttons). Native theme lives in .streamlit/config.toml ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&family=Space+Mono&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
code, pre { font-family: 'Space Mono', monospace; }
h1 { letter-spacing: -0.02em; font-weight: 700; }
.stButton > button {
    background: #4caf50; color: #0d1117; border: none;
    border-radius: 8px; font-weight: 600; transition: all .15s ease;
}
.stButton > button:hover { background: #43a047; transform: translateY(-1px); }
.stDownloadButton > button {
    background: #1e293b; color: #4caf50; border: 1px solid #4caf50; border-radius: 8px;
}
[data-testid="stFileUploader"] { background: #1e293b; border-radius: 12px; padding: .4rem; }
</style>
""", unsafe_allow_html=True)

import json

from resume_parser import parse_resume
from skill_extractor import extract_resume_intelligence
from ai_job_matcher import score_candidate

import os
from resume_builder import (extract_text, detect_font,
                            build_resume_docx, build_cover_letter_docx,
                            build_resume_pdf, build_cover_letter_pdf,
                            docx_to_pdf, libreoffice_available, to_markdown)
from resume_generator import generate_tailored_resume, generate_cover_letter


st.set_page_config(page_title="HoodaAgents AI Hiring Engine", layout="centered")
st.title("HoodaAgents AI Hiring Engine")

st.markdown(
"""
### AI Resume Intelligence Engine

Upload a resume and compare it against a job description.  
The system extracts structured candidate information and evaluates job fit using an AI model.
"""
)

resume = st.file_uploader("Upload Resume", type=["pdf", "docx"])
job_desc = st.text_area("Paste Job Description", height=140)

if st.button("Load Sample Job Description"):
    job_desc = """
Data Engineer

Responsibilities:
- Build ETL pipelines
- Work with SQL, Python, and cloud data platforms
- Build dashboards with Power BI
"""

st.markdown(
"[View Source Code on GitHub](https://github.com/yashhooda1/hooda-hiring-ai)"
)

if resume is not None:

    # Save uploaded resume safely
    tmp_path = "resume_uploaded" + os.path.splitext(resume.name)[1].lower()
    with open(tmp_path, "wb") as f:
        f.write(resume.getbuffer())

    # Extract text
    resume_text = extract_text(tmp_path)

    if not resume_text or len(resume_text.strip()) == 0:
        st.error("Could not extract text from this PDF. Try exporting it as a text-based PDF (not scanned).")
        st.stop()

    # Show preview
    st.subheader("Extracted Resume Text (Preview)")
    st.caption("First ~1200 characters")
    st.code(resume_text[:1200])

    # Call AI extractor
    st.subheader("AI Resume Intelligence")

    try:
        with st.spinner("Analyzing resume with AI..."):
            profile = extract_resume_intelligence(resume_text)

        # If OpenAI returns JSON string convert to dict
        if isinstance(profile, str):
            profile = json.loads(profile)

    except Exception as e:
        st.error(f"AI extraction failed: {e}")
        st.stop()

    # Show raw JSON
    st.json(profile)

    # Candidate summary
    st.subheader("Candidate Summary")

    name = profile.get("name", "Candidate")
    st.write(f"**{name}**")

    bullets = profile.get("summary_bullets", [])

    if bullets:
        for b in bullets[:6]:
            st.write(f"- {b}")

    # Skill matching vs job description
    if job_desc and job_desc.strip():

        st.subheader("Quick Skill Match")

        skills = profile.get("skills", {})

        flat_skills = []

        if isinstance(skills, dict):
            for k, v in skills.items():
                if isinstance(v, list):
                    flat_skills.extend(v)

        flat_skills_norm = {s.lower().strip() for s in flat_skills if isinstance(s, str)}

        jd_norm = job_desc.lower()

        hits = sorted([s for s in flat_skills_norm if s in jd_norm])

        st.write(f"**Matching Skills Found:** {len(hits)}")

        if hits:
            st.write(", ".join(hits[:40]))
        else:
            st.info("No direct skill matches found.")
        
        st.subheader("AI Candidate Fit Analysis")
        
        try:
            with st.spinner("Evaluating candidate vs job description..."):
                result = score_candidate(profile, job_desc)
            if isinstance(result, str):
                try:
                    result = json.loads(result)
                except:
                    pass
            if isinstance(result, dict):
                score = result.get("score", "N/A")
                st.metric("Candidate Fit Score", score)
                st.progress(score/100)
                
                st.write("### Strengths")
                for s in result.get("strengths", []):
                    st.write(f"- {s}")
                
                st.write("### Gaps")
                for g in result.get("gaps", []):
                    st.write(f"- {g}")
                
                st.write("### Summary")
                st.write(result.get("summary", ""))
            else:
                st.write(result)
            
        except Exception as e:
            st.error(f"AI match scoring failed: {e}")

        # ---- Tailored Resume + Cover Letter generator ----
        st.divider()
        st.subheader("Tailored Resume + Cover Letter")

        if tmp_path.lower().endswith(".docx"):
            st.caption("DOCX upload detected - the original font is preserved exactly.")
        else:
            st.caption("PDF upload - a clean ATS resume is generated in the closest recoverable font.")

        faithful = st.toggle(
            "Faithful PDF (exact DOCX render via LibreOffice - slower)",
            value=False,
            help="On: PDF matches the DOCX exactly. Off: fast, clean ATS PDF.",
        )

        if st.button("Generate Tailored Documents"):
            try:
                with st.spinner("Tailoring your resume to the job description..."):
                    tailored = generate_tailored_resume(profile, resume_text, job_desc)
                    cover = generate_cover_letter(profile, resume_text, job_desc)
                    font_name = detect_font(tmp_path)
                    resume_docx = build_resume_docx(tailored, font_name)
                    cover_docx = build_cover_letter_docx(cover, font_name)

                    if faithful and libreoffice_available():
                        try:
                            resume_pdf = docx_to_pdf(resume_docx)
                            cover_pdf = docx_to_pdf(cover_docx)
                            st.session_state["gen_pdf_mode"] = "faithful (LibreOffice)"
                        except Exception as conv_err:
                            resume_pdf = build_resume_pdf(tailored, font_name)
                            cover_pdf = build_cover_letter_pdf(cover, font_name)
                            st.session_state["gen_pdf_mode"] = f"fast (faithful failed: {conv_err})"
                    else:
                        resume_pdf = build_resume_pdf(tailored, font_name)
                        cover_pdf = build_cover_letter_pdf(cover, font_name)
                        st.session_state["gen_pdf_mode"] = "fast (fpdf2)"

                    st.session_state["gen_resume"] = resume_docx
                    st.session_state["gen_cover"] = cover_docx
                    st.session_state["gen_resume_pdf"] = resume_pdf
                    st.session_state["gen_cover_pdf"] = cover_pdf
                    st.session_state["gen_font"] = font_name
                    st.session_state["gen_tailored"] = tailored
            except Exception as e:
                st.error(f"Generation failed: {e}")

        if st.session_state.get("gen_resume"):
            st.success(f"Documents ready. Font: {st.session_state['gen_font']}  -  PDF mode: {st.session_state.get('gen_pdf_mode','fast')}")
            docx_mime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            r_col1, r_col2 = st.columns(2)
            with r_col1:
                st.download_button("Resume (.docx)", data=st.session_state["gen_resume"],
                                   file_name="tailored_resume.docx", mime=docx_mime,
                                   use_container_width=True)
            with r_col2:
                st.download_button("Resume (.pdf)", data=st.session_state["gen_resume_pdf"],
                                   file_name="tailored_resume.pdf", mime="application/pdf",
                                   use_container_width=True)
            c_col1, c_col2 = st.columns(2)
            with c_col1:
                st.download_button("Cover Letter (.docx)", data=st.session_state["gen_cover"],
                                   file_name="cover_letter.docx", mime=docx_mime,
                                   use_container_width=True)
            with c_col2:
                st.download_button("Cover Letter (.pdf)", data=st.session_state["gen_cover_pdf"],
                                   file_name="cover_letter.pdf", mime="application/pdf",
                                   use_container_width=True)
            with st.expander("Preview tailored resume content"):
                st.json(st.session_state["gen_tailored"])

            st.markdown("**Copy tailored content** (for pasting into LaTeX or another editor):")
            md = to_markdown(st.session_state["gen_tailored"])
            st.code(md, language="markdown")
            st.download_button("Download as Markdown (.md)", data=md.encode("utf-8"),
                               file_name="tailored_resume.md", mime="text/markdown",
                               use_container_width=True)

else:
    st.info("Upload a resume PDF to begin.")
