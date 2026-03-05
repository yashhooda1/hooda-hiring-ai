from sentence_transformers import SentenceTransformer
import numpy as np

model = SentenceTransformer("all-MiniLM-L6-v2")

def match_candidate(resume_text, job_description):

    resume_vector = model.encode([resume_text])
    job_vector = model.encode([job_description])

    similarity = np.dot(resume_vector, job_vector.T)

    return similarity[0][0]