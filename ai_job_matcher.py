import llm
import os
import json


def score_candidate(profile, job_desc, provider="openai"):

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

    return llm.complete(prompt, provider=provider)
