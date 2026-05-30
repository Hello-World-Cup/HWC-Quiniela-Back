from src.scoring.constants import POINTS_CORRECT_RESULT, POINTS_EXACT_SCORE, POINTS_WRONG


def _sign(n: int) -> int:
    if n > 0:
        return 1
    if n < 0:
        return -1
    return 0


def score_prediction(
    result_a: int,
    result_b: int,
    predicted_a: int,
    predicted_b: int,
) -> int:
    if predicted_a == result_a and predicted_b == result_b:
        return POINTS_EXACT_SCORE
    if _sign(result_a - result_b) == _sign(predicted_a - predicted_b):
        return POINTS_CORRECT_RESULT
    return POINTS_WRONG
