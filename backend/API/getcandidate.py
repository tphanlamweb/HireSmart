import json
import logging

logger = logging.getLogger("uvicorn")

def print_candidate(candidate):
    
    #logger.info("candidate: ", candidate['full_name'])
    print('Extracted Candidate Name: ', candidate.get('full_name', 'N/A'))
    candidate_size = len(candidate['filedata'])
    print(f"Candidate file size: {candidate_size} bytes")
    #print('data: ', candidate['filedata'])
