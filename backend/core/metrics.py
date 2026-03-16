
def safe_div(numerator, denominator, zero_value=0.0):
    if denominator == 0:
        return zero_value
    return numerator / denominator


def f1(precision, recall):
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)
