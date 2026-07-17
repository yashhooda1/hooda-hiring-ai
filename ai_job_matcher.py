from openai import OpenAI
import os
import json

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL = os.getenv("OPENAI_MODEL", "gpt-5.4-mini")

def score_candidate(profile, job_desc):

    prompt = f"""
You are an AI technical recruiter.

Evaluate how well this candidate matches the job.

Return JSON:

score (0-100)
strengths
gaps
summary

Candidate:
{json.dumps(profile)}

Job Description:
{job_desc}
"""

    response = client.responses.create(
        model=MODEL,
        input=prompt
    )

    return response.output_text
