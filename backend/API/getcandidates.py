import backend.API.candidates_CV_Scoring as cv
import os
def getcandidates():
    filename = 'demo_data.csv'
    file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), f'../results/{filename}'))
    candidate = cv.get_last_candidate(file_path)
    return candidate