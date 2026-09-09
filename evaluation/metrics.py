"""
Automated Evaluation Metrics for Intent Classification, Escalation Decisions, and Text Generation.
Pure Python implementations of Accuracy, Precision, Recall, Macro-F1, ROUGE-L, BLEU-4, and Cost-Weighted Safety Risk.
Zero external C/binary dependencies required.
"""

import math
import re
from collections import Counter
from src.config import COST_WEIGHT_FALSE_AUTO_HANDLE, COST_WEIGHT_FALSE_ESCALATION

def tokenize_words(text: str):
    """Clean word tokenizer for evaluation."""
    return re.findall(r'\b\w+\b', text.lower())

def compute_classification_metrics(y_true, y_pred, labels):
    """
    Computes Accuracy, Macro-F1, Weighted-F1, and Per-Class Precision/Recall/F1.
    """
    total = len(y_true)
    if total == 0:
        return {}

    correct = sum(1 for yt, yp in zip(y_true, y_pred) if yt == yp)
    accuracy = correct / total

    per_class = {}
    macro_f1_sum = 0.0
    weighted_f1_sum = 0.0

    for label in labels:
        tp = sum(1 for yt, yp in zip(y_true, y_pred) if yt == label and yp == label)
        fp = sum(1 for yt, yp in zip(y_true, y_pred) if yt != label and yp == label)
        fn = sum(1 for yt, yp in zip(y_true, y_pred) if yt == label and yp != label)
        support = sum(1 for yt in y_true if yt == label)

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

        per_class[label] = {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
            "support": support
        }
        macro_f1_sum += f1
        weighted_f1_sum += f1 * support

    macro_f1 = macro_f1_sum / len(labels) if labels else 0.0
    weighted_f1 = weighted_f1_sum / total if total > 0 else 0.0

    return {
        "accuracy": round(accuracy, 4),
        "macro_f1": round(macro_f1, 4),
        "weighted_f1": round(weighted_f1, 4),
        "per_class": per_class
    }

def compute_escalation_metrics(y_true_bool, y_pred_bool):
    """
    Computes Precision, Recall, F1, and Cost-Weighted Safety Risk for Escalation decisions.
    False Auto-Handle (FN) is penalized 5x more heavily than False Escalation (FP).
    """
    total = len(y_true_bool)
    if total == 0:
        return {}

    tp = sum(1 for yt, yp in zip(y_true_bool, y_pred_bool) if yt and yp)
    fp = sum(1 for yt, yp in zip(y_true_bool, y_pred_bool) if not yt and yp)
    fn = sum(1 for yt, yp in zip(y_true_bool, y_pred_bool) if yt and not yp)
    tn = sum(1 for yt, yp in zip(y_true_bool, y_pred_bool) if not yt and not yp)

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    accuracy = (tp + tn) / total

    # Safety-critical metric: Under-Escalation Rate (FN rate)
    under_escalation_rate = fn / (tp + fn) if (tp + fn) > 0 else 0.0

    # Total Cost-Weighted Safety Risk: 5.0 * FN + 1.0 * FP
    total_safety_cost = (COST_WEIGHT_FALSE_AUTO_HANDLE * fn) + (COST_WEIGHT_FALSE_ESCALATION * fp)
    normalized_cost_per_query = total_safety_cost / total

    return {
        "accuracy": round(accuracy, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "true_positives": tp,
        "false_positives": fp,
        "false_negatives": fn,
        "true_negatives": tn,
        "under_escalation_rate": round(under_escalation_rate, 4),
        "cost_weighted_safety_risk": round(normalized_cost_per_query, 4)
    }

def lcs_length(words1, words2):
    """Calculates Longest Common Subsequence length between two word lists."""
    m, n = len(words1), len(words2)
    dp = [0] * (n + 1)
    for i in range(1, m + 1):
        prev = 0
        for j in range(1, n + 1):
            temp = dp[j]
            if words1[i - 1] == words2[j - 1]:
                dp[j] = prev + 1
            else:
                dp[j] = max(dp[j], dp[j - 1])
            prev = temp
    return dp[n]

def compute_rouge_l(candidate: str, reference: str) -> float:
    """Computes ROUGE-L score based on Longest Common Subsequence."""
    cand_words = tokenize_words(candidate)
    ref_words = tokenize_words(reference)
    if not cand_words or not ref_words:
        return 0.0

    lcs = lcs_length(cand_words, ref_words)
    p = lcs / len(cand_words)
    r = lcs / len(ref_words)
    if (p + r) > 0:
        return (2 * p * r) / (p + r)
    return 0.0

def compute_bleu_4(candidate: str, reference: str) -> float:
    """Computes BLEU-4 score with brevity penalty."""
    cand_words = tokenize_words(candidate)
    ref_words = tokenize_words(reference)
    c_len = len(cand_words)
    r_len = len(ref_words)
    if c_len == 0 or r_len == 0:
        return 0.0

    # Brevity penalty
    bp = 1.0 if c_len > r_len else math.exp(1.0 - r_len / c_len)

    # Modified n-gram precisions for n=1..4
    precisions = []
    for n in range(1, 5):
        if c_len < n:
            precisions.append(0.0)
            continue
        cand_ngrams = Counter([tuple(cand_words[i:i+n]) for i in range(c_len - n + 1)])
        ref_ngrams = Counter([tuple(ref_words[i:i+n]) for i in range(r_len - n + 1)])

        clipped_matches = sum(min(count, ref_ngrams.get(ng, 0)) for ng, count in cand_ngrams.items())
        total_ngrams = sum(cand_ngrams.values())
        precisions.append((clipped_matches + 1e-4) / (total_ngrams + 1e-4))

    score = bp * math.exp(sum(0.25 * math.log(p) for p in precisions))
    return score

def compute_grounding_recall(reply: str) -> float:
    """Checks presence of official Apple Support KB link or actionable DM instructions."""
    has_apple_url = "support.apple.com" in reply or "reportaproblem.apple.com" in reply or "iforgot.apple.com" in reply
    has_dm = "dm" in reply.lower() or "direct message" in reply.lower()
    return 1.0 if (has_apple_url or has_dm) else 0.0
