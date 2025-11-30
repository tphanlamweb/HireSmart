import json
import logging

logger = logging.getLogger("uvicorn")

def print_candidate(candidate):
    
    #logger.info("candidate: ", candidate['full_name'])
    candidate_size = len(candidate['filedata'])
    print(f"Candidate file size: {candidate_size} bytes")
    print('data: ', candidate['filedata'])
