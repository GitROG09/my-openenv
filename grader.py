from typing import Dict, Any

class Grader:
    def __init__(self):
        self.results = {}
    
    def grade(self, task_id: str, score: float) -> Dict[str, Any]:
        normalized_score = min(score / 10.0, 1.0)
        grade = "A" if normalized_score >= 0.9 else "B" if normalized_score >= 0.8 else "C" if normalized_score >= 0.7 else "D"
        
        result = {
            "task_id": task_id,
            "raw_score": score,
            "normalized_score": normalized_score,
            "grade": grade
        }
        
        self.results[task_id] = result
        return result
    
    def get_results(self) -> Dict[str, Any]:
        return self.results
