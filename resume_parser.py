''' import pdfplumber
from openai import OpenAI

client = OpenAI()

def parse_resume(file_path):

    text = ""

    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text()

    prompt = f"""
    Extract structured resume information from the following resume.

    Return JSON with:
    name
    skills
    experience
    education
    projects

    Resume:
    {text}
    """

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt
    )

    return response.output_text
 '''
 
import pdfplumber

def parse_resume(file_path):

    text = ""

    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"

    return text