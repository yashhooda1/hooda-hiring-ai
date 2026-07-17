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

import json

from resume_parser import parse_resume
from skill_extractor import extract_resume_intelligence
from ai_job_matcher import score_candidate

import os
from resume_builder import extract_text, detect_font, build_resume_docx, build_cover_letter_docx
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

        if st.button("Generate Tailored Documents"):
            try:
                with st.spinner("Tailoring your resume to the job description..."):
                    tailored = generate_tailored_resume(profile, resume_text, job_desc)
                    cover = generate_cover_letter(profile, resume_text, job_desc)
                    font_name = detect_font(tmp_path)
                    st.session_state["gen_resume"] = build_resume_docx(tailored, font_name)
                    st.session_state["gen_cover"] = build_cover_letter_docx(cover, font_name)
                    st.session_state["gen_font"] = font_name
                    st.session_state["gen_tailored"] = tailored
            except Exception as e:
                st.error(f"Generation failed: {e}")

        if st.session_state.get("gen_resume"):
            st.success(f"Documents ready. Font used: {st.session_state['gen_font']}")
            docx_mime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            st.download_button("Download Tailored Resume (.docx)",
                               data=st.session_state["gen_resume"],
                               file_name="tailored_resume.docx", mime=docx_mime)
            st.download_button("Download Cover Letter (.docx)",
                               data=st.session_state["gen_cover"],
                               file_name="cover_letter.docx", mime=docx_mime)
            with st.expander("Preview tailored resume content"):
                st.json(st.session_state["gen_tailored"])

else:
    st.info("Upload a resume PDF to begin.")
