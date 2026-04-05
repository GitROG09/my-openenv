def calculate_reward(state, action):
    """
    Calculate the reward based on the given state and action.
    """
    # Insert reward shaping logic here
    reward = 0
    # Example logic:
    if action == 'goal':
        reward = 10
    elif action == 'penalty':
        reward = -5
    return reward

def normalize_score(score, min_score, max_score):
    """
    Normalize the score to a range of 0 to 1.
    """
    return (score - min_score) / (max_score - min_score) if max_score > min_score else 0
