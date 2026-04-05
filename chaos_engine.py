import numpy as np
import random

class ChaosEngine:
    def __init__(self, seed=42, failure_types=None, failure_weights=None):
        if failure_types is None:
            failure_types = ['timeout', 'wrong_data', 'partial_success', 'normal_execution']
        if failure_weights is None:
            failure_weights = [0.1, 0.1, 0.1, 0.7]  # Default weights
        self.seed = seed
        self.failure_types = failure_types
        self.failure_weights = failure_weights
        random.seed(self.seed)

    def inject_failure(self):
        return random.choices(self.failure_types, weights=self.failure_weights)[0]

    def reset(self):
        random.seed(self.seed)