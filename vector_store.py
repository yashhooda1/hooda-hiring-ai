from zvec import ZVec
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")

db = ZVec(dim=384)

def add_resume(resume_text):

    vector = model.encode(resume_text)

    db.add(vector, {"resume": resume_text})

def search_candidates(job_description):

    query_vector = model.encode(job_description)

    results = db.search(query_vector, top_k=5)

    return results