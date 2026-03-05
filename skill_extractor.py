from openai import OpenAI
from dotenv import load_dotenv
import os
import json
import re

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def extract_resume_intelligence(resume_text):

    prompt = f"""
Extract structured resume information.

Return ONLY valid JSON.

Fields:
name
skills
experience
education
projects
summary_bullets

Resume:
{resume_text}
"""

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt
    )

    output = response.output_text

    # Clean output in case model adds extra text
    match = re.search(r"\{.*\}", output, re.DOTALL)

    if match:
        json_text = match.group(0)
        return json.loads(json_text)

    raise ValueError("Could not parse JSON from AI response")