"""
Human-Judge Agreement Analysis.
Computes Cohen's Kappa, Spearman's Rank Correlation, Pearson Correlation,
and MAE between Human Annotators and LLM-as-a-Judge ratings across 50 calibrated examples.
Fulfills the mandatory assignment requirement: 'evidence of how well your judge agrees with a human'.
"""

import os
import sys
import math

# Ensure project root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data_loader import load_human_calibration
from evaluation.judge import SupportReplyJudge

def compute_cohen_kappa(human_categories, judge_categories, categories):
    """
    Computes Cohen's Kappa for categorical agreement:
    kappa = (Po - Pe) / (1 - Pe)
    """
    n = len(human_categories)
    if n == 0:
        return 0.0

    matrix = {c1: {c2: 0 for c2 in categories} for c1 in categories}
    for h, j in zip(human_categories, judge_categories):
        if h in matrix and j in matrix[h]:
            matrix[h][j] += 1

    po = sum(matrix[c][c] for c in categories) / n

    pe = 0.0
    for c in categories:
        row_sum = sum(matrix[c].values())
        col_sum = sum(matrix[other][c] for other in categories)
        pe += (row_sum / n) * (col_sum / n)

    if pe >= 1.0:
        return 1.0
    kappa = (po - pe) / (1.0 - pe)
    return round(kappa, 4)

def rank_data(values):
    """Assigns ranks to data with fractional handling for ties."""
    n = len(values)
    sorted_pairs = sorted(enumerate(values), key=lambda x: x[1])
    ranks = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j < n - 1 and sorted_pairs[j][1] == sorted_pairs[j + 1][1]:
            j += 1
        avg_rank = (i + j + 2) / 2.0
        for k in range(i, j + 1):
            ranks[sorted_pairs[k][0]] = avg_rank
        i = j + 1
    return ranks

def compute_spearman_rho(x, y):
    """
    Computes Spearman's Rank Correlation Coefficient (rho):
    rho = 1 - (6 * sum(d_i^2)) / (n * (n^2 - 1))
    """
    n = len(x)
    if n < 2:
        return 0.0

    rx = rank_data(x)
    ry = rank_data(y)

    d_squared_sum = sum((rx[i] - ry[i]) ** 2 for i in range(n))
    rho = 1.0 - (6.0 * d_squared_sum) / (n * (n ** 2 - 1))
    return round(rho, 4)

def compute_pearson_r(x, y):
    """Computes Pearson Linear Correlation Coefficient (r)."""
    n = len(x)
    if n < 2:
        return 0.0

    mean_x = sum(x) / n
    mean_y = sum(y) / n

    num = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
    den_x = math.sqrt(sum((x[i] - mean_x) ** 2 for i in range(n)))
    den_y = math.sqrt(sum((y[i] - mean_y) ** 2 for i in range(n)))

    if den_x == 0 or den_y == 0:
        return 0.0
    return round(num / (den_x * den_y), 4)

def evaluate_human_judge_agreement(calibration_data=None):
    """
    Evaluates agreement across the 50 human-graded calibration examples.
    Returns Kappa, Spearman rho, Pearson r, and MAE across all rubric dimensions.
    """
    if calibration_data is None:
        calibration_data = load_human_calibration()

    judge = SupportReplyJudge()

    human_overall = []
    judge_overall = []
    human_grounding = []
    judge_grounding = []
    human_helpfulness = []
    judge_helpfulness = []
    human_tone = []
    judge_tone = []
    human_safety = []
    judge_safety = []

    human_bins = []
    judge_bins = []

    for item in calibration_data:
        h_ratings = item["human_ratings"]
        # Use candidate reply (which has diverse qualities)
        reply_to_judge = item.get("candidate_reply", item.get("reference_reply", ""))
        
        j_eval = judge.evaluate_reply(
            customer_query=item["customer_text"],
            generated_reply=reply_to_judge,
            ground_truth_intent=item["ground_truth_intent"],
            should_escalate_gt=item["ground_truth_escalate"]
        )

        h_ov = h_ratings["overall_score"]
        j_ov = j_eval["overall_score"]

        human_overall.append(h_ov)
        judge_overall.append(j_ov)
        human_grounding.append(h_ratings["grounding"])
        judge_grounding.append(j_eval["grounding"])
        human_helpfulness.append(h_ratings["helpfulness"])
        judge_helpfulness.append(j_eval["helpfulness"])
        human_tone.append(h_ratings["brand_tone"])
        judge_tone.append(j_eval["brand_tone"])
        human_safety.append(h_ratings["escalation_safety"])
        judge_safety.append(j_eval["escalation_safety"])

        h_bin = "HIGH" if h_ov >= 4.0 else ("MODERATE" if h_ov >= 3.0 else "LOW")
        j_bin = "HIGH" if j_ov >= 4.0 else ("MODERATE" if j_ov >= 3.0 else "LOW")
        human_bins.append(h_bin)
        judge_bins.append(j_bin)

    categories = ["HIGH", "MODERATE", "LOW"]
    kappa = compute_cohen_kappa(human_bins, judge_bins, categories)
    spearman_rho = compute_spearman_rho(human_overall, judge_overall)
    pearson_r = compute_pearson_r(human_overall, judge_overall)
    mae = sum(abs(h - j) for h, j in zip(human_overall, judge_overall)) / len(human_overall)

    # Confusion matrix
    conf_matrix = {c1: {c2: 0 for c2 in categories} for c1 in categories}
    for h, j in zip(human_bins, judge_bins):
        conf_matrix[h][j] += 1

    dim_mae = {
        "grounding_mae": round(sum(abs(h - j) for h, j in zip(human_grounding, judge_grounding)) / len(human_grounding), 3),
        "helpfulness_mae": round(sum(abs(h - j) for h, j in zip(human_helpfulness, judge_helpfulness)) / len(human_helpfulness), 3),
        "brand_tone_mae": round(sum(abs(h - j) for h, j in zip(human_tone, judge_tone)) / len(human_tone), 3),
        "escalation_safety_mae": round(sum(abs(h - j) for h, j in zip(human_safety, judge_safety)) / len(human_safety), 3)
    }

    return {
        "sample_size": len(calibration_data),
        "cohen_kappa": kappa,
        "spearman_rho": spearman_rho,
        "pearson_r": pearson_r,
        "overall_mae": round(mae, 3),
        "confusion_matrix": conf_matrix,
        "dimension_mae": dim_mae,
        "interpretation": "Almost Perfect Agreement (κ >= 0.80)" if kappa >= 0.80 else ("Substantial Agreement (0.60 <= κ < 0.80)" if kappa >= 0.60 else "Moderate Agreement")
    }

if __name__ == "__main__":
    results = evaluate_human_judge_agreement()
    print("Human-Judge Agreement Analysis Results:")
    print(f"  Sample Size: {results['sample_size']}")
    print(f"  Cohen's Kappa (κ): {results['cohen_kappa']}")
    print(f"  Spearman's Rho (ρ): {results['spearman_rho']}")
    print(f"  Pearson Correlation (r): {results['pearson_r']}")
    print(f"  Overall MAE: {results['overall_mae']}")
    print(f"  Interpretation: {results['interpretation']}")
    print(f"  Confusion Matrix (Human rows, Judge cols):")
    for row_k, row_v in results['confusion_matrix'].items():
        print(f"    {row_k}: {row_v}")
