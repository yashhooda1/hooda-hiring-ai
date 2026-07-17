"""
resume_generator.py — LLM content generation for HoodaAgents.

Matches the existing OpenAI Responses API pattern used across the repo
(client.responses.create(model="gpt-4.1-mini", input=prompt) -> .output_text).

Two functions:
  - generate_tailored_resume(profile, resume_text, job_desc) -> structured dict
  - generate_cover_letter(profile, resume_text, job_desc)    -> str

Guardrail: the model may rephrase, reorder, and surface JD-relevant keywords
that are TRUTHFULLY supported by the resume. It must not invent employers,
titles, dates, degrees, or metrics.
"""

import os
import re
import json
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL = "gpt-4.1-mini"


def _extract_json(text):
    text = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("Could not parse JSON from AI response")
    return json.loads(match.group(0))


def generate_tailored_resume(profile, resume_text, job_desc):
    prompt = f"""
You are an expert resume writer optimizing a resume for an ATS and a specific job.

Rewrite the candidate's resume to align with the JOB DESCRIPTION while staying
strictly truthful. Rules:
- Do NOT invent employers, job titles, dates, degrees, certifications, or metrics.
- You MAY rephrase bullets, reorder for relevance, and surface keywords from the
  job description that are genuinely supported by the candidate's experience.
- Keep it concise and achievement-oriented (strong verbs, quantified where the
  source already provides numbers).

Return ONLY valid JSON with this exact schema:
{{
  "name": "string",
  "contact": "single line: email | phone | location | links",
  "summary": "2-3 sentence professional summary tailored to the job",
  "skills": ["skill", "..."],
  "experience": [
    {{"title":"", "company":"", "dates":"", "bullets":["", ""]}}
  ],
  "projects": [{{"name":"", "bullets":["", ""]}}],
  "education": [{{"degree":"", "school":"", "dates":""}}]
}}

STRUCTURED PROFILE (from parser):
{json.dumps(profile)}

RAW RESUME TEXT:
{resume_text}

JOB DESCRIPTION:
{job_desc}
"""
    resp = client.responses.create(model=MODEL, input=prompt)
    return _extract_json(resp.output_text)


def generate_cover_letter(profile, resume_text, job_desc):
    name = profile.get("name", "the candidate") if isinstance(profile, dict) else "the candidate"
    prompt = f"""
Write a concise, professional cover letter (about 250-320 words) for {name},
tailored to the JOB DESCRIPTION below. Ground every claim in the candidate's
actual experience — do not fabricate. Use a confident, specific tone; avoid
generic filler. Structure: greeting, opening hook, 1-2 body paragraphs mapping
experience to the role's needs, closing with a call to action.

Return ONLY the letter text (no markdown, no commentary). Separate paragraphs
with a blank line.

CANDIDATE PROFILE:
{json.dumps(profile)}

JOB DESCRIPTION:
{job_desc}
"""
    resp = client.responses.create(model=MODEL, input=prompt)
    return resp.output_text.strip()
