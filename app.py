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

import json
import streamlit as st

from resume_parser import parse_resume
from skill_extractor import extract_resume_intelligence
from ai_job_matcher import score_candidate


st.set_page_config(page_title="HoodaAgents AI Hiring Engine", layout="centered")
st.title("HoodaAgents AI Hiring Engine")

resume = st.file_uploader("Upload Resume", type=["pdf"])
job_desc = st.text_area("Paste Job Description", height=140)

if resume is not None:

    # Save uploaded resume safely
    tmp_path = "resume_uploaded.pdf"
    with open(tmp_path, "wb") as f:
        f.write(resume.getbuffer())

    # Extract text
    resume_text = parse_resume(tmp_path)

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

else:
    st.info("Upload a resume PDF to begin.")