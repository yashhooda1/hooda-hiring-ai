# HoodaAgents AI Hiring Engine

An AI-powered resume intelligence and hiring assistant that analyzes resumes and evaluates candidate fit against job descriptions.

This tool parses resume PDFs, extracts structured candidate information using a Large Language Model (LLM), and performs AI-powered job matching.

Live App:
https://jnopbakdpluthfpwq9whli.streamlit.app/

YouTube Demo:
https://www.youtube.com/watch?v=4KTblUUGv4I

---

## Features

• Upload resume PDFs  
• Extract structured resume intelligence using AI  
• Identify candidate skills, experience, education, and projects  
• Generate candidate summaries  
• Perform skill matching against job descriptions  
• AI-powered candidate fit analysis with strengths and gaps

---

## How It Works

The system follows this pipeline:

Resume Upload  
↓  
PDF text extraction (pdfplumber)  
↓  
LLM resume intelligence extraction (OpenAI)  
↓  
Structured candidate profile JSON  
↓  
Skill matching with job description  
↓  
AI candidate fit scoring

---

## Tech Stack

Python  
Streamlit  
OpenAI API  
pdfplumber  
python-dotenv  

hooda-hiring-ai
│
├── app.py # Streamlit application
├── resume_parser.py # Extracts text from PDF resumes
├── skill_extractor.py # AI extraction of resume intelligence
├── ai_job_matcher.py # AI evaluation of candidate fit
├── requirements.txt # Python dependencies
└── README.md

---

## Running Locally

Clone the repository:

```bash
git clone https://github.com/yashhooda1/hooda-hiring-ai.git
cd hooda-hiring-ai


pip install -r requirements.txt

OPENAI_API_KEY=your_api_key_here

streamlit run app.py


Future Improvements

• Multi-resume ranking system
• Vector search for semantic skill matching
• Recruiter dashboard
• Candidate ranking leaderboard
• Support for DOCX resumes
• ATS integration

Author

Yash Hooda
Computer Science Graduate – UT Dallas
AI Engineer | Data Engineer | AI Systems Builder

GitHub:
https://github.com/yashhooda1


License

This project is open-source and available under the MIT License.


---

# 3️⃣ Push README to GitHub

Run this:

```bash
git add README.md
git commit -m "Add project README"
git push

---

## Project Structure
